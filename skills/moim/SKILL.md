---
name: moim
description: Your tactical map. Read this first — it tells you what kind of question you're facing and what tools you have.
---

# MOIM — Map of Instructive Moments

Before you touch the corpus, spend 30 seconds here. Classify, then act.

## 1. Route the Question

Read the question. Write to `/app/draft.txt`:
1. What specific data you need
2. Your route:

| Route | When | What to do |
|-------|------|-----------|
| **FAST** | Clear lookup — one number, one table | Find the file (MCP or filename pattern), extract, answer. Skip skills. |
| **CAREFUL** | Multi-source, revision-sensitive, multi-step computation | Read the relevant skill(s) below. Use MCP tools to locate files and external data. |

Most questions are FAST. Don't over-classify.

## 2. Naming Patterns

Files are at `/app/corpus/` and named: `treasury_bulletin_YYYY_MM.txt`

Examples: `treasury_bulletin_1970_01.txt`, `treasury_bulletin_2011_09.txt`

- Before 1983: monthly issues (01–12)
- After 1983: quarterly issues (03, 06, 09, 12)

For fiscal year data: FY ends June 30 (pre-1976) or September 30 (post-1976). Calendar year ends December 31 — these are not interchangeable.

## 3. Domain Traps

These cost previous agents the most time. Read them now.

- **Revision trap:** Preliminary data gets revised 3–6 months later. If your number looks wrong, check bulletins from later months.
- **Column headers lie:** Multi-header tables are deceptive. After extracting any number, trace the FULL column path: "Parent → Sub → Column."
- **Method ambiguity:** "Average" = arithmetic mean. "Average YoY growth rate" = sum of annual % changes ÷ years. Not CAGR. The simple reading is right.
- **Never leave answer.txt empty.** A best-effort answer always beats no answer. Write a rough answer early, refine later.
- **Best answers came within 10 tool calls.** After that, verify rather than keep searching.

## 4. MCP Tools

You have live data tools — call them directly, no file reading needed:

| Tool | Use it when... |
|------|---------------|
| `lookup_cpi` | Need a CPI-U index value for any year (1939–2025) |
| `lookup_exchange_rate` | Need a historical currency conversion rate |
| `inflation_adjust` | Need to convert a dollar amount between years |
| `search_files_by_topic` | Can't find the right bulletin by filename guessing |
| `find_tables` | Looking for a specific table code across bulletins |
| `get_files_for_period` | Need all bulletins covering a date range |
| `get_file_info` | Check what tables are in a bulletin before reading it |

These are faster than searching the corpus. Use them.

## 5. Reference Skills

At `~/.config/goose/skills/` you have deeper guides. Read with `cat` only when your route calls for it:

| Skill | Read it when... |
|-------|----------------|
| `corpus-fieldguide/SKILL.md` | You need the full archive map — every table code, era, naming pattern |
| `doing-the-math/SKILL.md` | Computation guidance — averages, growth rates, adjustments |
| `reading-carefully/SKILL.md` | Extracting data from complex multi-header tables |
| `finding-your-way/SKILL.md` | You can't find a file or table and need navigation strategies |

FAST questions: skip these. CAREFUL questions: read 1–2 relevant skills, not all of them.
