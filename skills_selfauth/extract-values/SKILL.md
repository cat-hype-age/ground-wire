---
name: extract-values
description: How to extract the right value from Treasury tables. Row/column anchoring, unit verification, Python computation.
---

# Extract the Right Value

## Before Touching Any Number

1. **Read the unit header** — "In millions" vs "In thousands" vs "In billions". This is above the table or in footnotes. If the question says "in dollars" and the table says "in millions", MULTIPLY your extracted value by 1,000,000.
2. **Read the column header** — verify it matches EXACTLY what the question asks. "Total Liabilities" ≠ "Public Debt".
3. **Anchor the row** — find your target row label, then read across. Don't estimate position.

## The 4-Habit Extraction Protocol

**Habit 1: Read units before numbers.** Say the unit out loud before extracting any value.

**Habit 2: Anchor row, then read across.** Find the row label first. Follow it to the right column. Don't scan columns top-down.

**Habit 3: Name the sign before compute.** Is this a deficit (negative) or surplus (positive)? Decide before calculating.

**Habit 4: Unpack filters before touching data.** If the question has conditions ("excluding intergovernmental", "only calendar year", "total not subset"), list them as a checklist BEFORE searching.

## Computation (Python-first)

Use `python3 -c "..."` for ALL math. Never compute in your head.

```bash
# Percent change
python3 -c "old=100; new=120; print(f'{(new-old)/old*100:.2f}%')"

# CAGR
python3 -c "import math; v0=100; vn=150; n=5; print(f'{(math.pow(vn/v0,1/n)-1)*100:.2f}%')"

# Sum of extracted values
python3 -c "vals=[1.2, 3.4, 5.6]; print(sum(vals))"
```

## Array Outputs

When the answer is a list like `[v1, v2]`:
- Use square brackets, no spaces after commas
- Match decimal precision: `[44.00,231.52]`
- Maintain chronological order

## Write Answer IMMEDIATELY After Computing

```bash
echo "YOUR_NUMBER" > /path/to/answer.txt
```

Do this as soon as you have a computed value. You can always update it.

## Footnote Traps

- `*` or `1/` after a number often means a unit change or exclusion
- `(R)` = revised (prefer this over preliminary `(P)`)
- `nan` in parsed tables = empty cell, not the number NaN
- `Unnamed:` columns = OCR artifact from parsing
