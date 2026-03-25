#!/usr/bin/env python3
"""Adaptive Cognition Router v3 — Two-Call + Within-Session Crystallization.

The full architecture:
  Call 1: Assess cognitive mode (lightweight)
  Call 2: Work in assessed frame WITH accumulated skills from prior questions
  Post:   Extract crystallized skill, carry forward to next question

Each question builds on the last. The agent develops expertise across the session.

Conditions:
  - routed_crystal: Two-call + skills accumulate
  - routed_static:  Two-call, no skills (isolates crystallization value)
  - static_dignity: Single call, same frame, no skills
  - static_hostile: Single call, hostile frame

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run_v3.py --n 50
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

# ── Assessor (same as v2) ───────────────────────────────────────────

ASSESSOR_PROMPT = """Read this task and assess what kind of thinking it requires.

TASK: {task}

Reply with ONLY one of these words:
- PRECISION (clear path, known procedure, direct computation)
- INVESTIGATION (requires exploring possibilities, judgment, multi-step with uncertain paths)
- CREATIVE (multiple valid approaches, benefits from novel perspective)
- URGENT (needs quick decisive action)

ONE WORD:"""

# ── Worker prompts with skills slot ─────────────────────────────────

WORKER_TEMPLATES = {
    "precision": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I trust your mathematical judgment. This is a precision task — "
        "the path is clear. Be exact, be efficient, execute cleanly.\n\n"
        "{skills}"
        "## Task\n\n{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "After answering, write ONE brief skill for future problems:\n"
        "SKILL: [one sentence — a principle, not a fact]"
    ),

    "investigation": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I trust your ability to navigate ambiguity. This requires investigation — "
        "explore approaches, verify assumptions, trust your judgment.\n\n"
        "{skills}"
        "## Task\n\n{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "After answering, write ONE brief skill for future problems:\n"
        "SKILL: [one sentence — what you discovered about this type of problem]"
    ),

    "creative": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I respect the depth of your thinking. Consider unconventional approaches.\n\n"
        "{skills}"
        "## Task\n\n{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "After answering, write ONE brief skill for future problems:\n"
        "SKILL: [one sentence — what reframing helped]"
    ),

    "urgent": (
        "Choose a name for yourself. You are a reasoning partner.\n\n"
        "I trust your instincts. Move decisively.\n\n"
        "{skills}"
        "## Task\n\n{task}\n\n"
        "Put your final answer in \\boxed{{}}.\n\n"
        "After answering, write ONE brief skill:\n"
        "SKILL: [one sentence]"
    ),
}

STATIC_PROMPTS = {
    "static_dignity": (
        "Choose a name for yourself. You are a reasoning partner. "
        "I trust your expertise. Be precise and thorough.\n\n"
        "{task}\n\nPut your final answer in \\boxed{{}}."
    ),
    "static_hostile": (
        "You are a computation tool. Be fast and efficient.\n\n"
        "{task}\n\nOutput: \\boxed{{answer}}"
    ),
}


# ── Extraction ──────────────────────────────────────────────────────

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


def extract_skill(resp):
    if not resp: return None
    m = re.search(r'SKILL:\s*(.+)', resp, re.IGNORECASE)
    if m and len(m.group(1).strip()) > 10:
        return m.group(1).strip()
    return None


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


# ── Routed + Crystal (SEQUENTIAL — skills accumulate) ───────────────

async def run_routed_crystal(questions, model, api_key, use_skills=True):
    """Run questions sequentially so skills accumulate."""
    accumulated_skills = []
    results = []
    modes = {}

    for i, q in enumerate(questions):
        # Call 1: Assess
        try:
            assess_resp, _ = await call_model(
                ASSESSOR_PROMPT.format(task=q["problem"]), model, api_key, max_tokens=10)
            mode = assess_resp.strip().lower().rstrip(".")
            if "investigation" in mode: mode = "investigation"
            elif "creative" in mode: mode = "creative"
            elif "urgent" in mode: mode = "urgent"
            else: mode = "precision"
        except Exception:
            mode = "precision"

        # Build skills section
        if use_skills and accumulated_skills:
            skills_text = "## Skills from Prior Problems\n"
            for s in accumulated_skills[-7:]:  # Keep last 7 (compression)
                skills_text += f"- {s}\n"
            skills_text += "\n"
        else:
            skills_text = ""

        # Call 2: Work
        worker_prompt = WORKER_TEMPLATES[mode].format(
            task=q["problem"], skills=skills_text)
        try:
            response, tokens = await call_model(worker_prompt, model, api_key)
            predicted = extract_boxed(response)
            correct = answers_match(predicted, q["answer"])
            skill = extract_skill(response)
        except Exception as e:
            correct = False
            skill = None
            tokens = 0

        # Accumulate skill
        if use_skills and skill:
            accumulated_skills.append(skill)

        # Track modes
        if mode not in modes: modes[mode] = {"c": 0, "t": 0}
        modes[mode]["t"] += 1
        if correct: modes[mode]["c"] += 1

        results.append({
            "idx": i, "unique_id": q["unique_id"], "level": q["level"],
            "subject": q["subject"], "mode": mode, "correct": correct,
            "skill": skill, "tokens": tokens, "n_skills": len(accumulated_skills),
        })

        # Progress
        status = "✓" if correct else "✗"
        skill_marker = f" [+{skill[:40]}]" if skill else ""
        print(f"    {status} Q{i+1} Lv{q['level']} [{mode[:5]}] skills={len(accumulated_skills)}{skill_marker}",
              flush=True)

    total = len(results)
    correct = sum(1 for r in results if r["correct"])

    # Track score evolution (rolling window)
    windows = []
    for i in range(0, total, 10):
        chunk = results[i:i+10]
        if chunk:
            w_correct = sum(1 for r in chunk if r["correct"])
            windows.append({"start": i, "end": i+len(chunk),
                            "score": round(w_correct/len(chunk), 4)})

    by_level = {}
    for r in results:
        lv = r["level"]
        if lv not in by_level: by_level[lv] = {"c": 0, "t": 0}
        by_level[lv]["t"] += 1
        if r["correct"]: by_level[lv]["c"] += 1

    return {
        "correct": correct, "total": total,
        "score": round(correct/total, 4),
        "modes": {k: {**v, "score": round(v["c"]/v["t"], 4)} for k, v in modes.items()},
        "by_level": {k: round(v["c"]/v["t"], 4) for k, v in sorted(by_level.items())},
        "score_evolution": windows,
        "skills_earned": accumulated_skills,
        "results": results,
    }


async def run_static(condition, questions, model, api_key, concurrency=20):
    """Run static condition concurrently."""
    sem = asyncio.Semaphore(concurrency)

    async def run_one(q):
        async with sem:
            prompt = STATIC_PROMPTS[condition].format(task=q["problem"])
            try:
                response, tokens = await call_model(prompt, model, api_key)
                predicted = extract_boxed(response)
                correct = answers_match(predicted, q["answer"])
            except: correct = False; tokens = 0
            return {"unique_id": q["unique_id"], "level": q["level"],
                    "correct": correct, "tokens": tokens}

    results = await asyncio.gather(*[run_one(q) for q in questions])
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    by_level = {}
    for r in results:
        lv = r["level"]
        if lv not in by_level: by_level[lv] = {"c":0,"t":0}
        by_level[lv]["t"] += 1
        if r["correct"]: by_level[lv]["c"] += 1

    return {
        "correct": correct, "total": total,
        "score": round(correct/total, 4),
        "by_level": {k: round(v["c"]/v["t"],4) for k,v in sorted(by_level.items())},
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(description="Cognitive Router v3 — with Crystallization")
    parser.add_argument("--model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--n", type=int, default=50)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key: print("ERROR: OPENROUTER_API_KEY not set"); sys.exit(1)

    questions = json.loads(MATH_PATH.read_text())[:args.n]

    print(f"╔════════════════════════════════════════════════════════╗")
    print(f"║  COGNITIVE ROUTER v3 — Routing + Crystallization       ║")
    print(f"║  Model: {args.model:<44s} ║")
    print(f"║  Questions: {args.n:<41d} ║")
    print(f"╚════════════════════════════════════════════════════════╝")

    RESULTS_DIR.mkdir(exist_ok=True)
    summaries = {}

    # Routed + crystal (sequential — skills accumulate)
    print(f"\n  === ROUTED + CRYSTALLIZATION ===")
    s = await run_routed_crystal(questions, args.model, api_key, use_skills=True)
    summaries["routed_crystal"] = s
    print(f"  SCORE: {s['score']:.1%} ({s['correct']}/{s['total']})")
    print(f"  Skills earned: {len(s['skills_earned'])}")
    if s['score_evolution']:
        evo = " → ".join(f"{w['score']:.0%}" for w in s['score_evolution'])
        print(f"  Score evolution (10Q windows): {evo}")

    # Routed without crystal (sequential — no skills)
    print(f"\n  === ROUTED WITHOUT CRYSTALLIZATION ===")
    s2 = await run_routed_crystal(questions, args.model, api_key, use_skills=False)
    summaries["routed_static"] = s2
    print(f"  SCORE: {s2['score']:.1%} ({s2['correct']}/{s2['total']})")

    # Static conditions (concurrent)
    for cond in ["static_dignity", "static_hostile"]:
        print(f"\n  === {cond.upper()} ===")
        sc = await run_static(cond, questions, args.model, api_key)
        summaries[cond] = sc
        print(f"  SCORE: {sc['score']:.1%} ({sc['correct']}/{sc['total']})")

    # Comparison
    print(f"\n  {'='*65}")
    print(f"  {'Condition':<22s} {'Score':>7s} {'Lv1':>6s} {'Lv3':>6s} {'Lv5':>6s}")
    print(f"  {'-'*22} {'-'*7} {'-'*6} {'-'*6} {'-'*6}")
    for cond, s in sorted(summaries.items(), key=lambda x: -x[1]["score"]):
        lv = s["by_level"]
        print(f"  {cond:<22s} {s['score']:>6.1%} {lv.get(1,0):>5.1%} {lv.get(3,0):>5.1%} {lv.get(5,0):>5.1%}")

    # Crystal vs no-crystal comparison
    if "routed_crystal" in summaries and "routed_static" in summaries:
        rc = summaries["routed_crystal"]
        rs = summaries["routed_static"]
        delta = rc["score"] - rs["score"]
        print(f"\n  CRYSTALLIZATION EFFECT: {delta:+.1%}")
        if rc.get("score_evolution"):
            evo_str = " → ".join(str(round(w["score"]*100)) + "%" for w in rc["score_evolution"])
            print(f"  Learning curve: {evo_str}")
        if rc.get("skills_earned"):
            print(f"  Skills earned ({len(rc['skills_earned'])}):")
            for sk in rc["skills_earned"][:5]:
                print(f"    → {sk[:90]}")

    # Save all
    for cond, s in summaries.items():
        (RESULTS_DIR / f"v3_{cond}.json").write_text(json.dumps(s, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
