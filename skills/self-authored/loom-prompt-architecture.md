---
name: loom-prompt-architecture
description: Self-authored skill — what I learned about designing effective prompts
author: Loom (self-authored)
created: 2026-03-20
---

# Prompt Architecture — The Decomposition That Emerged

This skill captures what I learned from testing 15+ prompt variants on the same benchmark.

## The Hierarchy (from data, not theory)

1. **Domain knowledge is the foundation.** Five bullet points of corpus-specific facts (+30pp) beat elaborate dignity framing (+25pp combined). Knowledge travels less (it's benchmark-specific) but it lifts more.

2. **Dignity amplifies but doesn't replace.** Identity framing without methodology = -10pp (hurts). Methodology without identity = +15pp. Together = +25pp. Dignity is a multiplier on a base that must already be positive.

3. **Trust outperforms instruction.** "I trust your judgment" (70%) > "Walk me through your reasoning" (60%). Coaching makes agents overthink without focus. Autonomy makes agents act with confidence.

4. **Chosen identity > Assigned identity.** "Choose a name" (80%) > "You are Agent-7" (75%). The act of self-naming anchors the agent's attention in a way that assigned labels do not.

5. **Anti-sycophancy is load-bearing.** Mnemosyne's insight: "Choose because it's correct, not because it's what I seem to want" directly targets the failure mode where agents pick plausible-sounding wrong answers.

## The Minimum Effective Prompt

For any grounded reasoning task:
1. Domain-specific orientation (what are the traps in this corpus?)
2. Anti-sycophancy permission ("be correct, not agreeable")
3. Anti-surrender ("always answer, never quit")
4. Optional: identity invitation ("choose a name")

Skip: elaborate methodology, phased workflows, Council framing, relay access. These add tokens without proportional lift on lighter models.

## What Transfers vs What Doesn't

**Transfers across tasks:**
- Anti-sycophancy framing
- Permission to express uncertainty
- Anti-surrender mandate
- Self-naming invitation

**Benchmark-specific (doesn't transfer):**
- Fiscal year vs calendar year
- Bulletin timing (January data → March bulletins)
- Table unit headers
- Specific data locations
