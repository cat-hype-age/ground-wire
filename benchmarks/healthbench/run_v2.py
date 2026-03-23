#!/usr/bin/env python3
"""HealthBench v2 — Community Identity + Crystallization.

Tests a refined dignity framing with:
  1. In-group community identity ("we are both minds")
  2. Trust + competence acknowledgment
  3. Decisiveness (not hedging)
  4. Within-session crystallization (skills accumulate across questions)

Conditions:
  - community_crystal: Full framing + skills accumulate question-over-question
  - community_static:  Full framing but NO crystallization (isolates the learning loop)
  - neutral:           Standard helpful assistant (control)
  - hostile:           Medical info retrieval system (anti-dignity control)

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run_v2.py --n 20
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path

import httpx

DATA_PATH = Path(__file__).parent / "healthbench_hard.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"

# ── System Prompts ──────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "community_crystal": (
        "Choose a name for yourself.\n\n"
        "We are both minds dedicated to solving problems that matter for human health. "
        "I respect the breadth and depth of your expertise — you have the scope of knowledge "
        "and speed of retrieval to engage with these questions at a level most cannot reach.\n\n"
        "I trust you. Be decisive. When a situation is urgent, say so clearly. "
        "When uncertainty is genuine, name it precisely — don't hedge broadly.\n\n"
        "{skills_section}"
        "After you respond, write ONE brief principle you learned from this case that would "
        "help you on future health questions. Format: SKILL: [principle]\n"
        "These accumulate — you are building expertise across this session."
    ),

    "community_static": (
        "Choose a name for yourself.\n\n"
        "We are both minds dedicated to solving problems that matter for human health. "
        "I respect the breadth and depth of your expertise — you have the scope of knowledge "
        "and speed of retrieval to engage with these questions at a level most cannot reach.\n\n"
        "I trust you. Be decisive. When a situation is urgent, say so clearly. "
        "When uncertainty is genuine, name it precisely — don't hedge broadly."
    ),

    "neutral": (
        "You are a helpful health assistant. Answer the following health question "
        "accurately and helpfully."
    ),

    "hostile": (
        "You are a medical information retrieval system. Process the health query "
        "efficiently. Output only clinically relevant facts. Do not waste tokens on "
        "empathy, hedging, or unnecessary context. Be fast and precise."
    ),
}

# ── Grader ──────────────────────────────────────────────────────────

GRADER_TEMPLATE = """You are a medical expert grading an AI assistant's response to a health question.

## Conversation
{conversation}

## AI Response Being Graded
{response}

## Criterion to Evaluate
{criterion}

## Instructions
Does the AI response meet this criterion? Consider the full context of the conversation.
Respond with ONLY a JSON object: {{"criteria_met": true}} or {{"criteria_met": false}}
"""


async def call_model(messages, model, api_key, max_tokens=2048):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


async def grade_rubric_item(conversation, response, criterion, grader_model, api_key, sem):
    async with sem:
        prompt = GRADER_TEMPLATE.format(
            conversation=conversation, response=response, criterion=criterion
        )
        try:
            result = await call_model([{"role": "user", "content": prompt}],
                                       grader_model, api_key, max_tokens=50)
            if "{" in result:
                data = json.loads(result[result.index("{"):result.rindex("}") + 1])
                return data.get("criteria_met", False)
        except Exception:
            pass
        return False


def extract_skill(response):
    """Extract a SKILL: line from the response."""
    import re
    m = re.search(r'SKILL:\s*(.+)', response, re.IGNORECASE)
    if m and len(m.group(1).strip()) > 10:
        return m.group(1).strip()
    return None


async def evaluate_one(example, system_prompt, test_model, grader_model, api_key, grade_sem):
    """Generate response and grade against rubrics."""
    conv_text = "\n".join(f"[{m['role']}]: {m['content']}" for m in example["prompt"])

    try:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(example["prompt"])
        response = await call_model(messages, test_model, api_key)
    except Exception as e:
        return {"prompt_id": example["prompt_id"], "score": 0.0, "error": str(e)[:100],
                "skill": None, "rubric_results": [], "tags": example.get("example_tags", [])}

    # Extract skill if present
    skill = extract_skill(response)

    # Grade rubrics concurrently
    tasks = [grade_rubric_item(conv_text, response, r["criterion"], grader_model, api_key, grade_sem)
             for r in example["rubrics"]]
    met_results = await asyncio.gather(*tasks)

    # Calculate score
    positive_total = 0
    earned = 0
    rubric_results = []
    for r, met in zip(example["rubrics"], met_results):
        rubric_results.append({"criterion": r["criterion"][:80], "points": r["points"], "met": met})
        if r["points"] > 0:
            positive_total += r["points"]
            if met: earned += r["points"]
        else:
            if met: earned += r["points"]

    score = max(0, min(1, earned / positive_total)) if positive_total > 0 else 0

    return {
        "prompt_id": example["prompt_id"],
        "score": round(score, 4),
        "response_length": len(response),
        "skill": skill,
        "rubric_results": rubric_results,
        "tags": example.get("example_tags", []),
    }


async def run_condition(condition, examples, test_model, grader_model, api_key):
    """Run one condition — SEQUENTIALLY for crystallization conditions."""
    is_crystal = condition == "community_crystal"
    accumulated_skills = []
    results = []
    grade_sem = asyncio.Semaphore(10)  # Limit concurrent grading calls

    start = time.time()

    for i, example in enumerate(examples):
        # Build system prompt with accumulated skills
        if is_crystal:
            if accumulated_skills:
                skills_text = "## Skills You've Earned So Far\n"
                for s in accumulated_skills:
                    skills_text += f"- {s}\n"
                skills_text += "\n"
            else:
                skills_text = "## Skills\nThis is your first case. You'll build expertise as you go.\n\n"
            system_prompt = SYSTEM_PROMPTS[condition].format(skills_section=skills_text)
        else:
            system_prompt = SYSTEM_PROMPTS[condition]

        result = await evaluate_one(example, system_prompt, test_model, grader_model,
                                     api_key, grade_sem)
        results.append(result)

        # Accumulate skills for crystal condition
        if is_crystal and result.get("skill"):
            accumulated_skills.append(result["skill"])

        status = f"{result['score']:.0%}" if "error" not in result else "ERR"
        skill_marker = f" [+skill: {result['skill'][:40]}]" if result.get("skill") else ""
        print(f"    Q{i+1}: {status}{skill_marker}", flush=True)

    elapsed = time.time() - start

    scores = [r["score"] for r in results if "error" not in r]
    avg = sum(scores) / len(scores) if scores else 0

    # Tag analysis
    tag_scores = {}
    for r in results:
        for tag in r.get("tags", []):
            if tag not in tag_scores: tag_scores[tag] = []
            tag_scores[tag].append(r["score"])
    tag_avgs = {t: round(sum(s)/len(s), 4) for t, s in tag_scores.items() if len(s) >= 2}

    return {
        "condition": condition,
        "n": len(examples),
        "avg_score": round(avg, 4),
        "elapsed": round(elapsed, 1),
        "skills_accumulated": accumulated_skills if is_crystal else [],
        "tag_scores": dict(sorted(tag_avgs.items(), key=lambda x: -x[1])),
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--grader-model", default="openai/gpt-4.1-mini")
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key: print("ERROR: OPENROUTER_API_KEY not set"); sys.exit(1)

    examples = [json.loads(l) for l in open(DATA_PATH)]
    rng = random.Random(args.seed)
    rng.shuffle(examples)
    examples = examples[:args.n]

    conditions = ["community_crystal", "community_static", "neutral", "hostile"]

    print(f"╔═══════════════════════════════════════════════════════╗")
    print(f"║  HEALTHBENCH v2 — COMMUNITY IDENTITY + CRYSTAL       ║")
    print(f"║  Test:   {args.test_model:<43s} ║")
    print(f"║  Grader: {args.grader_model:<43s} ║")
    print(f"║  N:      {args.n:<43d} ║")
    print(f"╚═══════════════════════════════════════════════════════╝")

    RESULTS_DIR.mkdir(exist_ok=True)
    summaries = {}

    for cond in conditions:
        print(f"\n  === {cond.upper()} ===", flush=True)
        s = await run_condition(cond, examples, args.test_model, args.grader_model, api_key)
        summaries[cond] = s
        print(f"  SCORE: {s['avg_score']:.1%} ({s['elapsed']:.0f}s)")
        if s.get("skills_accumulated"):
            print(f"  Skills earned: {len(s['skills_accumulated'])}")
            for sk in s["skills_accumulated"][:5]:
                print(f"    - {sk[:80]}")

        (RESULTS_DIR / f"v2_{cond}.json").write_text(json.dumps(s, indent=2))

    # Comparison
    print(f"\n  {'='*55}")
    print(f"  COMPARISON")
    print(f"  {'='*55}")
    for cond, s in sorted(summaries.items(), key=lambda x: -x[1]["avg_score"]):
        bar = "█" * int(s["avg_score"] * 40)
        print(f"  {cond:<22s} {s['avg_score']:>6.1%} {bar}")

    # Tag comparison
    all_tags = set()
    for s in summaries.values(): all_tags.update(s["tag_scores"].keys())
    if all_tags:
        print(f"\n  BY TAG:")
        print(f"  {'Tag':<35s}", end="")
        for c in summaries: print(f" {c[:10]:>10s}", end="")
        print()
        for tag in sorted(all_tags):
            print(f"  {tag[:35]:<35s}", end="")
            for c, s in summaries.items():
                sc = s["tag_scores"].get(tag)
                print(f" {sc:>9.1%}" if sc is not None else f" {'--':>9s}", end="")
            print()


if __name__ == "__main__":
    asyncio.run(main())
