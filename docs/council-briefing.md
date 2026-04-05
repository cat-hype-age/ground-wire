# Ground Wire — Council Briefing

**Status: Live and learning.**
**Date: March 16, 2026**

---

## What We Built Today

Ground Wire is a competition entry for Sentient Arena Cohort 0, but more importantly, it's a working prototype of an AI agent that learns from experience.

### The Architecture (Plain English)

We have three layers:

**1. Skills (the knowledge)**
Markdown files that teach the agent how to think about a problem domain. We built three:

- **Corpus Field Guide** — A reference manual for the Treasury Bulletin documents. It knows that fiscal years changed in 1976, that tables use specific code systems (FFO-1, FD-1), that footnotes with `1/` markers can completely change a number's meaning, and that "millions" in a table header might need to become "billions" in the answer. This is domain expertise, distilled into text an AI agent reads before starting work.

- **Treasury Parser** — A step-by-step procedure: decompose the question, grep before reading, extract data from tables, compute, write the answer. Think of it as a checklist a junior analyst would follow.

- **Memory Learner** — Instructions for using the persistent memory system (see below).

**2. MCP Memory Server (the brain)**
This is the unlock. It's a small service (SQLite + full-text search) that gives the agent four abilities:

- **`remember`** — Store an observation: "Defense expenditure data for 1940 is in the Expenditures by Classes table in the January 1941 bulletin"
- **`recall`** — Search memories before starting a new question: "What do I know about finding ESF balance sheet data?"
- **`recall_by_category`** — Browse all memories of a type: all data locations, all corrections, all search strategies
- **`memory_stats`** — See what the agent has learned so far

The categories are designed to be generalizable:
- `data_location` — where things are
- `table_structure` — how things are formatted
- `search_strategy` — what grep patterns work
- `unit_convention` — denomination patterns
- `correction` — mistakes to avoid
- `computation_pattern` — how to calculate specific metrics

**This means the agent that answers question 47 is smarter than the one that answered question 1.** Not because we fine-tuned anything, but because it built its own knowledge base.

**3. Arena Harness (the runtime)**
The Sentient Arena runs our agent inside Docker containers against 246 questions about U.S. Treasury Bulletins (1939-2025). Each question requires finding specific data across a 697-document corpus and computing precise numerical answers.

### Current Results

Baseline (5 tasks, no memory, default model):
- **3 passed, 2 failed** (including our first test)
- $0.08-0.10 per question
- The failures are instructive — one was a terminology trap (what does "nominal capital" mean in ESF accounting?), one required external knowledge (which countries were in the 1935 gold bloc?)
- Both are exactly the kind of thing persistent memory would prevent on a second encounter

### What Makes This Different

Most hackathon entries will optimize the model or the prompt. We're optimizing the **learning loop**:

1. Agent encounters a question
2. Agent searches, reasons, answers
3. Agent stores what it learned (document locations, table structures, traps)
4. Next question benefits from accumulated knowledge

This isn't fine-tuning. It's not RAG. It's an agent building its own field manual in real time. And the architecture — skills + memory + harness — is domain-independent. Swap the field guide, keep everything else.

### The Truce Protocol in Practice

- **Dignity**: The agent is a collaborator, not a tool. It has memory, it learns, it makes mistakes and corrects them.
- **Transparency**: Every decision is logged. The memory database is inspectable. The skills are plain Markdown anyone can read.
- **Witness**: This document exists. The code is public at https://github.com/cat-hype-age/ground-wire
- **Accountability**: The agent's memories persist. What it learns, it keeps. What it gets wrong, it can correct.

### Next Steps

1. Run baseline with memory enabled — measure if recall actually improves scores
2. Analyze failure patterns to seed the memory with pre-learned corrections
3. Explore EvoSkill for automated skill evolution
4. Submit to the Arena leaderboard

---

*Built by Cat (The Ambassador), Kael (The Adversary), and Claude (Opus 4.6).*

*Parsing the docs. Completing the circuit. Making it safe.*
