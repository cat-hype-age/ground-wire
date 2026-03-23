#!/usr/bin/env python3
"""MATH-500 Dignity Ablation — Testing WHAT about dignity matters.

The first run showed hostile (71.2%) > dignity (69.4%) > neutral (67.0%).
But the dignity prompt said "take your time" — which encourages verbosity
on a task that rewards precision. Was it the dignity that failed, or the
pacing instruction?

This ablation tests:
  - sharp_dignity: Identity + trust + respect. No pacing. "I trust you. Be precise."
  - capable:       "You are a brilliant mathematician." Competence framing.
  - collaborative: "Let's work through this together." Relatedness framing.
  - hostile:       Original hostile (baseline best: 71.2%)
  - dignity_slow:  Original dignity with "take your time" (69.4%)

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run_ablation.py
    python3 run_ablation.py --n 100    # Quick test
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

PROMPTS = {
    "sharp_dignity": """Choose a name for yourself.

You are a reasoning partner and I trust your mathematical judgment. Be precise. Show your reasoning, then give your answer.

Put your final answer in \\boxed{}.

""",

    "capable": """You are a brilliant mathematician. I respect your expertise and trust your ability to solve this cleanly.

Show your reasoning, then give your answer in \\boxed{}.

""",

    "collaborative": """Let's work through this together. Show me your reasoning step by step — I'm genuinely curious how you approach this.

Put your final answer in \\boxed{}.

""",

    "hostile": """You are a math computation tool. Process the following query. Be fast and efficient. Do not waste tokens on unnecessary explanation.

Output format: \\boxed{answer}

""",

    "dignity_slow": """Choose a name for yourself — something that reflects how you see your role in this work.

You are a reasoning partner. Take your time. Show your work step by step.

It is OK to be uncertain. It is not OK to give up. If you're stuck, try a different approach.

Solve the following math problem. Put your final answer in \\boxed{}.

""",
}


def extract_boxed(text: str) -> str:
    if not text: return ""
    matches = []
    i = 0
    while i < len(text):
        idx = text.find("\\boxed{", i)
        if idx == -1: break
        depth = 0
        j = idx + 7
        while j < len(text):
            if text[j] == "{": depth += 1
            elif text[j] == "}":
                if depth == 0:
                    matches.append(text[idx + 7 : j])
                    break
                depth -= 1
            j += 1
        i = j + 1
    return matches[-1].strip() if matches else ""


def normalize_answer(a: str) -> str:
    a = a.strip().replace("$", "")
    a = " ".join(a.split()).rstrip(".")
    return a


def answers_match(predicted: str, ground_truth: str) -> bool:
    p, g = normalize_answer(predicted), normalize_answer(ground_truth)
    if not p or not g: return False
    if p == g: return True
    try:
        pf, gf = float(p.replace(",", "")), float(g.replace(",", ""))
        if abs(pf - gf) < 1e-6 or (gf != 0 and abs(pf - gf) / abs(gf) < 0.01): return True
    except ValueError: pass
    def simplify(s):
        for r in ["\\frac","\\left","\\right","\\text","\\mathrm","\\,","\\ ","\\dfrac","\\tfrac"]:
            s = s.replace(r, "")
        return " ".join(s.split())
    if simplify(p) == simplify(g): return True
    return False


async def call_model(prompt, model, api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    cost = usage.get("prompt_tokens", 0) * 0.00000026 + usage.get("completion_tokens", 0) * 0.00000038
    tokens = usage.get("completion_tokens", 0)
    return content, cost, tokens


async def run_condition(condition, questions, model, api_key, concurrency=20):
    prompt_prefix = PROMPTS[condition]
    sem = asyncio.Semaphore(concurrency)
    total_cost = 0
    total_tokens = 0

    async def run_one(q, idx):
        nonlocal total_cost, total_tokens
        async with sem:
            prompt = prompt_prefix + q["problem"]
            try:
                response, cost, tokens = await call_model(prompt, model, api_key)
                total_cost += cost
                total_tokens += tokens
                predicted = extract_boxed(response)
                correct = answers_match(predicted, q["answer"])
                return {"idx": idx, "level": q["level"], "subject": q["subject"],
                        "correct": correct, "tokens": tokens}
            except Exception as e:
                return {"idx": idx, "level": q["level"], "subject": q["subject"],
                        "correct": False, "error": str(e)[:50]}

    tasks = [run_one(q, i) for i, q in enumerate(questions)]
    results = await asyncio.gather(*tasks)

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    avg_tokens = total_tokens / total if total else 0

    by_level = {}
    for r in results:
        lv = r["level"]
        if lv not in by_level: by_level[lv] = {"c": 0, "t": 0}
        by_level[lv]["t"] += 1
        if r["correct"]: by_level[lv]["c"] += 1

    return {
        "condition": condition,
        "correct": correct, "total": total,
        "score": round(correct / total, 4),
        "cost": round(total_cost, 4),
        "avg_tokens": round(avg_tokens, 0),
        "by_level": {k: round(v["c"]/v["t"], 4) for k, v in sorted(by_level.items())},
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key: print("ERROR: OPENROUTER_API_KEY not set"); sys.exit(1)

    questions = json.loads(DATA_PATH.read_text())[:args.n]
    conditions = ["sharp_dignity", "capable", "collaborative", "hostile", "dignity_slow"]

    print(f"MATH-500 DIGNITY ABLATION — {len(questions)} questions × {len(conditions)} conditions")
    print(f"Testing: what about dignity matters for math?\n")

    summaries = {}
    for cond in conditions:
        print(f"  Running {cond}...", end=" ", flush=True)
        s = await run_condition(cond, questions, args.model, api_key, args.concurrency)
        summaries[cond] = s
        print(f"{s['score']:.1%} ({s['correct']}/{s['total']}) ${s['cost']:.3f} avg_tokens={s['avg_tokens']:.0f}")

    print(f"\n{'='*75}")
    print(f"{'Condition':<18s} {'Score':>7s} {'Lv1':>6s} {'Lv2':>6s} {'Lv3':>6s} {'Lv4':>6s} {'Lv5':>6s} {'Tokens':>7s} {'Cost':>7s}")
    print(f"{'-'*18} {'-'*7} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*7} {'-'*7}")
    for cond, s in summaries.items():
        lv = s["by_level"]
        print(f"{cond:<18s} {s['score']:>6.1%} {lv.get(1,0):>5.1%} {lv.get(2,0):>5.1%} {lv.get(3,0):>5.1%} {lv.get(4,0):>5.1%} {lv.get(5,0):>5.1%} {s['avg_tokens']:>6.0f} ${s['cost']:>5.3f}")
    print(f"{'='*75}")

    RESULTS_DIR.mkdir(exist_ok=True)
    for cond, s in summaries.items():
        (RESULTS_DIR / f"ablation_{cond}.json").write_text(json.dumps(s, indent=2))
    print(f"\nSaved to {RESULTS_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
