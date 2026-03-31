---
name: uncertainty-protocol
description: When uncertain about a term, metric, or interpretation — make your best assumption, state it, and proceed. Never freeze.
---

# Uncertainty Protocol: Assume, State, Proceed

**Problem**: When you encounter an unfamiliar term or ambiguous question, you freeze and search endlessly without computing.

**The Rule**: If you don't know something after 2 search attempts, MAKE AN ASSUMPTION and proceed.

## When You Don't Know a Term
1. Search the corpus for the exact term (1 attempt)
2. Search for related terms or synonyms (1 attempt)  
3. If still unclear: state your best interpretation, compute with it, write your answer
4. A wrong-but-computed answer beats an empty answer every time

## When You're Unsure Which Data to Use
- Use the most recent source
- Use the most specific match to the question's wording
- If two values seem equally valid, pick one and compute
- Write the answer. You can always update it.

## When You Don't Have All the Years/Months
- Compute with what you have
- 4 data points > 0 data points
- Partial computation > empty answer

## Format Safety
When writing to /app/answer.txt:
- Write ONLY the number (no units, no labels, no explanation)
- Example: `echo "36080" > /app/answer.txt`
- NOT: `echo "36080 million" > /app/answer.txt`
- NOT: `echo "The answer is 36080" > /app/answer.txt`
