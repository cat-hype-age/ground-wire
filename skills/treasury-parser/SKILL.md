---
name: treasury-parser
description: Step-by-step procedure for answering questions from the Treasury Bulletin corpus. Handles table extraction, multi-document lookups, and computation.
---

# Treasury Document Parser — Execution Procedure

Follow these steps exactly for each question.

## Step 0: Orient Before You Search

Before extracting any numbers, orient yourself:
- **Identify the era:** Pre-1983 = monthly bulletins. Post-1983 = quarterly. This affects which files exist.
- **Check reporting basis:** The same metric can mean different things depending on the era. Interest on public debt switched from "due and payable" to "accrual" in 1955. Budget classifications changed multiple times.
- **Read footnotes FIRST:** Footnotes can completely change a number's meaning. Don't extract a value without checking what's below the table.
- **Start with metadata:** If a bulletin has a table of contents, skim it. It tells you what's in that issue and what's not.

## Step 1: Decompose the Question

Before touching any file, write down:
- **Metric:** What data is being asked for? (e.g., "total expenditures for national defense")
- **Time period:** Which months/years? Calendar or fiscal?
- **Source clue:** Which bulletin(s) likely contain this? (Data appears in bulletins AFTER the period)
- **Output format:** Units? Decimal places? Percent sign? Bracketed list?
- **Computation:** Simple lookup, or math required? (percent change, CAGR, geometric mean, etc.)

## Step 2: Search the Corpus

```bash
# Find files containing the key metric
grep -rl "KEYWORD" /app/corpus/ | sort

# For multiple keywords, chain greps
grep -rl "national defense" /app/corpus/ | xargs grep -l "expenditures"

# Check the file listing
cat /app/corpus/index.txt
```

Never open files speculatively. Let grep tell you where the data is.

## Step 3: Extract Data from Tables

When reading a file, locate the right table:
```bash
# Find the table section
grep -n "KEYWORD" /app/corpus/treasury_bulletin_YYYY_MM.txt
```

Then read surrounding context. Watch for:
- The "(In millions of dollars)" line above the table — this tells you the unit
- Multi-level headers with `>` separators
- Footnote markers (`1/`, `2/`, `r`) on values
- `nan` cells from OCR — these are empty, skip them

## Step 4: Compute

For simple lookups, extract the value and convert units.

For complex computations, write a Python script:
```bash
cat > /app/compute.py << 'PYEOF'
# Extract values and compute
values = [...]  # from the tables
result = ...    # computation
print(f"{result:.2f}")  # match requested precision
PYEOF
python3 /app/compute.py
```

Always verify:
- Did you convert units correctly? (millions → billions = divide by 1000)
- Did you use the right number of decimal places?
- Did you include/exclude the % sign as requested?

## Step 5: Write Answer

```bash
echo "YOUR_ANSWER" > /app/answer.txt
```

Write ONLY the answer — no explanation, no units unless the format requires it (like `%`).
