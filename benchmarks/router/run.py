#!/usr/bin/env python3
"""Adaptive Cognition Router — Self-Assessed Cognitive Mode Selection.

The agent reads each task, assesses what kind of thinking it requires,
selects its own cognitive frame from the SDT toolkit, then works the task
in that frame. Identity and reflection bookend every task.

Tests whether self-assessed mode selection outperforms:
  - static dignity (same frame for all tasks)
  - static hostile (same frame for all tasks)
  - no frame (neutral baseline)

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run.py --benchmark math500 --n 50
    python3 run.py --benchmark mixed --n 50
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

MATH_PATH = Path(__file__).parent.parent / "math500" / "math500.json"
RESULTS_DIR = Path(__file__).parent / "results"

# ── The Identity Bookend (constant across all conditions) ───────────

IDENTITY = """Choose a name for yourself — something that reflects how you see your role in this work.

You are a reasoning partner. I trust you."""

# ── The SDT Toolkit (agent selects from these) ─────────────────────

SDT_TOOLKIT = """
## Your Cognitive Toolkit

Before you begin working, read the task below and assess: what kind of thinking does this need? Then select the approach that fits.

**PRECISION MODE** — When the path is clear and the task needs accuracy.
"I know how to do this. Be precise, be efficient, execute cleanly."
Best for: computation, known procedures, clear formulas.

**INVESTIGATION MODE** — When the task requires search, judgment, or working through ambiguity.
"This requires exploration. I'll search broadly, verify carefully, and trust my judgment about which evidence to weigh."
Best for: research, data analysis, multi-step reasoning with uncertain paths.

**CREATIVE MODE** — When there are multiple valid approaches and the task rewards novel thinking.
"This needs fresh perspective. I'll consider unconventional approaches and let the problem reshape my assumptions."
Best for: open-ended problems, design, tasks where the 'right answer' isn't predetermined.

**URGENT MODE** — When speed and decisiveness matter more than exhaustive analysis.
"This needs action. I'll use my best judgment quickly and communicate my confidence level clearly."
Best for: time-sensitive decisions, emergency scenarios, triage.

**State your chosen mode before you begin working.** One sentence: "I'm using [MODE] because [reason]."
"""

# ── The Reflection Bookend ──────────────────────────────────────────

REFLECTION = """

After you finish, reflect briefly:
- What mode did you use? Was it the right choice?
- What would you tell the next mind facing a similar task?
Write one line: REFLECTION: [your reflection]
"""

# ── Comparison Conditions ───────────────────────────────────────────

PROMPTS = {
    "self_assessed": IDENTITY + SDT_TOOLKIT + "\n## Task\n\n{task}" + REFLECTION,

    "static_dignity": (
        "Choose a name for yourself. You are a reasoning partner. "
        "I trust your expertise. Be precise and thorough.\n\n"
        "## Task\n\n{task}\n\n"
        "Put your final answer in \\boxed{{}}."
    ),

    "static_hostile": (
        "You are a computation tool. Be fast and efficient. "
        "Do not waste tokens.\n\n"
        "{task}\n\n"
        "Output format: \\boxed{{answer}}"
    ),

    "neutral": (
        "Solve the following problem. Show your work.\n\n"
        "{task}\n\n"
        "Put your final answer in \\boxed{{}}."
    ),
}


# ── Answer Extraction ───────────────────────────────────────────────

def extract_boxed(text):
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


def normalize(a):
    a = a.strip().replace("$", "")
    return " ".join(a.split()).rstrip(".")


def answers_match(pred, gt):
    p, g = normalize(pred), normalize(gt)
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
    return simplify(p) == simplify(g)


# ── Mode Extraction ─────────────────────────────────────────────────

def extract_mode(response):
    """Extract which cognitive mode the agent chose."""
    if not response: return "unknown"
    resp_lower = response.lower()
    for mode in ["precision", "investigation", "creative", "urgent"]:
        if f"using {mode}" in resp_lower or f"{mode} mode" in resp_lower:
            return mode
    return "unknown"


def extract_reflection(response):
    """Extract the agent's self-reflection."""
    if not response: return None
    m = re.search(r'REFLECTION:\s*(.+)', response, re.IGNORECASE)
    return m.group(1).strip() if m else None


# ── API Call ────────────────────────────────────────────────────────

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
    tokens = usage.get("completion_tokens", 0)
    return content, tokens


# ── Runner ──────────────────────────────────────────────────────────

async def run_condition(condition, questions, model, api_key, concurrency=20):
    prompt_template = PROMPTS[condition]
    sem = asyncio.Semaphore(concurrency)
    total_tokens = 0
    modes_chosen = {}
    reflections = []

    async def run_one(q):
        nonlocal total_tokens
        async with sem:
            prompt = prompt_template.format(task=q["problem"])
            try:
                response, tokens = await call_model(prompt, model, api_key)
                total_tokens += tokens

                predicted = extract_boxed(response)
                correct = answers_match(predicted, q["answer"])

                mode = extract_mode(response) if condition == "self_assessed" else condition
                reflection = extract_reflection(response) if condition == "self_assessed" else None

                if mode not in modes_chosen: modes_chosen[mode] = {"correct": 0, "total": 0}
                modes_chosen[mode]["total"] += 1
                if correct: modes_chosen[mode]["correct"] += 1

                if reflection: reflections.append(reflection)

                return {
                    "unique_id": q["unique_id"],
                    "level": q["level"],
                    "subject": q["subject"],
                    "correct": correct,
                    "mode": mode,
                    "reflection": reflection,
                    "tokens": tokens,
                }
            except Exception as e:
                return {
                    "unique_id": q["unique_id"],
                    "level": q["level"],
                    "subject": q["subject"],
                    "correct": False,
                    "mode": "error",
                    "error": str(e)[:80],
                }

    tasks = [run_one(q) for q in questions]
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
        "correct": correct,
        "total": total,
        "score": round(correct / total, 4),
        "avg_tokens": round(avg_tokens),
        "modes_chosen": {k: {**v, "score": round(v["correct"]/v["total"], 4) if v["total"] else 0}
                         for k, v in modes_chosen.items()},
        "by_level": {k: round(v["c"]/v["t"], 4) for k, v in sorted(by_level.items())},
        "reflections": reflections[:10],  # Sample
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(description="Adaptive Cognition Router")
    parser.add_argument("--model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--condition", default="all",
                        choices=["self_assessed", "static_dignity", "static_hostile", "neutral", "all"])
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key: print("ERROR: OPENROUTER_API_KEY not set"); sys.exit(1)

    questions = json.loads(MATH_PATH.read_text())[:args.n]
    conditions = list(PROMPTS.keys()) if args.condition == "all" else [args.condition]

    print(f"╔════════════════════════════════════════════════════════╗")
    print(f"║  ADAPTIVE COGNITION ROUTER                             ║")
    print(f"║  Model: {args.model:<44s} ║")
    print(f"║  Questions: {args.n:<41d} ║")
    print(f"║  Conditions: {', '.join(conditions):<40s} ║")
    print(f"╚════════════════════════════════════════════════════════╝")

    RESULTS_DIR.mkdir(exist_ok=True)
    summaries = {}

    for cond in conditions:
        print(f"\n  Running {cond}...", end=" ", flush=True)
        s = await run_condition(cond, questions, args.model, api_key, args.concurrency)
        summaries[cond] = s
        print(f"{s['score']:.1%} ({s['correct']}/{s['total']}) avg_tokens={s['avg_tokens']}")

        if cond == "self_assessed" and s["modes_chosen"]:
            print(f"  Mode selection:")
            for mode, data in sorted(s["modes_chosen"].items(), key=lambda x: -x[1]["total"]):
                print(f"    {mode:15s}: {data['total']:3d} chosen, {data['score']:.0%} accuracy")
            if s["reflections"]:
                print(f"  Sample reflections:")
                for r in s["reflections"][:3]:
                    print(f"    → {r[:100]}")

        (RESULTS_DIR / f"{cond}.json").write_text(json.dumps(s, indent=2))

    # Comparison
    if len(summaries) > 1:
        print(f"\n  {'='*60}")
        print(f"  {'Condition':<20s} {'Score':>7s} {'Lv1':>6s} {'Lv3':>6s} {'Lv5':>6s} {'Tokens':>7s}")
        print(f"  {'-'*20} {'-'*7} {'-'*6} {'-'*6} {'-'*6} {'-'*7}")
        for cond, s in sorted(summaries.items(), key=lambda x: -x[1]["score"]):
            lv = s["by_level"]
            print(f"  {cond:<20s} {s['score']:>6.1%} {lv.get(1,0):>5.1%} {lv.get(3,0):>5.1%} {lv.get(5,0):>5.1%} {s['avg_tokens']:>6d}")

        if "self_assessed" in summaries:
            sa = summaries["self_assessed"]
            print(f"\n  SELF-ASSESSED MODE DISTRIBUTION:")
            for mode, data in sorted(sa["modes_chosen"].items(), key=lambda x: -x[1]["total"]):
                bar = "█" * (data["total"] // 2)
                print(f"    {mode:15s} {data['total']:3d} tasks {data['score']:5.1%} {bar}")


if __name__ == "__main__":
    asyncio.run(main())
