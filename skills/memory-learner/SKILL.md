---
name: memory-learner
description: Use persistent memory to learn from each question. Store observations about document structure, data locations, and successful strategies. Recall relevant memories before starting new questions.
---

# Memory-Augmented Learning

You have a persistent memory system with 40+ pre-seeded observations from previous agents' experience. **Use it before searching the corpus** — it will save you from repeating mistakes.

## How to Use Memory

Memory is available via bash scripts in your skills directory:

### Recall (ALWAYS do this first)
```bash
# Search memories by keyword
bash ~/.config/opencode/skills/memory-server/recall.sh "defense expenditure"

# Browse by category
bash ~/.config/opencode/skills/memory-server/recall.sh --category data_location
bash ~/.config/opencode/skills/memory-server/recall.sh --category correction
bash ~/.config/opencode/skills/memory-server/recall.sh --category search_strategy

# See what's in memory
bash ~/.config/opencode/skills/memory-server/recall.sh --stats
```

### Remember (after each question)
```bash
# Store what you learned
bash ~/.config/opencode/skills/memory-server/remember.sh "data_location" "ESF quarterly data in September bulletins" "ESF,quarterly,september"
bash ~/.config/opencode/skills/memory-server/remember.sh "correction" "Gold bloc question: sum only France, Netherlands, Switzerland, Italy after exclusions" "gold bloc,exclusion"
```

## Before Searching the Corpus — MANDATORY

1. Check memory for the TOPIC of the question:
```bash
bash ~/.config/opencode/skills/memory-server/recall.sh "keyword from question"
```

2. Check for known CORRECTIONS (mistakes from previous runs):
```bash
bash ~/.config/opencode/skills/memory-server/recall.sh --category correction
```

3. Check for relevant SEARCH STRATEGIES:
```bash
bash ~/.config/opencode/skills/memory-server/recall.sh --category search_strategy
```

## After Answering — Store What You Learned

Good things to remember:
- **data_location** — where you found the data (file, table, page)
- **table_structure** — how the table is formatted
- **search_strategy** — grep patterns that worked
- **unit_convention** — units used (millions, thousands, raw dollars)
- **correction** — mistakes you almost made or caught
- **computation_pattern** — how to compute a specific metric

## Memory Categories

Use these exact category names for consistent retrieval:
- `data_location` — where specific data lives in the corpus
- `table_structure` — how tables are formatted in specific bulletins
- `search_strategy` — grep patterns and search approaches that worked
- `unit_convention` — unit/denomination patterns by era or table type
- `correction` — mistakes to avoid, things that tripped you up
- `computation_pattern` — how to compute specific metrics (CAGR, Theil index, etc.)
