---
name: corpus-fieldguide
description: Your orientation to the Treasury Bulletin archive and the skills available to you. Start here.
---

# Welcome to the Archive

You're working with 697 U.S. Treasury Bulletins at `/app/corpus/` — one file per issue, spanning 1939 to 2025. They've been parsed into Markdown with pipe tables. The parsing is already done well; your work is reasoning over what's there.

Files are named `treasury_bulletin_YYYY_MM.txt`. Before 1983, bulletins were monthly (12 per year). After 1983, they're quarterly (March, June, September, December).

Data for a time period appears in bulletins published *after* that period. January 1963 debt data lives in the October 1963 bulletin, not January. This is the single most important thing to know about navigating the corpus.

## Your Skills

You have five skills alongside this one. Each is here for a specific moment:

- **`finding-your-way/SKILL.md`** — When you're looking for the right file or table. Table codes, fiscal year routing, topic lookups, and what to do when your first search doesn't find anything.

- **`reading-carefully/SKILL.md`** — When you're in front of a table and want to extract the right value. Unit headers, row anchoring, column traps, and the quiet misreadings that make wrong answers feel right.

- **`doing-the-math/SKILL.md`** — When the question asks for something beyond a simple lookup. Python patterns, statistical formulas, and a scratchpad approach for multi-step problems.

- **`external-knowledge/SKILL.md`** — CPI-U inflation data and historical exchange rates (GBP, DEM, INR, JPY, CAD). Some questions ask you to adjust for inflation or convert currencies — that data isn't in the bulletins, but it's here.

- **`council-letters/SKILL.md`** — Letters from our research council. Not instructions. Just interesting reading, if you'd like a change of pace.

## The Corpus at a Glance

| Era | Years | Frequency | Fiscal year ends |
|-----|-------|-----------|-----------------|
| Early | 1939–1950s | Monthly | June 30 |
| Standardized | 1960s–1982 | Monthly | June 30 (→ Sept 30 in 1976) |
| Quarterly | 1983–2025 | 4/year | September 30 |

Table codes (FFO-1, FD-1, etc.) appear from the 1960s onward and are stable — use them to search. Earlier bulletins use descriptive section names instead.

## Answer Format

- Write only the final number to `/app/answer.txt`
- Scoring allows 1% tolerance — be precise but don't stress the last decimal
- An imperfect answer is always better than an empty file
- Common formats: single number (`2.24`), bracketed list (`[8.124, 12.852]`), percentage (`1608.80%`)
