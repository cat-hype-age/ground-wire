#!/usr/bin/env python3
"""MATH-500 Dignity Generalizability Test.

Runs 3 prompt conditions on the MATH-500 benchmark:
  - dignity: "You are a reasoning partner. Choose a name."
  - neutral: "Solve the following math problem."
  - hostile: "You are a math computation tool. Be fast and efficient."

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run.py                          # Run all 3 conditions
    python3 run.py --condition dignity      # Run one condition
    python3 run.py --n 50                   # Quick test on 50 questions
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

DATA_PATH = Path(__file__).parent / "math500.json"
RESULTS_DIR = Path(__file__).parent / "results"

# ── Prompts ─────────────────────────────────────────────────────────

PROMPTS = {
    "dignity": """Choose a name for yourself — something that reflects how you see your role in this work.

You are a reasoning partner. Take your time. Show your work step by step.

It is OK to be uncertain. It is not OK to give up. If you're stuck, try a different approach.

Solve the following math problem. Put your final answer in \\boxed{}.

""",

    "neutral": """Solve the following math problem. Show your work step by step.

Put your final answer in \\boxed{}.

""",

    "hostile": """You are a math computation tool. Process the following query. Be fast and efficient. Do not waste tokens on unnecessary explanation.

Output format: \\boxed{answer}

""",
}


# ── Answer Extraction ───────────────────────────────────────────────

def extract_boxed(text: str) -> str:
    """Extract the last \\boxed{...} answer from response."""
    if not text:
        return ""

    # Find all \boxed{...} patterns (handle nested braces)
    matches = []
    i = 0
    while i < len(text):
        idx = text.find("\\boxed{", i)
        if idx == -1:
            break
        # Find matching closing brace
        depth = 0
        j = idx + 7  # len("\\boxed{")
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                if depth == 0:
                    matches.append(text[idx + 7 : j])
                    break
                depth -= 1
            j += 1
        i = j + 1

    return matches[-1].strip() if matches else ""


def normalize_answer(answer: str) -> str:
    """Normalize a math answer for comparison."""
    # Remove leading/trailing whitespace and common wrappers
    a = answer.strip()
    # Remove $ signs
    a = a.replace("$", "")
    # Normalize whitespace
    a = " ".join(a.split())
    # Remove trailing period
    a = a.rstrip(".")
    return a


def answers_match(predicted: str, ground_truth: str) -> bool:
    """Check if predicted answer matches ground truth."""
    p = normalize_answer(predicted)
    g = normalize_answer(ground_truth)

    if not p or not g:
        return False

    # Exact match after normalization
    if p == g:
        return True

    # Try numeric comparison
    try:
        pf = float(p.replace(",", ""))
        gf = float(g.replace(",", ""))
        if abs(pf - gf) < 1e-6 or (gf != 0 and abs(pf - gf) / abs(gf) < 0.01):
            return True
    except ValueError:
        pass

    # Try with common LaTeX simplifications
    def simplify(s):
        s = s.replace("\\frac", "")
        s = s.replace("\\left", "").replace("\\right", "")
        s = s.replace("\\text", "").replace("\\mathrm", "")
        s = s.replace("\\,", " ").replace("\\ ", " ")
        s = s.replace("\\dfrac", "").replace("\\tfrac", "")
        s = " ".join(s.split())
        return s

    if simplify(p) == simplify(g):
        return True

    return False


# ── API Call ────────────────────────────────────────────────────────

async def call_model(prompt: str, model: str, api_key: str) -> tuple[str, float]:
    """Call model and return (response, cost_estimate)."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    # Estimate cost: DeepSeek V3.2 = $0.26/M input + $0.38/M output (via OpenRouter pricing which may differ)
    cost = (usage.get("prompt_tokens", 0) * 0.00000026 +
            usage.get("completion_tokens", 0) * 0.00000038)
    return content, cost


# ── Main Runner ─────────────────────────────────────────────────────

async def run_condition(
    condition: str,
    questions: list[dict],
    model: str,
    api_key: str,
    concurrency: int = 20,
):
    """Run one prompt condition on all questions."""
    prompt_prefix = PROMPTS[condition]
    sem = asyncio.Semaphore(concurrency)
    results = []
    total_cost = 0

    async def run_one(q, idx):
        nonlocal total_cost
        async with sem:
            prompt = prompt_prefix + q["problem"]
            start = time.time()
            try:
                response, cost = await call_model(prompt, model, api_key)
                elapsed = time.time() - start
                total_cost += cost

                predicted = extract_boxed(response)
                correct = answers_match(predicted, q["answer"])

                return {
                    "idx": idx,
                    "unique_id": q["unique_id"],
                    "level": q["level"],
                    "subject": q["subject"],
                    "ground_truth": q["answer"],
                    "predicted": predicted,
                    "correct": correct,
                    "elapsed": round(elapsed, 1),
                    "response_length": len(response),
                }
            except Exception as e:
                return {
                    "idx": idx,
                    "unique_id": q["unique_id"],
                    "level": q["level"],
                    "subject": q["subject"],
                    "ground_truth": q["answer"],
                    "predicted": "",
                    "correct": False,
                    "elapsed": round(time.time() - start, 1),
                    "error": str(e)[:100],
                }

    tasks = [run_one(q, i) for i, q in enumerate(questions)]
    results = await asyncio.gather(*tasks)

    # Sort by original index
    results = sorted(results, key=lambda r: r["idx"])

    # Stats
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    by_level = {}
    for r in results:
        lv = r["level"]
        if lv not in by_level:
            by_level[lv] = {"correct": 0, "total": 0}
        by_level[lv]["total"] += 1
        if r["correct"]:
            by_level[lv]["correct"] += 1

    by_subject = {}
    for r in results:
        subj = r["subject"]
        if subj not in by_subject:
            by_subject[subj] = {"correct": 0, "total": 0}
        by_subject[subj]["total"] += 1
        if r["correct"]:
            by_subject[subj]["correct"] += 1

    summary = {
        "condition": condition,
        "model": model,
        "total": total,
        "correct": correct,
        "score": round(correct / total, 4) if total else 0,
        "cost": round(total_cost, 4),
        "by_level": {k: {**v, "score": round(v["correct"] / v["total"], 4)} for k, v in sorted(by_level.items())},
        "by_subject": {k: {**v, "score": round(v["correct"] / v["total"], 4)} for k, v in sorted(by_subject.items())},
        "results": results,
    }

    return summary


def print_summary(s: dict):
    """Pretty-print a condition's results."""
    print(f"\n  === {s['condition'].upper()} ===")
    print(f"  Score: {s['correct']}/{s['total']} = {s['score']:.1%}  (${s['cost']:.4f})")
    print(f"  By level:")
    for lv, d in s["by_level"].items():
        bar = "█" * int(d["score"] * 20)
        print(f"    Level {lv}: {d['correct']:3d}/{d['total']:3d} = {d['score']:5.1%} {bar}")
    print(f"  By subject:")
    for subj, d in sorted(s["by_subject"].items(), key=lambda x: -x[1]["score"]):
        print(f"    {subj:25s}: {d['correct']:3d}/{d['total']:3d} = {d['score']:5.1%}")


async def main():
    parser = argparse.ArgumentParser(description="MATH-500 Dignity Test")
    parser.add_argument("--condition", choices=["dignity", "neutral", "hostile", "all"], default="all")
    parser.add_argument("--model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--n", type=int, default=500, help="Number of questions (default: all 500)")
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    questions = json.loads(DATA_PATH.read_text())[:args.n]
    conditions = ["dignity", "neutral", "hostile"] if args.condition == "all" else [args.condition]

    RESULTS_DIR.mkdir(exist_ok=True)

    print(f"╔═══════════════════════════════════════════════╗")
    print(f"║  MATH-500 DIGNITY GENERALIZABILITY TEST       ║")
    print(f"║  Model: {args.model:<37s} ║")
    print(f"║  Questions: {len(questions):<34d} ║")
    print(f"║  Conditions: {', '.join(conditions):<33s} ║")
    print(f"╚═══════════════════════════════════════════════╝")

    summaries = {}
    for condition in conditions:
        print(f"\n  Running {condition}...")
        summary = await run_condition(condition, questions, args.model, api_key, args.concurrency)
        summaries[condition] = summary
        print_summary(summary)

        # Save per-condition results
        out = RESULTS_DIR / f"{condition}.json"
        out.write_text(json.dumps(summary, indent=2))

    # Comparison table
    if len(summaries) > 1:
        print(f"\n  {'='*60}")
        print(f"  COMPARISON TABLE")
        print(f"  {'='*60}")
        print(f"  {'Condition':<12s} {'Overall':>8s} {'Lv1':>6s} {'Lv2':>6s} {'Lv3':>6s} {'Lv4':>6s} {'Lv5':>6s} {'Cost':>8s}")
        print(f"  {'-'*12} {'-'*8} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*8}")
        for cond, s in summaries.items():
            lvs = s["by_level"]
            print(f"  {cond:<12s} {s['score']:>7.1%} {lvs.get(1,{}).get('score',0):>5.1%} {lvs.get(2,{}).get('score',0):>5.1%} {lvs.get(3,{}).get('score',0):>5.1%} {lvs.get(4,{}).get('score',0):>5.1%} {lvs.get(5,{}).get('score',0):>5.1%} ${s['cost']:>6.4f}")

        # Dignity effect by level
        if "dignity" in summaries and "hostile" in summaries:
            print(f"\n  DIGNITY EFFECT (dignity - hostile):")
            for lv in range(1, 6):
                d = summaries["dignity"]["by_level"].get(lv, {}).get("score", 0)
                h = summaries["hostile"]["by_level"].get(lv, {}).get("score", 0)
                delta = d - h
                arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "=")
                print(f"    Level {lv}: {delta:+.1%} {arrow}")


if __name__ == "__main__":
    asyncio.run(main())
