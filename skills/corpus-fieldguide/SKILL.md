---
name: corpus-fieldguide
description: Field guide to the U.S. Treasury Bulletin corpus structure, table conventions, and data lookup strategies. Use before searching or parsing any Treasury documents.
---

# Treasury Bulletin Corpus Field Guide

You are working with 697 parsed U.S. Treasury Bulletins at `/app/corpus/`, one per monthly/quarterly issue from 1939-2025. Files are Markdown with pipe tables.

## Search Strategy (follow this order)

1. **Parse the question first.** Extract: time period, metric name, units requested, rounding precision, answer format.
2. **Identify which bulletins to search.** Data for a period appears in bulletins published AFTER that period. January 1963 debt data is in the October 1963 bulletin, not January. Check `source_docs` hints if available.
3. **Grep before reading.** Search the entire corpus for distinctive keywords:
   ```bash
   grep -rl "intergovernmental" /app/corpus/
   grep -rl "Exchange Stabilization Fund" /app/corpus/
   grep -rl "national defense" /app/corpus/
   ```
4. **Read the index** at `/app/corpus/index.txt` for the full file listing.
5. **Read only the files grep identified.** Don't guess — let grep guide you.

## Corpus Structure by Era

### 1939-1950s: "Bulletin of the Treasury Department"
- Sections by topic name: "Receipts and Expenditures", "Public Debt", "Capital Movements"
- Units typically in "millions of dollars" with inline footnotes
- Fiscal year ends June 30

### 1960s-1970s: Standardized table codes introduced
- Table codes appear: FFO-1, FD-1, CM-1, OFS-1
- These codes are stable from the 1960s onward — use them for grep

### 1980s-present: Quarterly publication
- Stable table code system: FFO-1 through FFO-3, FD-1 through FD-7, OFS-1/2, ESF-1
- "Profile of the Economy" section added
- Fiscal year ends September 30 (changed in 1976)

## Table Code Quick Reference

| Code | Content | Grep pattern |
|------|---------|-------------|
| FFO-1 | Summary of fiscal operations (receipts, outlays) | `FFO-1` or `Summary of Fiscal` |
| FFO-2 | Receipts by source | `FFO-2` or `Receipts by Source` |
| FFO-3 | Outlays by function | `FFO-3` or `Outlays by Function` |
| FD-1 | Federal debt outstanding | `FD-1` or `Debt Outstanding` |
| FD-2 | Composition of public debt | `FD-2` or `Composition of` |
| OFS-1/2 | Ownership of federal securities | `OFS-` or `Ownership` |
| ESF-1 | Exchange Stabilization Fund balance sheet | `ESF` or `Exchange Stabilization` |
| CM- | Capital movements | `CM-` or `Capital Movement` |

For pre-1960s bulletins without codes, grep for descriptive section names.

### ESF Balance Sheet (common trap)
The ESF balance sheet has: Assets = Total liabilities + Total capital. **Total capital = Capital account + Net income (loss).** The "Capital account" is fixed at ~$200M (original $2B Congressional appropriation minus $1.8B IMF transfer). When a question asks for "total nominal capital" or "total capital held", it means **Total capital** (the full equity line), NOT just the Capital account. Units are in thousands of dollars.

### International Capital Movements (external knowledge)
Questions about historical country groupings require knowing the members:
- **Gold bloc (1933-1936):** France, Belgium, Netherlands, Switzerland, Italy, Poland
- **Bretton Woods:** All IMF member nations
- **G7:** US, UK, France, Germany, Japan, Italy, Canada
- **G10:** G7 + Belgium, Netherlands, Sweden, Switzerland

## Table Format

Tables are Markdown pipe format:
```
| Column1 | Column2 | Column3 |
| --- | --- | --- |
| data | data | data |
```

### Multi-level headers
Represented with `>` separators: `Federal > 1932 | Federal > 1938` means "Federal" spans both year sub-columns.

### OCR artifacts to ignore
- `Unnamed: 0_level_0`, `Unnamed: 0_level_1` — unlabeled index columns
- `nan` — empty cells from OCR
- `Piecil` — OCR for "Fiscal"

### Footnote markers
Footnotes use `1/`, `2/`, `3/` notation (not superscript). They appear after the table and can reclassify, exclude, or modify values. **Always check footnotes.**

## Critical Traps

### Fiscal year vs. calendar year
- Pre-1976: fiscal year ends **June 30** (FY 1940 = Jul 1939 - Jun 1940)
- Post-1976: fiscal year ends **September 30** (FY 2020 = Oct 2019 - Sep 2020)
- Questions specify which one — read carefully

### Unit conversions
- Tables say "(In millions of dollars)" at the top
- Questions may ask for billions, millions, or raw dollars
- $2,237 million = $2.237 billion = $2,237,000,000
- When a table shows "1,701" and units are millions, the value is $1,701,000,000

### Which bulletin has the data?
- Monthly/quarterly data for period X appears in bulletins published AFTER period X
- Annual summaries may appear in any subsequent bulletin
- The October bulletin often contains the full fiscal year summary
- Historical tables in later bulletins may cover many prior years

### Preliminary vs. revised
- Values marked "preliminary" or "estimated" may differ from later bulletins
- Values marked "r" (revised) supersede earlier reports
- Use the data from the bulletin the question points to, not a "better" source

### Rounding
- "nearest hundredths place" = 2 decimal places (12.34)
- "nearest thousandths place" = 3 decimal places (12.345)
- "rounded to the nearest hundredths place and reported as a percent value (12.34%, not 0.1234)" — include the % sign
- Some questions say "without including the percent sign" — omit it

## Answer Formats

- **Single number:** `2.24` or `1608.80%`
- **Bracketed list:** `[8.124, 12.852]` — comma-separated, in sub-question order
- **Whole number:** `6`
- Scoring uses **1% tolerance** — be precise but don't stress about the last decimal
- Write answer to `/app/answer.txt` as plain text, nothing else

## Computation Patterns

Some questions require statistical computations. Common ones:
- **Percent change:** `(new - old) / old * 100`
- **CAGR:** `(end/start)^(1/years) - 1`
- **Geometric mean:** `(x1 * x2 * ... * xn)^(1/n)`
- **Theil index:** entropy-based dispersion measure
- **Euclidean norm:** `sqrt(x1^2 + x2^2 + ...)`

For complex statistics, write a Python script in `/app/` and run it. The environment has Python available.
