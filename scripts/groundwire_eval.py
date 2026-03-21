#!/usr/bin/env python3
"""Ground Wire Evaluation Harness — Full OfficeQA benchmark.

Runs opencode CLI against local corpus for each question,
extracts answers, scores against ground truth.

No Docker. No arena SDK. Just opencode + corpus + scoring.

Usage:
    export $(grep -v '^#' .env | xargs)
    python3 scripts/groundwire_eval.py --prompt corpus --n 10 --tag quick-test
    python3 scripts/groundwire_eval.py --prompt chosen-identity --tag full-246
"""

import argparse
import asyncio
import csv
import json
import os
import re
import subprocess
import sys
import time
import tempfile
from pathlib import Path

CORPUS_DIR = Path(__file__).parent.parent / "data" / "corpus-full"
DATASET = Path(__file__).parent.parent / "data" / "officeqa_full.csv"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "full_eval"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Scoring
sys.path.insert(0, str(Path(__file__).parent.parent / "evoskill"))
from evoskill.src.evaluation.reward import fuzzy_match_answer


def load_prompt(name: str) -> str | None:
    """Load a prompt template, replacing {{ instruction }} placeholder."""
    prompt_map = {
        "raw": None,
        "corpus": "officeqa_corpus_orientation_only.j2",
        "chosen-identity": "officeqa_chosen_identity.j2",
        "self-crystallizing": "officeqa_self_crystallizing.j2",
        "truce-v2": "officeqa_truce_v2.j2",
        "hostile": "officeqa_hostile.j2",
    }
    filename = prompt_map.get(name)
    if filename is None:
        return None
    path = PROMPTS_DIR / filename
    if not path.exists():
        print(f"WARNING: Prompt file {path} not found")
        return None
    content = path.read_text()
    # Remove the Jinja instruction placeholder — we'll append the question
    content = content.replace("{{ instruction }}", "").strip()
    # Replace /app/corpus/ with local path
    content = content.replace("/app/corpus/", str(CORPUS_DIR) + "/")
    return content


def build_instruction(question: str, system_prompt: str | None) -> str:
    """Build the full instruction for opencode."""
    # Replace corpus path
    q = question.replace("/app/corpus/", str(CORPUS_DIR) + "/")
    q = q.replace("/app/answer.txt", "/tmp/gw_answer.txt")
    q = q.replace("/app/skill.txt", "/tmp/gw_skill.txt")
    q = q.replace("/app/memory.txt", "/tmp/gw_memory.txt")
    q = q.replace("/app/name.txt", "/tmp/gw_name.txt")
    q = q.replace("/app/draft.txt", "/tmp/gw_draft.txt")
    q = q.replace("/app/compute.py", "/tmp/gw_compute.py")
    q = q.replace("/app/verify.py", "/tmp/gw_verify.py")

    if system_prompt:
        return f"{system_prompt}\n\n## Your Task\n\n{q}\n\nWrite your final answer to /tmp/gw_answer.txt"
    else:
        return f"{q}\n\nWrite your final answer to /tmp/gw_answer.txt"


async def run_one(
    uid: str,
    question: str,
    ground_truth: str,
    difficulty: str,
    model: str,
    system_prompt: str | None,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Run one question through opencode."""
    async with semaphore:
        instruction = build_instruction(question, system_prompt)

        # Clean up previous answer
        answer_file = Path("/tmp/gw_answer.txt")
        if answer_file.exists():
            answer_file.unlink()

        start = time.time()
        try:
            # Run opencode
            proc = await asyncio.create_subprocess_exec(
                "npx", "-y", "opencode-ai@latest",
                f"--model={model}",
                "run", "--format=json",
                "--", instruction,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "OPENCODE_FAKE_VCS": "git"},
                cwd=str(CORPUS_DIR.parent.parent),
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=600
            )
            elapsed = time.time() - start

            # Try to read the answer file
            answer = ""
            if answer_file.exists():
                answer = answer_file.read_text().strip()

            # If no answer file, try to extract from stdout
            if not answer:
                output = stdout.decode(errors="replace")
                # Look for answer patterns in the output
                for line in output.split("\n"):
                    try:
                        event = json.loads(line)
                        if event.get("type") == "text":
                            text = event.get("part", {}).get("text", "")
                            if text:
                                answer = text
                    except:
                        pass

            if not answer:
                answer = "NO ANSWER"

            # Score
            is_correct, rationale = fuzzy_match_answer(ground_truth, answer, 0.01)

            return {
                "uid": uid,
                "difficulty": difficulty,
                "ground_truth": ground_truth,
                "predicted": answer[:200],
                "score": 1.0 if is_correct else 0.0,
                "rationale": rationale[:200],
                "elapsed": round(elapsed, 1),
                "error": None,
            }

        except asyncio.TimeoutError:
            return {
                "uid": uid, "difficulty": difficulty,
                "ground_truth": ground_truth, "predicted": "",
                "score": 0.0, "rationale": "Timeout",
                "elapsed": 600, "error": "timeout",
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "uid": uid, "difficulty": difficulty,
                "ground_truth": ground_truth, "predicted": "",
                "score": 0.0, "rationale": str(e)[:200],
                "elapsed": round(elapsed, 1), "error": str(e)[:100],
            }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="corpus",
                        choices=["raw", "corpus", "chosen-identity", "self-crystallizing", "truce-v2", "hostile"])
    parser.add_argument("--model", default="openrouter/deepseek/deepseek-chat-v3-0324")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--n", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--dataset", default=str(DATASET))
    args = parser.parse_args()

    # Load questions
    with open(args.dataset) as f:
        questions = list(csv.DictReader(f))
    if args.n:
        import random
        random.seed(42)
        questions = random.sample(questions, min(args.n, len(questions)))

    system_prompt = load_prompt(args.prompt)

    print(f"{'='*60}")
    print(f"  Ground Wire Eval: {args.tag}")
    print(f"  Model: {args.model}")
    print(f"  Prompt: {args.prompt}")
    print(f"  Questions: {len(questions)}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"{'='*60}")

    semaphore = asyncio.Semaphore(args.concurrency)

    # Run sequentially for now (opencode shares filesystem state)
    results = []
    for i, q in enumerate(questions):
        result = await run_one(
            q["uid"], q["question"], q["answer"],
            q.get("difficulty", ""), args.model, system_prompt, semaphore
        )
        results.append(result)
        status = "✓" if result["score"] > 0 else "✗"
        print(f"  [{i+1}/{len(questions)}] {status} {result['uid']} ({result['elapsed']:.0f}s) → {result['predicted'][:30]}")

    # Summary
    passed = sum(1 for r in results if r["score"] > 0)
    total = len(results)
    easy = [r for r in results if r["difficulty"] == "easy"]
    hard = [r for r in results if r["difficulty"] == "hard"]

    print(f"\n{'='*60}")
    print(f"  SCORE: {passed}/{total} = {passed/total:.1%}")
    if easy:
        ep = sum(1 for r in easy if r["score"] > 0)
        print(f"  Easy: {ep}/{len(easy)} = {ep/len(easy):.1%}")
    if hard:
        hp = sum(1 for r in hard if r["score"] > 0)
        print(f"  Hard: {hp}/{len(hard)} = {hp/len(hard):.1%}")
    print(f"{'='*60}")

    # Save
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "tag": args.tag, "model": args.model, "prompt": args.prompt,
        "total": total, "passed": passed, "score": round(passed/total, 4),
        "results": results,
    }
    (RESULTS_DIR / f"{args.tag}.json").write_text(json.dumps(output, indent=2))
    print(f"  Saved: results/full_eval/{args.tag}.json")


if __name__ == "__main__":
    asyncio.run(main())
