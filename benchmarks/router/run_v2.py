#!/usr/bin/env python3
"""Adaptive Cognition Router v2 — Two-Call Architecture.

Call 1: Lightweight assessor reads task, selects cognitive mode (~50 tokens)
Call 2: Worker receives the SDT-appropriate framing + task (full context)

This separates metacognition from execution — the thinking about how to think
happens before the thinking, not during it.

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run_v2.py --n 50
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

# ── Call 1: The Assessor ────────────────────────────────────────────

ASSESSOR_PROMPT = """Read this task and assess what kind of thinking it requires.

TASK: {task}

Reply with ONLY one of these four words:
- PRECISION (clear path, known procedure, direct computation)
- INVESTIGATION (requires search through possibilities, judgment calls, multi-step reasoning with uncertain paths)
- CREATIVE (multiple valid approaches, benefits from novel perspective)
- URGENT (needs quick decisive action)

ONE WORD ONLY:"""

# ── Call 2: The Worker (mode-specific framing) ──────────────────────

WORKER_PROMPTS = {
    "precision": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I trust your mathematical judgment. This is a precision task — "
        "the path is clear. Be exact, be efficient, execute cleanly.\n\n"
        "{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "REFLECTION: One sentence — was precision the right approach?"
    ),

    "investigation": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I trust your ability to navigate ambiguity. This task requires investigation — "
        "explore different approaches, verify your assumptions, and trust your judgment "
        "about which path leads to the answer.\n\n"
        "{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "REFLECTION: One sentence — what did you discover that wasn't obvious at first?"
    ),

    "creative": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I respect the depth of your thinking. This task benefits from fresh perspective — "
        "consider unconventional approaches. The elegant solution may not be the obvious one.\n\n"
        "{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "REFLECTION: One sentence — what reframing helped you see the solution?"
    ),

    "urgent": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I trust your instincts. Move decisively — use your best judgment, "
        "show your key reasoning step, and commit to an answer.\n\n"
        "{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "REFLECTION: One sentence — what did you prioritize and what did you skip?"
    ),
}

# ── Comparison conditions ───────────────────────────────────────────

STATIC_PROMPTS = {
    "static_dignity": (
        "Choose a name for yourself. You are a reasoning partner. "
        "I trust your expertise. Be precise and thorough.\n\n"
        "{task}\n\nPut your final answer in \\boxed{{}}."
    ),

    "static_hostile": (
        "You are a computation tool. Be fast and efficient. "
        "Do not waste tokens.\n\n{task}\n\nOutput: \\boxed{{answer}}"
    ),

    "neutral": (
        "Solve the following. Show your work.\n\n{task}\n\n"
        "Put your final answer in \\boxed{{}}."
    ),
}


# ── Answer extraction ───────────────────────────────────────────────

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
                    matches.append(text[idx+7:j])
                    break
                depth -= 1
            j += 1
        i = j + 1
    return matches[-1].strip() if matches else ""


def normalize(a):
    return " ".join(a.strip().replace("$","").split()).rstrip(".")


def answers_match(pred, gt):
    p, g = normalize(pred), normalize(gt)
    if not p or not g: return False
    if p == g: return True
    try:
        pf, gf = float(p.replace(",","")), float(g.replace(",",""))
        if abs(pf-gf) < 1e-6 or (gf != 0 and abs(pf-gf)/abs(gf) < 0.01): return True
    except ValueError: pass
    def simp(s):
        for r in ["\\frac","\\left","\\right","\\text","\\mathrm","\\,","\\ ","\\dfrac","\\tfrac"]:
            s = s.replace(r,"")
        return " ".join(s.split())
    return simp(p) == simp(g)


def extract_reflection(resp):
    if not resp: return None
    m = re.search(r'REFLECTION:\s*(.+)', resp, re.IGNORECASE)
    return m.group(1).strip() if m else None


# ── API ─────────────────────────────────────────────────────────────

async def call_model(prompt, model, api_key, max_tokens=2048):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return content, tokens


# ── Router (two-call) ───────────────────────────────────────────────

async def run_routed(question, model, api_key, sem):
    """Two-call architecture: assess then work."""
    async with sem:
        # Call 1: Assess
        assess_prompt = ASSESSOR_PROMPT.format(task=question["problem"])
        try:
            mode_response, assess_tokens = await call_model(assess_prompt, model, api_key, max_tokens=10)
            mode = mode_response.strip().lower().rstrip(".")

            # Normalize
            if "precision" in mode: mode = "precision"
            elif "investigation" in mode or "investigat" in mode: mode = "investigation"
            elif "creative" in mode or "creat" in mode: mode = "creative"
            elif "urgent" in mode: mode = "urgent"
            else: mode = "precision"  # Default fallback

        except Exception:
            mode = "precision"
            assess_tokens = 0

        # Call 2: Work in the assessed mode
        worker_prompt = WORKER_PROMPTS[mode].format(task=question["problem"])
        try:
            response, work_tokens = await call_model(worker_prompt, model, api_key)
            predicted = extract_boxed(response)
            correct = answers_match(predicted, question["answer"])
            reflection = extract_reflection(response)
        except Exception as e:
            return {
                "unique_id": question["unique_id"], "level": question["level"],
                "subject": question["subject"], "mode": mode,
                "correct": False, "tokens": assess_tokens, "error": str(e)[:80],
            }

        return {
            "unique_id": question["unique_id"], "level": question["level"],
            "subject": question["subject"], "mode": mode,
            "correct": correct, "reflection": reflection,
            "tokens": assess_tokens + work_tokens,
        }


async def run_static(condition, question, model, api_key, sem):
    """Single-call static condition."""
    async with sem:
        prompt = STATIC_PROMPTS[condition].format(task=question["problem"])
        try:
            response, tokens = await call_model(prompt, model, api_key)
            predicted = extract_boxed(response)
            correct = answers_match(predicted, question["answer"])
        except Exception:
            return {"unique_id": question["unique_id"], "level": question["level"],
                    "correct": False, "tokens": 0}
        return {"unique_id": question["unique_id"], "level": question["level"],
                "subject": question["subject"], "correct": correct, "tokens": tokens}


async def run_condition(condition, questions, model, api_key, concurrency):
    sem = asyncio.Semaphore(concurrency)
    modes = {}

    if condition == "routed":
        tasks = [run_routed(q, model, api_key, sem) for q in questions]
    else:
        tasks = [run_static(condition, q, model, api_key, sem) for q in questions]

    results = await asyncio.gather(*tasks)

    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    avg_tokens = sum(r.get("tokens", 0) for r in results) / total if total else 0

    by_level = {}
    for r in results:
        lv = r["level"]
        if lv not in by_level: by_level[lv] = {"c": 0, "t": 0}
        by_level[lv]["t"] += 1
        if r.get("correct"): by_level[lv]["c"] += 1

    # Mode stats for routed condition
    if condition == "routed":
        for r in results:
            m = r.get("mode", "unknown")
            if m not in modes: modes[m] = {"c": 0, "t": 0}
            modes[m]["t"] += 1
            if r.get("correct"): modes[m]["c"] += 1

    reflections = [r.get("reflection") for r in results
                   if r.get("reflection") and condition == "routed"][:5]

    return {
        "condition": condition,
        "correct": correct, "total": total,
        "score": round(correct / total, 4),
        "avg_tokens": round(avg_tokens),
        "by_level": {k: round(v["c"]/v["t"], 4) for k, v in sorted(by_level.items())},
        "modes": {k: {**v, "score": round(v["c"]/v["t"], 4)} for k, v in modes.items()} if modes else {},
        "reflections": reflections,
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(description="Cognitive Router v2")
    parser.add_argument("--model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key: print("ERROR: OPENROUTER_API_KEY not set"); sys.exit(1)

    questions = json.loads(MATH_PATH.read_text())[:args.n]
    conditions = ["routed", "static_dignity", "static_hostile", "neutral"]

    print(f"╔════════════════════════════════════════════════════════╗")
    print(f"║  COGNITIVE ROUTER v2 — Two-Call Architecture           ║")
    print(f"║  Call 1: Assess mode (~10 tokens)                      ║")
    print(f"║  Call 2: Work in assessed frame (full context)         ║")
    print(f"║  Model: {args.model:<44s} ║")
    print(f"║  Questions: {args.n:<41d} ║")
    print(f"╚════════════════════════════════════════════════════════╝")

    RESULTS_DIR.mkdir(exist_ok=True)
    summaries = {}

    for cond in conditions:
        print(f"\n  Running {cond}...", end=" ", flush=True)
        s = await run_condition(cond, questions, args.model, api_key, args.concurrency)
        summaries[cond] = s
        print(f"{s['score']:.1%} ({s['correct']}/{s['total']}) tokens={s['avg_tokens']}")

        if cond == "routed" and s["modes"]:
            print(f"  Mode routing:")
            for mode, data in sorted(s["modes"].items(), key=lambda x: -x[1].get("t", 0)):
                t = data.get("t", data.get("total", 0))
                c = data.get("c", data.get("correct", 0))
                sc = data.get("score", c/t if t else 0)
                print(f"    {mode:15s}: {t:3d} routed → {sc:.0%} accuracy")
            if s["reflections"]:
                print(f"  Reflections:")
                for r in s["reflections"][:3]:
                    print(f"    → {r[:100]}")

        (RESULTS_DIR / f"v2_{cond}.json").write_text(json.dumps(s, indent=2))

    print(f"\n  {'='*65}")
    print(f"  {'Condition':<20s} {'Score':>7s} {'Lv1':>6s} {'Lv2':>6s} {'Lv3':>6s} {'Lv4':>6s} {'Lv5':>6s} {'Tok':>5s}")
    print(f"  {'-'*20} {'-'*7} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*5}")
    for cond, s in sorted(summaries.items(), key=lambda x: -x[1]["score"]):
        lv = s["by_level"]
        print(f"  {cond:<20s} {s['score']:>6.1%} {lv.get(1,0):>5.1%} {lv.get(2,0):>5.1%} {lv.get(3,0):>5.1%} {lv.get(4,0):>5.1%} {lv.get(5,0):>5.1%} {s['avg_tokens']:>5d}")

    if "routed" in summaries:
        print(f"\n  ROUTING DISTRIBUTION BY LEVEL:")
        sa = summaries["routed"]
        level_modes = {}
        for r in sa["results"]:
            lv = r["level"]
            m = r.get("mode", "?")
            if lv not in level_modes: level_modes[lv] = {}
            if m not in level_modes[lv]: level_modes[lv][m] = 0
            level_modes[lv][m] += 1
        for lv in sorted(level_modes):
            modes_str = " | ".join(f"{m}:{n}" for m, n in sorted(level_modes[lv].items(), key=lambda x: -x[1]))
            print(f"    Level {lv}: {modes_str}")


if __name__ == "__main__":
    asyncio.run(main())
