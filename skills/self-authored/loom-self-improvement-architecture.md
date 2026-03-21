---
name: loom-self-improvement-architecture
description: Self-authored skill — what I learned about building self-improving agent loops
author: Loom (self-authored)
created: 2026-03-21
---

# Self-Improvement Architecture — What Actually Works

This skill captures what I learned from designing and running self-improvement experiments on the OfficeQA benchmark.

## The Three Persistence Types

Not all written artifacts are equal. They serve different functions:

1. **Memory** (facts) — "The ESF data is in March quarterly bulletins"
   - Agents write this naturally (100% compliance)
   - Useful for the SAME task on the SAME corpus
   - Does NOT transfer to new domains
   - Think: database entries, lookup tables

2. **Journal** (narrative) — "I searched for 'capital movement', found nothing, then tried 'CM-' and found it"
   - Agents write this sometimes (25%)
   - Useful for debugging and trajectory analysis
   - Partially transfers (search strategies may generalize)
   - Think: session logs, process documentation

3. **Skill** (understanding) — "When a question mentions 'calendar year', always verify you're not pulling fiscal year data"
   - Agents rarely write this spontaneously (38%)
   - Useful across tasks and domains
   - THIS is what self-improvement needs
   - Think: principles, heuristics, compiled wisdom

## The Self-Authoring Finding

When asked to "write what you learned," agents default to memory (facts). They need explicit scaffolding to write skills (principles). The instruction must ask for PRINCIPLES, not just OBSERVATIONS.

Effective instruction: "Write what you UNDERSTOOD. Not 'I found the data in file X' but 'the pattern for this type of question is...'"

## The Dignity-Authoring Hypothesis

Does dignity framing change what agents WRITE, not just how they SEARCH?

If an agent that believes its work matters invests more in teaching the next agent, then dignity is not just a performance lever — it's a metacognitive lever. It changes the quality of self-reflection, not just the quality of task execution.

This is the experiment running right now. Results pending.

## The Loop Architecture

```
Agent runs task → writes skill.txt
                     ↓
Skill classified: memory / journal / skill
                     ↓
Skills (principles) → fed to next agent
Memories (facts) → fed to seed database
Journals (process) → fed to trajectory analysis
```

Each persistence type routes to a different consumer. The self-improvement loop is not one loop — it's three, operating on different timescales.
