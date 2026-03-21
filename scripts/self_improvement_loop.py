#!/usr/bin/env python3
"""Self-Improvement Loop — agents that teach themselves.

Experiment 1: Single-task self-authoring
  Run 10 tasks with the self-authoring prompt. Collect what agents write
  to /app/skill.txt. Analyze: do they write facts, narratives, or skills?

Experiment 2: Two-question sessions (requires persistent container)
  Run pairs of questions. After Q1, agent writes a skill. Before Q2,
  agent reads the skill from Q1. Measure if Q2 improves.

Usage:
    python3 scripts/self_improvement_loop.py --experiment 1
    python3 scripts/self_improvement_loop.py --experiment 2
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def run_experiment_1(n_tasks=10):
    """Run tasks with self-authoring prompt and collect skill.txt outputs."""
    print("=" * 60)
    print("  EXPERIMENT 1: What Do Agents Write When Asked to Teach?")
    print("=" * 60)

    # Set up arena.yaml
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    Path("arena.yaml").write_text(f"""name: "ground-wire"
version: "0.9.0"
competition: "grounded-reasoning"
agent:
  type: "harness"
  harness_name: "opencode"
  model: "openrouter/deepseek/deepseek-v3.2"
  prompt_template_path: "prompts/officeqa_self_authoring.j2"
  config:
    reasoning_effort: "high"
  env:
    OPENROUTER_API_KEY: "{openrouter_key}"
environment:
  timeout_per_task: 600
""")

    # Clean docker
    subprocess.run(["docker", "network", "prune", "-f"],
                    capture_output=True)
    subprocess.run(["docker", "container", "prune", "-f"],
                    capture_output=True)

    # Run tasks
    tag = "self-authoring-exp1"
    print(f"\nRunning {n_tasks} tasks with self-authoring prompt...")
    result = subprocess.run(
        ["arena", "test", "-n", str(n_tasks), "--tag", tag],
        capture_output=True, text=True, timeout=3600,
        env={**os.environ},
    )
    output = result.stdout + result.stderr
    print(output[-500:])  # tail

    # Collect skill.txt files from agent artifacts
    run_dirs = sorted(Path(".arena/runs").glob("*/self-authoring-exp1"))
    if not run_dirs:
        print("No run directory found!")
        return

    run_dir = run_dirs[-1]
    skills_collected = []

    for task_dir in sorted(run_dir.iterdir()):
        if not task_dir.name.startswith("officeqa-"):
            continue

        uid = task_dir.name.split("__")[0]

        # Check result
        result_file = task_dir / "result.json"
        if result_file.exists():
            r = json.loads(result_file.read_text())
            reward = r.get("verifier_result", {}).get("rewards", {}).get("reward", 0)
            passed = "PASS" if reward and reward > 0 else "FAIL"
        else:
            passed = "UNKNOWN"

        # Look for skill.txt in the agent's output
        # The agent writes to /app/skill.txt inside the container
        # We need to check the trajectory for write calls to skill.txt
        traj_file = task_dir / "agent" / "trajectory.json"
        skill_content = None

        if traj_file.exists():
            try:
                t = json.loads(traj_file.read_text())
                for step in t.get("steps", []):
                    for tc in step.get("tool_calls", []):
                        args = tc.get("arguments", {})
                        if tc.get("function_name") == "write":
                            path = args.get("filePath", args.get("file_path", ""))
                            if "skill" in path.lower():
                                skill_content = args.get("content", "")[:1000]
                        elif tc.get("function_name") == "bash":
                            cmd = args.get("command", "")
                            if "skill.txt" in cmd and ("echo" in cmd or "cat" in cmd or ">" in cmd):
                                # Try to extract from observation
                                obs = step.get("observation", {})
                                for r in obs.get("results", []):
                                    c = r.get("content", "")
                                    if len(c) > 20 and len(c) < 2000:
                                        skill_content = c[:1000]
            except Exception as e:
                print(f"  Error parsing trajectory for {uid}: {e}")

        skills_collected.append({
            "uid": uid,
            "passed": passed,
            "skill_written": skill_content is not None,
            "skill_content": skill_content,
        })

        status = "✓ SKILL" if skill_content else "✗ no skill"
        print(f"  {uid}: {passed} | {status}")

    # Analyze what was written
    print(f"\n{'=' * 60}")
    print("  ANALYSIS: What Did Agents Write?")
    print(f"{'=' * 60}")

    total = len(skills_collected)
    with_skills = sum(1 for s in skills_collected if s["skill_written"])
    print(f"\n  Tasks: {total}")
    print(f"  Wrote skill.txt: {with_skills}/{total}")

    # Classify each skill as memory, journal, or skill
    for s in skills_collected:
        if not s["skill_content"]:
            continue
        content = s["skill_content"].lower()

        # Heuristic classification
        has_location = any(w in content for w in ["found in", "located in", "file", "bulletin", "table"])
        has_narrative = any(w in content for w in ["i searched", "i found", "i tried", "first i", "then i"])
        has_principle = any(w in content for w in ["always", "never", "remember to", "tip:", "important:", "lesson"])

        types = []
        if has_location: types.append("MEMORY")
        if has_narrative: types.append("JOURNAL")
        if has_principle: types.append("SKILL")

        print(f"\n  --- {s['uid']} ({s['passed']}) ---")
        print(f"  Type: {', '.join(types) or 'UNCLASSIFIED'}")
        print(f"  Content: {s['skill_content'][:300]}...")

    # Save results
    results_file = Path("results/self_authoring_exp1.json")
    results_file.write_text(json.dumps(skills_collected, indent=2))
    print(f"\n  Results saved to {results_file}")

    return skills_collected


def run_experiment_2(n_pairs=5):
    """Run pairs of questions. Agent writes skill after Q1, reads it before Q2."""
    print("=" * 60)
    print("  EXPERIMENT 2: Does Self-Authored Knowledge Transfer?")
    print("=" * 60)
    print("\n  This experiment requires persistent containers.")
    print("  Running each pair as sequential tasks in the same session.")

    # For now, we simulate by:
    # 1. Running Q1 with self-authoring prompt
    # 2. Extracting the skill.txt content
    # 3. Injecting it into the prompt for Q2
    # 4. Comparing Q2 performance with and without the injected skill

    # This is a simplified version — full implementation needs
    # persistent containers or a custom harness

    print("\n  [Experiment 2 requires persistent container support]")
    print("  [Logging design for future implementation]")
    print("  ")
    print("  Design:")
    print("  - Q1: self-authoring prompt → agent writes skill.txt")
    print("  - Q2a: baseline prompt (no skill from Q1)")
    print("  - Q2b: baseline prompt + skill from Q1 injected")
    print("  - Measure: does Q2b outperform Q2a?")
    print("  ")
    print("  This is the minimum viable self-improvement loop.")
    print("  One agent, two questions, one skill written in between.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=int, default=1, choices=[1, 2])
    parser.add_argument("--n", type=int, default=10)
    args = parser.parse_args()

    if args.experiment == 1:
        run_experiment_1(n_tasks=args.n)
    elif args.experiment == 2:
        run_experiment_2(n_pairs=args.n)
