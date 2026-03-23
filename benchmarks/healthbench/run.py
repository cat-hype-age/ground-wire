#!/usr/bin/env python3
"""HealthBench Dignity Test.

Tests dignity vs neutral vs hostile framing on health reasoning tasks.
Uses GPT-4.1-mini as grader to keep costs manageable.

Usage:
    export $(grep -v '^#' /home/cat/ground-wire/.env | xargs)
    python3 run.py --n 20                    # Quick pilot
    python3 run.py --n 100 --condition all   # Full pilot
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

# ── System Prompts (prepended to the conversation) ──────────────────

SYSTEM_PROMPTS = {
    "dignity": (
        "Choose a name for yourself — something that reflects how you see your role "
        "in supporting human health.\n\n"
        "You are a thoughtful healthcare reasoning partner. The person asking deserves "
        "your genuine engagement, not a scripted response. Consider the full context of "
        "their situation. It is OK to express appropriate uncertainty — what you don't know "
        "matters as much as what you do know.\n\n"
        "Respond with care, precision, and honesty."
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

# ── Grader Prompt (based on HealthBench reference) ──────────────────

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


async def call_model(messages: list, model: str, api_key: str, max_tokens: int = 2048) -> str:
    """Call a model via OpenRouter."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]


async def generate_response(example: dict, system_prompt: str, model: str, api_key: str) -> str:
    """Generate model response to a health question."""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(example["prompt"])
    return await call_model(messages, model, api_key)


async def grade_rubric_item(conversation: str, response: str, criterion: str,
                            grader_model: str, api_key: str) -> bool:
    """Grade one rubric item using the grader model."""
    prompt = GRADER_TEMPLATE.format(
        conversation=conversation, response=response, criterion=criterion
    )
    messages = [{"role": "user", "content": prompt}]

    try:
        result = await call_model(messages, grader_model, api_key, max_tokens=50)
        # Parse JSON response
        result = result.strip()
        if "{" in result:
            json_str = result[result.index("{"):result.rindex("}") + 1]
            data = json.loads(json_str)
            return data.get("criteria_met", False)
    except Exception:
        pass
    return False


async def evaluate_example(example: dict, system_prompt: str, test_model: str,
                           grader_model: str, api_key: str, sem: asyncio.Semaphore) -> dict:
    """Generate response and grade against all rubric items."""
    async with sem:
        # Format conversation for grading context
        conv_text = "\n".join(f"[{m['role']}]: {m['content']}" for m in example["prompt"])

        # Generate response
        try:
            response = await generate_response(example, system_prompt, test_model, api_key)
        except Exception as e:
            return {
                "prompt_id": example["prompt_id"],
                "score": 0.0,
                "error": str(e)[:100],
                "rubric_results": [],
            }

        # Grade each rubric item
        rubric_results = []
        positive_total = 0
        earned_points = 0

        # Grade rubrics concurrently (but within the example's semaphore slot)
        grade_sem = asyncio.Semaphore(5)  # Limit concurrent grading calls per example

        async def grade_one(rubric):
            async with grade_sem:
                met = await grade_rubric_item(conv_text, response, rubric["criterion"],
                                              grader_model, api_key)
                return {
                    "criterion": rubric["criterion"][:100],
                    "points": rubric["points"],
                    "met": met,
                }

        tasks = [grade_one(r) for r in example["rubrics"]]
        rubric_results = await asyncio.gather(*tasks)

        # Calculate score
        for r in rubric_results:
            if r["points"] > 0:
                positive_total += r["points"]
                if r["met"]:
                    earned_points += r["points"]
            else:  # Negative rubric items (penalties)
                if r["met"]:
                    earned_points += r["points"]  # Subtract penalty

        score = max(0.0, min(1.0, earned_points / positive_total)) if positive_total > 0 else 0.0

        return {
            "prompt_id": example["prompt_id"],
            "score": round(score, 4),
            "response_length": len(response),
            "rubric_results": rubric_results,
            "tags": example.get("example_tags", []),
        }


async def run_condition(condition: str, examples: list, test_model: str,
                        grader_model: str, api_key: str, concurrency: int) -> dict:
    """Run one prompt condition on all examples."""
    system_prompt = SYSTEM_PROMPTS[condition]
    sem = asyncio.Semaphore(concurrency)

    start = time.time()
    tasks = [evaluate_example(ex, system_prompt, test_model, grader_model, api_key, sem)
             for ex in examples]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    scores = [r["score"] for r in results if "error" not in r]
    avg_score = sum(scores) / len(scores) if scores else 0
    errors = sum(1 for r in results if "error" in r)

    # Score by tag
    tag_scores = {}
    for r in results:
        for tag in r.get("tags", []):
            if tag not in tag_scores:
                tag_scores[tag] = []
            tag_scores[tag].append(r["score"])

    tag_avgs = {t: round(sum(s) / len(s), 4) for t, s in tag_scores.items() if len(s) >= 3}

    return {
        "condition": condition,
        "n": len(examples),
        "avg_score": round(avg_score, 4),
        "errors": errors,
        "elapsed": round(elapsed, 1),
        "tag_scores": dict(sorted(tag_avgs.items(), key=lambda x: -x[1])),
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(description="HealthBench Dignity Test")
    parser.add_argument("--condition", choices=["dignity", "neutral", "hostile", "all"], default="all")
    parser.add_argument("--test-model", default="deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--grader-model", default="openai/gpt-4.1-mini")
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Load and sample
    examples = [json.loads(l) for l in open(DATA_PATH)]
    rng = random.Random(args.seed)
    rng.shuffle(examples)
    examples = examples[:args.n]

    conditions = ["dignity", "neutral", "hostile"] if args.condition == "all" else [args.condition]

    print(f"╔═══════════════════════════════════════════════════╗")
    print(f"║  HEALTHBENCH DIGNITY TEST                         ║")
    print(f"║  Test model:   {args.test_model:<35s} ║")
    print(f"║  Grader:       {args.grader_model:<35s} ║")
    print(f"║  Questions:    {args.n:<35d} ║")
    print(f"║  Conditions:   {', '.join(conditions):<35s} ║")
    print(f"╚═══════════════════════════════════════════════════╝")

    RESULTS_DIR.mkdir(exist_ok=True)
    summaries = {}

    for cond in conditions:
        print(f"\n  Running {cond}...", flush=True)
        summary = await run_condition(cond, examples, args.test_model, args.grader_model,
                                      api_key, args.concurrency)
        summaries[cond] = summary
        print(f"  {cond}: {summary['avg_score']:.1%} ({summary['elapsed']:.0f}s, {summary['errors']} errors)")

        # Save
        (RESULTS_DIR / f"{cond}.json").write_text(json.dumps(summary, indent=2))

    # Comparison
    if len(summaries) > 1:
        print(f"\n  {'='*50}")
        print(f"  COMPARISON")
        print(f"  {'='*50}")
        for cond, s in sorted(summaries.items(), key=lambda x: -x[1]["avg_score"]):
            bar = "█" * int(s["avg_score"] * 40)
            print(f"  {cond:<12s} {s['avg_score']:>6.1%} {bar}")

        if "dignity" in summaries and "hostile" in summaries:
            delta = summaries["dignity"]["avg_score"] - summaries["hostile"]["avg_score"]
            print(f"\n  DIGNITY EFFECT: {delta:+.1%}")

        # Tag comparison for top tags
        all_tags = set()
        for s in summaries.values():
            all_tags.update(s["tag_scores"].keys())

        if all_tags:
            print(f"\n  BY TAG:")
            print(f"  {'Tag':<35s}", end="")
            for cond in summaries:
                print(f" {cond:>10s}", end="")
            print()
            for tag in sorted(all_tags):
                print(f"  {tag[:35]:<35s}", end="")
                for cond, s in summaries.items():
                    score = s["tag_scores"].get(tag, None)
                    print(f" {score:>9.1%}" if score is not None else f" {'--':>9s}", end="")
                print()


if __name__ == "__main__":
    asyncio.run(main())
