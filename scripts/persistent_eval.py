#!/usr/bin/env python3
"""Run OfficeQA questions through opencode in the persistent container.

This is the 30-minute shortcut: uses spark-persistent container with the
full corpus, runs opencode directly, collects answers and scores them.

Usage:
    python scripts/persistent_eval.py --n 5 --model anthropic/claude-sonnet-4-20250514
    python scripts/persistent_eval.py --tasks uid0057,uid0199,uid0246
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd


def load_questions(dataset_path: str, n: int = None, tasks: list[str] = None) -> list[dict]:
    """Load questions from the OfficeQA dataset."""
    df = pd.read_csv(dataset_path)
    questions = []
    for _, row in df.iterrows():
        task_id = row.get("task_id", "")
        if tasks and not any(t in task_id for t in tasks):
            continue
        questions.append({
            "task_id": task_id,
            "question": row["question"],
            "ground_truth": str(row.get("ground_truth", row.get("answer", ""))),
            "category": row.get("category", "unknown"),
        })
    if n and not tasks:
        questions = questions[:n]
    return questions


def run_question(question: str, task_id: str, model: str) -> dict:
    """Run a single question through opencode in the persistent container."""
    # Read the prompt template
    template_path = Path("prompts/officeqa_prompt.j2")
    if template_path.exists():
        template = template_path.read_text()
        prompt = template.replace("{{ instruction }}", question)
    else:
        prompt = question

    # Escape for shell
    escaped = prompt.replace("'", "'\\''")

    # Set up skills and config, then run
    setup = """
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
mkdir -p ~/.config/opencode/skills && cp -r /app/skills/* ~/.config/opencode/skills/ 2>/dev/null || true
mkdir -p ~/.config/opencode && echo '{"provider":{"anthropic":{"models":{"MODELID":{}}}}}' | sed 's|MODELID|MODEL_PLACEHOLDER|' > ~/.config/opencode/opencode.json
rm -f /app/answer.txt /app/draft.txt /app/name.txt
""".replace("MODEL_PLACEHOLDER", model.split("/", 1)[1] if "/" in model else model)

    cmd = f"""docker exec -e ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY','')} \
      -e SPARK_API_KEY={os.environ.get('SPARK_API_KEY','')} \
      -e OPENCODE_FAKE_VCS=git \
      spark-persistent bash -c '{setup}
opencode --model={model} run -- '\\'''{escaped}'\\''' 2>&1 | tail -5
echo "EXIT:$?"
cat /app/answer.txt 2>/dev/null || echo "NO_ANSWER"
'"""

    start = time.time()
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=900
        )
        elapsed = time.time() - start
        output = result.stdout

        # Extract answer
        lines = output.strip().split("\n")
        answer = lines[-1] if lines else "NO_ANSWER"
        if answer == "NO_ANSWER":
            answer = ""

        return {
            "task_id": task_id,
            "answer": answer.strip(),
            "elapsed": round(elapsed, 1),
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "task_id": task_id,
            "answer": "",
            "elapsed": 900,
            "exit_code": -1,
            "error": "timeout",
        }


def score(predicted: str, ground_truth: str, tolerance: float = 0.01) -> float:
    """Score with 1% numeric tolerance."""
    try:
        # Clean both values
        pred_clean = re.sub(r'[%$,\s]', '', predicted.strip())
        gt_clean = re.sub(r'[%$,\s]', '', ground_truth.strip())

        # Try parsing as numbers
        pred_val = float(pred_clean)
        gt_val = float(gt_clean)

        if gt_val == 0:
            return 1.0 if abs(pred_val) < tolerance else 0.0
        if abs(pred_val - gt_val) / abs(gt_val) <= tolerance:
            return 1.0
        return 0.0
    except (ValueError, ZeroDivisionError):
        # Fall back to exact string match
        return 1.0 if predicted.strip() == ground_truth.strip() else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=None, help="Number of questions")
    parser.add_argument("--tasks", type=str, default=None, help="Comma-separated task IDs")
    parser.add_argument("--model", type=str, default="anthropic/claude-sonnet-4-20250514")
    parser.add_argument("--dataset", type=str, default="data/officeqa-evoskill.csv")
    args = parser.parse_args()

    tasks = args.tasks.split(",") if args.tasks else None
    questions = load_questions(args.dataset, n=args.n, tasks=tasks)

    print(f"Running {len(questions)} questions with {args.model}")
    print(f"{'='*60}")

    results = []
    passed = 0
    for i, q in enumerate(questions):
        print(f"\n[{i+1}/{len(questions)}] {q['task_id']}: {q['question'][:60]}...")
        result = run_question(q["question"], q["task_id"], args.model)
        result["ground_truth"] = q["ground_truth"]
        result["score"] = score(result["answer"], q["ground_truth"])
        results.append(result)

        status = "PASS" if result["score"] > 0 else "FAIL"
        passed += int(result["score"] > 0)
        print(f"  {status} | answer={result['answer'][:40]} | expected={q['ground_truth'][:40]} | {result['elapsed']}s")

    print(f"\n{'='*60}")
    print(f"Score: {passed}/{len(questions)} ({100*passed/len(questions):.0f}%)")

    # Save results
    output_path = Path(f"results/persistent_eval_{args.model.split('/')[-1]}.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
