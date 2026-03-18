---
name: verify-complete
description: Before writing your answer, verify completeness. Use this as a final check on every question to catch subset errors, wrong rows, and partial computations.
---

# Verification Protocol

**Run this check AFTER extracting data and BEFORE writing to `/app/answer.txt`.**

## The Three Completeness Questions

### 1. Did I use the TOTAL, not a subset?

Re-read the question. If it asks for:
- "total gross federal debt" → Did I use the Grand Total row, or just "Held by the public"?
- "total gross obligations within and outside" → Did I sum both, or just one?
- "total nominal capital" → Did I use Total Capital, or just Capital Account?

**Rule:** If the question says "total" and your extracted value has a parent row in the table, you probably read the wrong line. Go back and find the aggregate.

### 2. Did I answer ALL parts?

Re-read the question. Count the sub-questions:
- "What is X and what is Y?" → Two values needed
- "Report the Euclidean norm of these two absolute changes" → Need BOTH changes before computing the norm
- "Comma-separated values in enclosed brackets" → Is the count right?

**Rule:** Count the values in your answer. Count the sub-questions. They must match.

### 3. Did I WRITE a numeric answer?

Never write an explanation to `/app/answer.txt`. Never write "Data not available" or "The corpus does not contain...". The scoring system expects a number.

**Rule:** If you cannot find the exact data, use the closest available data and state your assumptions in your reasoning — but ALWAYS write a number. A best-effort numeric answer scores better than no answer.

## Verification Script

When in doubt, run a verification step:

```bash
# Read what you're about to submit
cat /app/answer.txt

# Ask yourself:
# - Is this a number (or bracketed list of numbers)?
# - Does the format match what was requested?
# - Did I convert units correctly?
# - Did I round to the right decimal places?
```

## Common Completeness Failures

- Reading "Outside" instead of "Total" (Outside + Within)
- Reading "Held by public" instead of "Gross" (public + intragovernmental)
- Computing one component of a multi-part answer
- Surrendering with text instead of writing a best-effort number
- Using data from one time period when the question asks for a range

## Anti-Surrender Protocol (MANDATORY)

**You MUST write a numeric answer to `/app/answer.txt` before finishing. NO EXCEPTIONS.**

If you cannot find the exact data after extensive searching:
1. Use the closest available data (e.g., fiscal year data if calendar year is unavailable)
2. State your assumptions in `/app/draft.txt`
3. Compute your best estimate
4. Write the NUMBER to `/app/answer.txt`

A wrong number scores 0. No number also scores 0. But a wrong number that's close might score 1 (1% tolerance). Silence NEVER wins.

**Check:** Before your final step, run `cat /app/answer.txt`. If the file doesn't exist or contains text instead of a number, FIX IT NOW.

## Double-Computation Verification (MANDATORY for any math)

If your answer involves computation (percent change, CAGR, HP filter, index, norm):

```bash
cat > /app/verify.py << 'PYEOF'
# Recompute the answer a DIFFERENT way to verify
# Method 1: your original calculation
result1 = ...  # paste your formula

# Method 2: alternative calculation (different order, different formula)
result2 = ...  # compute same answer differently

print(f"Method 1: {result1}")
print(f"Method 2: {result2}")
print(f"Match: {abs(result1 - result2) < 0.01}")
PYEOF
python3 /app/verify.py
```

If the two methods disagree, investigate BEFORE writing your answer.

## Row Verification (MANDATORY for table lookups)

After extracting a value from a table:
1. Re-read the 3 lines ABOVE your target row — is there a more specific or more general row?
2. Re-read the 3 lines BELOW — did you grab a subtotal instead of the grand total?
3. Read the column header AGAIN — are you in the right column?
4. If extracting a date: count the row position from the table header to verify

## Bulletin Selection Audit (MANDATORY)

Before finalizing, verify your source bulletin:
- Did I find data in the bulletin the question pointed to, or a different one?
- If the question says "from [Month] bulletins", am I using those exact bulletins?
- Did I check whether a DIFFERENT bulletin (earlier or later) has the same data with different values?
- For calendar year-end (Dec 31) data: did I check JUNE bulletins?
- For January 31 data: did I check MARCH bulletins?
- For pre-1940 historical data: did I check the earliest bulletins in the corpus (1939)?
