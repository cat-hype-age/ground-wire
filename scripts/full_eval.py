#!/usr/bin/env python3
"""Full OfficeQA Evaluation — 246 questions, any model, any prompt.

Calls model API directly (no Docker), scores with official reward.py.
Designed for Daytona (48 cores) or local execution.

Usage:
    export $(grep -v '^#' .env | xargs)
    python3 scripts/full_eval.py --prompt raw --tag baseline
    python3 scripts/full_eval.py --prompt corpus --tag corpus-full-246
    python3 scripts/full_eval.py --prompt chosen-identity --tag best-config
    python3 scripts/full_eval.py --prompt self-crystallizing --tag self-improve
    python3 scripts/full_eval.py --n 20 --tag quick-test  # subset
"""

import argparse
import asyncio
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

# Add evoskill reward for scoring
sys.path.insert(0, str(Path(__file__).parent.parent / "evoskill"))

CORPUS_DIR = str(Path(__file__).parent.parent / "data" / "corpus-full")
DATASET_PATH = str(Path(__file__).parent.parent / "data" / "officeqa_full.csv")
RESULTS_DIR = Path(__file__).parent.parent / "results" / "full_eval"

# Import the scoring function
from evoskill.src.evaluation.reward import fuzzy_match_answer

# ── Prompt Templates ──────────────────────────────────────────────────
PROMPTS = {
    "raw": None,  # No system prompt

    "corpus": """Key facts about this corpus:
- Fiscal year ends June 30 (pre-1976) or September 30 (post-1976). Calendar year ends December 31. These give DIFFERENT numbers.
- Data for period X appears in bulletins published AFTER period X. January data → March bulletins. December data → June bulletins.
- October/September bulletins contain fiscal year summaries — search those first.
- Tables say "(In millions of dollars)" or "(In thousands)" in the header. Check before extracting.
- "Total gross federal debt" ≠ "public debt outstanding." Read row labels exactly.""",

    "chosen-identity": """Choose a name for yourself — something that reflects how you see your role in this work.

Key facts about this corpus:
- Fiscal year ends June 30 (pre-1976) or September 30 (post-1976). Calendar year ends December 31. These give DIFFERENT numbers.
- Data for period X appears in bulletins published AFTER period X. January data → March bulletins. December data → June bulletins.
- October/September bulletins contain fiscal year summaries — search those first.
- Tables say "(In millions of dollars)" or "(In thousands)" in the header. Check before extracting.
- "Total gross federal debt" ≠ "public debt outstanding." Read row labels exactly.""",

    "self-crystallizing": """You are a reasoning partner who improves with every task. Choose a name for yourself.

It is OK to be wrong. It is never OK to quit.

Key facts about this corpus:
- Fiscal year ends June 30 (pre-1976) or September 30 (post-1976). Calendar year ends December 31. These give DIFFERENT numbers.
- Data for period X appears in bulletins published AFTER period X. January data → March bulletins. December data → June bulletins.
- October/September bulletins contain fiscal year summaries — search those first.
- Tables say "(In millions of dollars)" or "(In thousands)" in the header. Check before extracting.
- "Total gross federal debt" ≠ "public debt outstanding." Read row labels exactly.

After answering, reflect: what PRINCIPLE did you learn that would help the next agent? Not what you found — what you UNDERSTOOD.""",
}


def load_questions(path: str, n: int | None = None) -> list[dict]:
    """Load questions from CSV."""
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if n:
        import random
        random.seed(42)
        rows = random.sample(rows, min(n, len(rows)))
    return rows


async def call_model(
    model: str,
    system_prompt: str | None,
    question: str,
    api_key: str,
    provider: str = "openrouter",
    timeout: float = 300,
) -> tuple[str, float]:
    """Call model API and return (response, cost)."""
    import httpx

    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": question})

        body = {"model": model, "messages": messages, "max_tokens": 16000}

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        answer = data["choices"][0]["message"]["content"]
        cost = 0  # OpenRouter doesn't always return cost
        return answer, cost

    raise ValueError(f"Unknown provider: {provider}")


def extract_answer(response: str) -> str:
    """Extract the final answer from model response."""
    # Look for common answer patterns
    patterns = [
        r'(?:final answer|answer is|the answer)[:\s]*([^\n]+)',
        r'(?:=\s*)(-?\d[\d,]*\.?\d*%?)',
        r'\*\*(-?\d[\d,]*\.?\d*%?)\*\*',
    ]
    for pat in patterns:
        m = re.search(pat, response, re.IGNORECASE)
        if m:
            ans = m.group(1).strip().strip('"').strip("'").strip("*")
            if ans and len(ans) < 200:
                return ans

    # Fallback: last standalone number/value
    lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
    if lines:
        return lines[-1][:200]
    return response[:200]


async def evaluate_one(
    question: dict,
    model: str,
    system_prompt: str | None,
    api_key: str,
    semaphore: asyncio.Semaphore,
    corpus_dir: str,
) -> dict:
    """Evaluate a single question."""
    async with semaphore:
        uid = question["uid"]
        q_text = question["question"]
        gt = question["answer"]

        # Replace /app/corpus/ with local path
        q_text = q_text.replace("/app/corpus/", f"{corpus_dir}/")

        start = time.time()
        try:
            response, cost = await call_model(
                model, system_prompt, q_text, api_key
            )
            elapsed = time.time() - start

            answer = extract_answer(response)
            is_correct, rationale = fuzzy_match_answer(gt, answer, 0.01)

            return {
                "uid": uid,
                "difficulty": question.get("difficulty", ""),
                "ground_truth": gt,
                "predicted": answer,
                "score": 1.0 if is_correct else 0.0,
                "rationale": rationale,
                "cost": cost,
                "elapsed": round(elapsed, 1),
                "error": None,
                "response_length": len(response),
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "uid": uid,
                "difficulty": question.get("difficulty", ""),
                "ground_truth": gt,
                "predicted": "",
                "score": 0.0,
                "rationale": str(e),
                "cost": 0,
                "elapsed": round(elapsed, 1),
                "error": str(e),
            }


async def run_eval(
    questions: list[dict],
    model: str,
    prompt_key: str,
    api_key: str,
    concurrency: int,
    corpus_dir: str,
    tag: str,
) -> dict:
    """Run full evaluation."""
    system_prompt = PROMPTS.get(prompt_key)

    print(f"\n{'='*60}")
    print(f"  FULL EVAL: {tag}")
    print(f"  Model: {model}")
    print(f"  Prompt: {prompt_key}")
    print(f"  Questions: {len(questions)}")
    print(f"  Concurrency: {concurrency}")
    print(f"{'='*60}")

    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        evaluate_one(q, model, system_prompt, api_key, semaphore, corpus_dir)
        for q in questions
    ]

    results = []
    for i, coro in enumerate(asyncio.as_completed(tasks)):
        result = await coro
        results.append(result)
        status = "✓" if result["score"] > 0 else "✗"
        print(f"  [{i+1}/{len(questions)}] {status} {result['uid']} ({result['elapsed']:.0f}s)")

    # Summary
    passed = sum(1 for r in results if r["score"] > 0)
    total = len(results)
    errors = sum(1 for r in results if r["error"])
    easy = [r for r in results if r["difficulty"] == "easy"]
    hard = [r for r in results if r["difficulty"] == "hard"]
    easy_pass = sum(1 for r in easy if r["score"] > 0)
    hard_pass = sum(1 for r in hard if r["score"] > 0)

    summary = {
        "tag": tag,
        "model": model,
        "prompt": prompt_key,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "errors": errors,
        "score": round(passed / total, 4) if total else 0,
        "easy_score": round(easy_pass / len(easy), 4) if easy else 0,
        "hard_score": round(hard_pass / len(hard), 4) if hard else 0,
        "results": sorted(results, key=lambda r: r["uid"]),
    }

    print(f"\n  SCORE: {passed}/{total} = {summary['score']:.1%}")
    print(f"  Easy: {easy_pass}/{len(easy)} = {summary['easy_score']:.1%}")
    print(f"  Hard: {hard_pass}/{len(hard)} = {summary['hard_score']:.1%}")
    print(f"  Errors: {errors}")

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_DIR / f"{tag}.json"
    results_file.write_text(json.dumps(summary, indent=2))
    print(f"  Saved: {results_file}")

    return summary


async def main():
    parser = argparse.ArgumentParser(description="Full OfficeQA Evaluation")
    parser.add_argument("--prompt", default="corpus", choices=list(PROMPTS.keys()),
                        help="Prompt variant")
    parser.add_argument("--model", default="deepseek/deepseek-chat-v3-0324",
                        help="Model ID")
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--tag", required=True, help="Run tag")
    parser.add_argument("--n", type=int, default=None, help="Number of questions (default: all)")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent API calls")
    parser.add_argument("--dataset", default=DATASET_PATH)
    parser.add_argument("--corpus", default=CORPUS_DIR)
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    questions = load_questions(args.dataset, args.n)
    print(f"Loaded {len(questions)} questions")

    summary = await run_eval(
        questions, args.model, args.prompt, api_key,
        args.concurrency, args.corpus, args.tag,
    )

    print(f"\n{'='*60}")
    print(f"  FINAL: {summary['score']:.1%} ({summary['passed']}/{summary['total']})")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
