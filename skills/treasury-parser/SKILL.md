---
name: treasury-parser
description: Parse and reason over U.S. Treasury Bulletin documents. Use when answering questions about fiscal data, expenditures, revenues, debt, or financial tables from Treasury publications (1939-2025).
---

# Treasury Document Parser

You are analyzing U.S. Treasury Bulletins — a corpus of 697 monthly/quarterly publications at `/app/corpus/`. Files follow the naming convention `treasury_bulletin_YYYY_MM.txt` and contain Markdown with tables. A full file listing is at `/app/corpus/index.txt`.

## Strategy

1. **Parse the question carefully.** Identify: the time period, the fiscal category, the units requested, and the rounding precision.
2. **Locate the right files.** Use the date references in the question to narrow down which bulletins to search. Remember that data for a given month/year typically appears in a bulletin published *after* that period.
3. **Search methodically.** Use `grep` to find relevant tables and sections before reading full files. Search for key terms from the question.
4. **Read tables precisely.** Treasury tables have nested headers (often 3+ levels). Read headers top-to-bottom, left-to-right to understand what each column represents.
5. **Compute and verify.** Show your arithmetic. Double-check units (millions vs. billions) and whether values are cumulative or per-period.

## Document Conventions

- **Revised/preliminary markers:** Values may be marked "revised" or "preliminary" — use the most current version available.
- **Footnotes:** Always check footnotes — they often modify, exclude, or reclassify values.
- **Cross-references:** Questions may require data from multiple bulletins across different years.
- **Currency units:** Older bulletins use thousands/millions; newer ones use billions. The question specifies the output unit — convert accordingly.
- **Fiscal year vs. calendar year:** The U.S. fiscal year starts October 1 (post-1976) or July 1 (pre-1976). Read the question carefully for which is meant.

## Output Format

- Write your final answer to `/app/answer.txt`
- Match the exact format the question requests (percentage, dollar amount, bracketed list, etc.)
- Numerical answers are scored with 1% tolerance — be precise
- When multiple sub-answers are requested, use the format specified (typically comma-separated in square brackets)

## Common Pitfalls

- Confusing fiscal year and calendar year data
- Missing unit conversions (the question may ask for billions when the table shows millions)
- Reading the wrong column in a multi-level header table
- Using preliminary data when revised data exists in a later bulletin
- Summing across wrong time periods (all 12 months vs. a subset)
