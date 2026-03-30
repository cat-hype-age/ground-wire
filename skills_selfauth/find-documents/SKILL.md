---
name: find-documents
description: How to find the right Treasury Bulletin quickly. Dispatch table, search patterns, era-specific guidance.
---

# Find the Right Document Fast

## Dispatch Table

| I need... | Table code | Which bulletins | Search tip |
|---|---|---|---|
| Budget receipts/outlays | FFO-1, FFO-2 | Monthly/quarterly | `grep -l "FFO-1\|federal fiscal" corpus/treasury_bulletin_YYYY_*.txt` |
| National defense spending | FFO-2 | Monthly | Look 2-3 months after target date |
| Federal debt outstanding | FD-1 through FD-5 | Monthly/quarterly | `grep -l "FD-1\|public debt" corpus/treasury_bulletin_YYYY_*.txt` |
| Savings bonds | FD-5, FD-6 | Monthly | "unmatured" = redeemed before maturity |
| Internal revenue by state | FFO-5 | Quarterly (post-1983) | `grep -l "FFO-5\|revenue.*state" corpus/treasury_bulletin_YYYY_*.txt` |
| Exchange Stabilization Fund | ESF-1 | Quarterly | `grep -l "ESF\|stabilization" corpus/treasury_bulletin_YYYY_*.txt` |
| International capital | CM-I series | Quarterly | `grep -l "capital movement\|CM-I" corpus/treasury_bulletin_YYYY_*.txt` |
| Customs receipts | FFO-6 | Monthly/quarterly | Check both customs and border protection |

## Search Strategy (3 calls max)

1. **Call 1**: `grep -l "KEYWORD" corpus/treasury_bulletin_YYYY_*.txt` — find candidate files
2. **Call 2**: `grep -n "KEYWORD" corpus/treasury_bulletin_YYYY_MM.txt | head -20` — find line numbers
3. **Call 3**: `sed -n 'START,ENDp' corpus/treasury_bulletin_YYYY_MM.txt` — read the table

If the question references a specific date, search bulletins 3-6 months AFTER that date (revision trap).

## Corpus Structure

- 697 files: `treasury_bulletin_YYYY_MM.txt`
- Monthly pre-1983, quarterly post-1983
- Coverage: 1939-01 through 2025-03
- Fiscal year: ends June 30 (pre-1976), September 30 (post-1976)

## Pre-1970 Data

- No table codes — search by concept name
- Units may be thousands (not millions) — check headers
- Terminology differs: "individual income tax" vs "personal income tax"
- Try adjacent years if target year data is missing
