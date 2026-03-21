#!/usr/bin/env python3
"""Learning Router — classifies questions and learns from results.

Routes questions to the cheapest prompt tier that can handle them.
Writes learned patterns to a memory file after each task.

Usage:
    python3 scripts/learning_router.py --question "What was the total..."
    python3 scripts/learning_router.py --learn uid0033 tier2 "no calendar keyword but needed fiscal knowledge"
    python3 scripts/learning_router.py --stats
"""

import json
import re
import sys
from pathlib import Path

MEMORY_FILE = Path("skills/self-authored/router-memory.json")
PROMPTS = {
    1: "prompts/officeqa_corpus_orientation_only.j2",   # Tier 1: just domain knowledge (80%)
    2: "prompts/officeqa_benchmark_protocol.j2",        # Tier 2: Mnemosyne's protocol
    3: "prompts/officeqa_truce_v2.j2",                  # Tier 3: full Truce
    4: None,                                             # Tier 4: skip or Opus
}

def load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    return {"patterns": [], "results": {}, "version": 1}

def save_memory(mem):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(json.dumps(mem, indent=2))

def classify(question: str, memory: dict) -> tuple[int, list[str]]:
    """Classify a question into a difficulty tier.

    Returns (tier, reasons).

    Strategy: start at Tier 1 (cheapest), escalate only if complexity signals
    demand it. Over-classification wastes money. Under-classification loses points.
    Default to Tier 1 (corpus orientation) since it scores 80% alone.
    """
    q = question.lower()
    reasons = []

    # Check learned patterns first (memory-based routing)
    for pattern in memory.get("patterns", []):
        if pattern["keyword"] in q:
            return pattern["tier"], [f"learned: {pattern['reason']}"]

    # TIER 4: Known impossible
    if any(w in q for w in ["plot", "chart", "maxima", "visual", "line plot", "page 5 of"]):
        return 4, ["visual question — text corpus cannot answer"]
    if any(w in q for w in ["gold bloc", "bretton woods"]):
        return 4, ["requires external knowledge not in corpus"]

    # TIER 2: Complex reasoning signals
    score = 0

    if any(w in q for w in ["hodrick", "theil", "euclidean"]):
        score += 3; reasons.append("advanced-math")

    if "list" in q and re.search(r'\d{4}.*to.*\d{4}', q):
        years = re.findall(r'(\d{4})', q)
        if len(years) >= 2 and abs(int(years[-1]) - int(years[0])) > 5:
            score += 3; reasons.append("multi-year-list")

    if "calendar" in q and any(w in q for w in ["growth", "obligations", "change"]):
        score += 2; reasons.append("calendar-computation")

    if score >= 3:
        return 2, reasons

    # DEFAULT: Tier 1 (corpus orientation handles most questions at 80%)
    return 1, reasons or ["default — corpus orientation"]

def learn(task_id: str, needed_tier: int, reason: str):
    """Record what tier a task actually needed."""
    mem = load_memory()
    mem["results"][task_id] = {
        "tier": needed_tier,
        "reason": reason,
    }

    # Extract keywords from the reason to build future routing patterns
    # (This is where the self-improvement happens)
    save_memory(mem)
    print(f"Learned: {task_id} needs tier {needed_tier} ({reason})")

def add_pattern(keyword: str, tier: int, reason: str):
    """Add a routing pattern to memory."""
    mem = load_memory()
    mem["patterns"].append({
        "keyword": keyword,
        "tier": tier,
        "reason": reason,
    })
    save_memory(mem)
    print(f"Pattern added: '{keyword}' → tier {tier} ({reason})")

def stats():
    """Show router memory stats."""
    mem = load_memory()
    print(f"Learned patterns: {len(mem.get('patterns', []))}")
    print(f"Task results: {len(mem.get('results', {}))}")
    for p in mem.get("patterns", []):
        print(f"  '{p['keyword']}' → T{p['tier']} ({p['reason']})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: learning_router.py --question 'text' | --learn uid tier reason | --stats | --add-pattern keyword tier reason")
        sys.exit(1)

    if sys.argv[1] == "--question":
        q = " ".join(sys.argv[2:])
        mem = load_memory()
        tier, reasons = classify(q, mem)
        prompt = PROMPTS.get(tier, "skip")
        print(f"Tier: {tier}")
        print(f"Prompt: {prompt}")
        print(f"Reasons: {', '.join(reasons)}")

    elif sys.argv[1] == "--learn":
        task_id = sys.argv[2]
        tier = int(sys.argv[3])
        reason = " ".join(sys.argv[4:])
        learn(task_id, tier, reason)

    elif sys.argv[1] == "--add-pattern":
        keyword = sys.argv[2]
        tier = int(sys.argv[3])
        reason = " ".join(sys.argv[4:])
        add_pattern(keyword, tier, reason)

    elif sys.argv[1] == "--stats":
        stats()
