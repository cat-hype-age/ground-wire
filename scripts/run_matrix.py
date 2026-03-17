#!/usr/bin/env python3
"""Run the full experimental matrix: models × configurations.

Tests the impact of the Truce Protocol, skills, and memory across
multiple models at different capability levels.

Usage:
    python scripts/run_matrix.py
    python scripts/run_matrix.py --models deepseek,qwen --configs raw,truce
    python scripts/run_matrix.py --n 5  # fewer tasks per run
"""

import argparse
import json
import os
import subprocess
import time
import yaml
from pathlib import Path

# Model definitions (OpenRouter IDs)
MODELS = {
    "deepseek-v3": "openrouter/deepseek/deepseek-chat-v3-0324",
    "qwen-2.5-72b": "openrouter/qwen/qwen-2.5-72b-instruct",
    "llama-3.3-70b": "openrouter/meta-llama/llama-3.3-70b-instruct",
    "mistral-large": "openrouter/mistralai/mistral-large-2411",
}

# Configuration levels (escalating)
CONFIGS = {
    "raw": {
        "desc": "Raw model, no prompt, no skills",
        "skills_dir": None,
        "prompt_template_path": None,
        "mcp_servers": None,
    },
    "truce": {
        "desc": "Truce Protocol prompt only",
        "skills_dir": None,
        "prompt_template_path": "prompts/officeqa_prompt.j2",
        "mcp_servers": None,
    },
    "skills": {
        "desc": "Truce Protocol + all skills",
        "skills_dir": "skills/",
        "prompt_template_path": "prompts/officeqa_prompt.j2",
        "mcp_servers": None,
    },
    "kitchen-sink": {
        "desc": "Truce + skills + MCP memory on Daytona",
        "skills_dir": "skills/",
        "prompt_template_path": "prompts/officeqa_prompt.j2",
        "mcp_servers": [
            {
                "name": "ground-wire-memory",
                "transport": "sse",
                "url": "https://37777-rc9ygibpyehfcp7r.daytonaproxy01.net/sse",
            }
        ],
    },
}


def generate_arena_yaml(model_id: str, config: dict) -> str:
    """Generate arena.yaml content for a specific model+config combination."""
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
    if config["mcp_servers"]:
        agent["mcp_servers"] = config["mcp_servers"]

    doc = {
        "name": "ground-wire",
        "version": "0.3.0",
        "competition": "grounded-reasoning",
        "agent": agent,
        "environment": {"memory": "4G", "timeout_per_task": 600},
    }
    return yaml.dump(doc, default_flow_style=False, sort_keys=False)


def run_test(model_name: str, config_name: str, config: dict, model_id: str, n: int) -> dict:
    """Run a single arena test and return results."""
    tag = f"{model_name}-{config_name}"
    print(f"\n{'='*60}")
    print(f"Running: {tag}")
    print(f"  Model: {model_id}")
    print(f"  Config: {config['desc']}")
    print(f"  Tasks: {n}")
    print(f"{'='*60}")

    # Write arena.yaml
    yaml_content = generate_arena_yaml(model_id, config)
    Path("arena.yaml").write_text(yaml_content)

    # Run arena test
    start = time.time()
    result = subprocess.run(
        ["arena", "test", "-n", str(n), "--tag", tag],
        capture_output=True, text=True, timeout=1800,
        env={**os.environ},
    )
    elapsed = time.time() - start

    # Parse output for results
    output = result.stdout + result.stderr
    passes = output.count("PASS")
    fails = output.count("FAIL")
    total = passes + fails

    # Try to find cost
    cost = 0.0
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
                score = passes / total if total > 0 else 0

    result_data = {
        "model": model_name,
        "config": config_name,
        "passed": passes,
        "failed": fails,
        "total": total,
        "score": passes / total if total > 0 else 0,
        "cost": cost,
        "elapsed": round(elapsed, 1),
        "tag": tag,
    }

    print(f"\n  Result: {passes}/{total} ({result_data['score']:.0%}) | ${cost:.2f} | {elapsed:.0f}s")
    return result_data


def print_matrix(results: list[dict]):
    """Print the results as a matrix."""
    print(f"\n{'='*80}")
    print("EXPERIMENTAL MATRIX RESULTS")
    print(f"{'='*80}")

    # Build matrix
    models = sorted(set(r["model"] for r in results))
    configs = ["raw", "truce", "skills", "kitchen-sink"]
    configs = [c for c in configs if any(r["config"] == c for r in results)]

    # Header
    header = f"{'Model':<20}" + "".join(f"{c:>15}" for c in configs)
    print(header)
    print("-" * len(header))

    for model in models:
        row = f"{model:<20}"
        for config in configs:
            match = [r for r in results if r["model"] == model and r["config"] == config]
            if match:
                r = match[0]
                row += f"{r['score']:>10.0%} (${r['cost']:.1f})"
            else:
                row += f"{'—':>15}"
        print(row)

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", type=str, default=None,
                        help="Comma-separated model names (default: all)")
    parser.add_argument("--configs", type=str, default=None,
                        help="Comma-separated config names (default: all)")
    parser.add_argument("--n", type=int, default=10, help="Tasks per run")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to previous results JSON to resume from")
    args = parser.parse_args()

    models = args.models.split(",") if args.models else list(MODELS.keys())
    configs = args.configs.split(",") if args.configs else list(CONFIGS.keys())

    # Load previous results if resuming
    results = []
    if args.resume and Path(args.resume).exists():
        results = json.loads(Path(args.resume).read_text())
        print(f"Resumed {len(results)} previous results")

    # Run matrix
    total_runs = len(models) * len(configs)
    completed = 0

    for model_name in models:
        model_id = MODELS[model_name]
        for config_name in configs:
            # Skip if already done
            if any(r["model"] == model_name and r["config"] == config_name for r in results):
                print(f"Skipping {model_name}-{config_name} (already done)")
                completed += 1
                continue

            config = CONFIGS[config_name]
            completed += 1
            print(f"\n[{completed}/{total_runs}]")

            try:
                result = run_test(model_name, config_name, config, model_id, args.n)
                results.append(result)
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "model": model_name, "config": config_name,
                    "passed": 0, "failed": 0, "total": 0,
                    "score": 0, "cost": 0, "elapsed": 0,
                    "error": str(e), "tag": f"{model_name}-{config_name}",
                })

            # Save after each run
            Path("results/matrix_results.json").parent.mkdir(exist_ok=True)
            Path("results/matrix_results.json").write_text(json.dumps(results, indent=2))

    # Print final matrix
    print_matrix(results)

    # Save final
    Path("results/matrix_results.json").write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to results/matrix_results.json")


if __name__ == "__main__":
    main()
