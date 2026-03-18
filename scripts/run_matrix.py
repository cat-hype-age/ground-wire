#!/usr/bin/env python3
"""Run the full experimental matrix: models × configurations.

Tests the impact of the Truce Protocol and skills across
multiple models at different capability levels.

Saves results after every single run for crash resilience.
Use --resume to pick up after a crash.

Usage:
    export $(grep -v '^#' .env | xargs)
    python scripts/run_matrix.py
    python scripts/run_matrix.py --models sonnet-4,deepseek-v3 --configs raw,truce
    python scripts/run_matrix.py --n 5 --resume results/matrix_results.json
"""

import argparse
import json
import os
import subprocess
import time
import yaml
from pathlib import Path

# ── Models ──────────────────────────────────────────────────────────────
# Maps friendly name → OpenCode model ID
MODELS = {
    # Claude (via Anthropic API — needs ANTHROPIC_API_KEY)
    "sonnet-4": "anthropic/claude-sonnet-4-20250514",
    # Open models (via OpenRouter — needs OPENROUTER_API_KEY)
    "deepseek-v3": "openrouter/deepseek/deepseek-chat-v3-0324",
    "qwen-2.5-72b": "openrouter/qwen/qwen-2.5-72b-instruct",
    "llama-3.3-70b": "openrouter/meta-llama/llama-3.3-70b-instruct",
    "mistral-large": "openrouter/mistralai/mistral-large-2411",
    "gemini-2.5-flash": "openrouter/google/gemini-2.5-flash",
    "gemini-2.5-pro": "openrouter/google/gemini-2.5-pro",
}

# ── Configurations ──────────────────────────────────────────────────────
CONFIGS = {
    "raw": {
        "desc": "Raw model — no prompt, no skills (baseline)",
        "skills_dir": None,
        "prompt_template_path": None,
    },
    "hostile": {
        "desc": "Hostile/transactional prompt — anti-dignity control",
        "skills_dir": None,
        "prompt_template_path": "prompts/officeqa_hostile.j2",
    },
    "truce": {
        "desc": "Truce Protocol prompt only — dignity framing, no skills",
        "skills_dir": None,
        "prompt_template_path": "prompts/officeqa_prompt.j2",
    },
    "truce+skills": {
        "desc": "Truce Protocol + all compiled skills",
        "skills_dir": "skills/",
        "prompt_template_path": "prompts/officeqa_prompt.j2",
    },
}

RESULTS_FILE = "results/matrix_results.json"


def generate_arena_yaml(model_id: str, config: dict) -> str:
    """Generate arena.yaml for a specific model+config combination."""
    agent = {
        "type": "harness",
        "harness_name": "opencode",
        "model": model_id,
        "config": {"reasoning_effort": "high"},
        "env": {
            "OPENROUTER_API_KEY": "${oc.env:OPENROUTER_API_KEY,''}",
            "ANTHROPIC_API_KEY": "${oc.env:ANTHROPIC_API_KEY,''}",
            "SPARK_API_KEY": "${oc.env:SPARK_API_KEY,''}",
        },
    }

    if config["skills_dir"]:
        agent["skills_dir"] = config["skills_dir"]
    if config["prompt_template_path"]:
        agent["prompt_template_path"] = config["prompt_template_path"]

    doc = {
        "name": "ground-wire",
        "version": "0.4.0",
        "competition": "grounded-reasoning",
        "agent": agent,
        "environment": {"timeout_per_task": 600},
    }
    return yaml.dump(doc, default_flow_style=False, sort_keys=False)


def parse_arena_output(output: str) -> dict:
    """Parse arena test stdout for results."""
    passes = output.count("PASS")
    fails = output.count("FAIL")
    total = passes + fails

    cost = 0.0
    score = passes / total if total > 0 else 0

    for line in output.split("\n"):
        if "Total cost:" in line:
            try:
                cost = float(line.split("$")[1].strip())
            except (IndexError, ValueError):
                pass
        if "Score:" in line:
            try:
                score = float(line.split(":")[1].strip())
            except (IndexError, ValueError):
                pass

    # Extract per-task results from the table
    task_results = []
    for line in output.split("\n"):
        if "officeqa-uid" in line and ("PASS" in line or "FAIL" in line):
            parts = line.split("│")
            if len(parts) >= 5:
                task_id = parts[1].strip() if len(parts) > 1 else ""
                status = parts[2].strip() if len(parts) > 2 else ""
                reward = parts[3].strip() if len(parts) > 3 else ""
                latency = parts[4].strip() if len(parts) > 4 else ""
                task_cost = parts[5].strip() if len(parts) > 5 else ""
                task_results.append({
                    "task_id": task_id,
                    "status": status,
                    "reward": reward,
                    "latency": latency,
                    "cost": task_cost,
                })

    return {
        "passed": passes,
        "failed": fails,
        "total": total,
        "score": score,
        "cost": cost,
        "task_results": task_results,
    }


def run_test(model_name: str, config_name: str, config: dict, model_id: str, n: int, timeout: int) -> dict:
    """Run a single arena test and return results."""
    tag = f"{model_name}-{config_name}"
    print(f"\n{'='*60}")
    print(f"  Running: {tag}")
    print(f"  Model: {model_id}")
    print(f"  Config: {config['desc']}")
    print(f"  Tasks: {n}")
    print(f"{'='*60}", flush=True)

    # Write arena.yaml
    yaml_content = generate_arena_yaml(model_id, config)
    Path("arena.yaml").write_text(yaml_content)

    # Run arena test
    start = time.time()
    try:
        result = subprocess.run(
            ["arena", "test", "-n", str(n), "--tag", tag],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ},
        )
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        print(output)
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "model": model_name,
            "config": config_name,
            "passed": 0, "failed": 0, "total": 0,
            "score": 0, "cost": 0, "elapsed": round(elapsed, 1),
            "error": f"Timed out after {timeout}s",
            "tag": tag, "task_results": [],
        }

    parsed = parse_arena_output(output)
    result_data = {
        "model": model_name,
        "config": config_name,
        "tag": tag,
        "elapsed": round(elapsed, 1),
        **parsed,
    }

    print(f"\n  Result: {parsed['passed']}/{parsed['total']} ({parsed['score']:.0%}) | ${parsed['cost']:.2f} | {elapsed:.0f}s")
    return result_data


def print_matrix(results: list[dict]):
    """Print results as a formatted matrix with delta analysis."""
    # Filter out errored runs
    valid = [r for r in results if "error" not in r]

    print(f"\n{'='*80}")
    print("  EXPERIMENTAL MATRIX: Model × Protocol")
    print(f"{'='*80}")

    # Preserve insertion order
    models = list(dict.fromkeys(r["model"] for r in valid))
    all_configs = ["raw", "hostile", "truce", "truce+skills"]
    configs = [c for c in all_configs if any(r["config"] == c for r in valid)]

    # Header
    header = f"  {'Model':<20}" + "".join(f"{c:>16}" for c in configs)
    print(header)
    print("  " + "-" * (len(header) - 2))

    for model in models:
        row = f"  {model:<20}"
        for config in configs:
            match = [r for r in valid if r["model"] == model and r["config"] == config]
            if match:
                r = match[0]
                cell = f"{r['score']:.0%} (${r['cost']:.1f})"
                row += f"{cell:>16}"
            else:
                row += f"{'—':>16}"
        print(row)

    # Delta analysis
    print(f"\n  Truce Protocol Impact (score deltas vs raw baseline):")
    print(f"  {'Model':<20}  {'→hostile':>10}  {'→truce':>10}  {'→truce+skills':>14}")
    print("  " + "-" * 60)

    for model in models:
        raw = next((r for r in valid if r["model"] == model and r["config"] == "raw"), None)
        if not raw:
            continue
        row = f"  {model:<20}"
        for cfg in ["hostile", "truce", "truce+skills"]:
            other = next((r for r in valid if r["model"] == model and r["config"] == cfg), None)
            if other:
                delta = other["score"] - raw["score"]
                width = 14 if cfg == "truce+skills" else 10
                row += f"  {delta:>+{width-2}.0%}"
            else:
                width = 14 if cfg == "truce+skills" else 10
                row += f"  {'—':>{width}}"
        print(row)

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(description="Run model × config experimental matrix")
    parser.add_argument("--models", type=str, default=None,
                        help="Comma-separated model names (default: all)")
    parser.add_argument("--configs", type=str, default=None,
                        help="Comma-separated config names (default: raw,truce,truce+skills)")
    parser.add_argument("--n", type=int, default=10, help="Tasks per run")
    parser.add_argument("--timeout", type=int, default=3600,
                        help="Timeout per combo in seconds (default: 3600)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from previous results")
    args = parser.parse_args()

    # Verify env vars
    missing = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.environ.get("OPENROUTER_API_KEY"):
        missing.append("OPENROUTER_API_KEY")
    if missing:
        print(f"WARNING: Missing env vars: {', '.join(missing)}")
        print("Run: export $(grep -v '^#' .env | xargs)")

    models = args.models.split(",") if args.models else list(MODELS.keys())
    configs = args.configs.split(",") if args.configs else ["raw", "truce", "truce+skills"]

    # Load previous results if resuming
    results = []
    results_path = Path(RESULTS_FILE)
    if args.resume and results_path.exists():
        results = json.loads(results_path.read_text())
        print(f"Resumed {len(results)} previous results")

    # Backup arena.yaml before matrix run
    arena_yaml_path = Path("arena.yaml")
    arena_backup = arena_yaml_path.read_text() if arena_yaml_path.exists() else None

    # Run matrix
    total_runs = len(models) * len(configs)
    completed = 0

    for model_name in models:
        if model_name not in MODELS:
            print(f"Unknown model: {model_name}, skipping")
            continue

        model_id = MODELS[model_name]
        for config_name in configs:
            if config_name not in CONFIGS:
                print(f"Unknown config: {config_name}, skipping")
                continue

            # Skip if already done (and not errored)
            existing = [r for r in results if r["model"] == model_name and r["config"] == config_name]
            if existing and "error" not in existing[0]:
                print(f"Skipping {model_name} × {config_name} (already done)")
                completed += 1
                continue

            # Remove previous errored entry if retrying
            results = [r for r in results if not (r["model"] == model_name and r["config"] == config_name)]

            completed += 1
            print(f"\n[{completed}/{total_runs}]")

            try:
                result = run_test(model_name, config_name, CONFIGS[config_name], model_id, args.n, args.timeout)
                results.append(result)
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "model": model_name, "config": config_name,
                    "passed": 0, "failed": 0, "total": 0,
                    "score": 0, "cost": 0, "elapsed": 0,
                    "error": str(e), "tag": f"{model_name}-{config_name}",
                    "task_results": [],
                })

            # Save after each run — crash resilience
            results_path.parent.mkdir(exist_ok=True)
            results_path.write_text(json.dumps(results, indent=2))
            print(f"  [saved to {RESULTS_FILE}]")

    # Restore arena.yaml from backup
    if arena_backup:
        Path("arena.yaml").write_text(arena_backup)
        print("  [arena.yaml restored from backup]")

    # Print final matrix
    print_matrix(results)
    print(f"\nResults saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
