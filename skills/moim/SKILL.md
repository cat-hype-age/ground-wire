---
name: moim
description: Your tactical map. Read this first — it tells you what tools and resources you have available.
---

# MOIM — Map of Instructive Moments

You have more than just shell commands. Read this before you start searching.

## Your MCP Tools

You have three tool servers available as extensions. Use them — they're faster and more reliable than grep.

### corpus-index (structured search)
Find the right bulletin file without guessing filenames.

| Tool | What it does | When to use it |
|------|-------------|----------------|
| `corpus_index__search_files_by_topic` | Find files by topic or keyword | "Which bulletins cover federal debt?" |
| `corpus_index__find_tables` | Find tables by code (FFO-1, FD-3) or name | "Where is Table FD-3 in 1970?" |
| `corpus_index__get_files_for_period` | Get bulletins for a year/month/FY | "What bulletins exist for 1985?" |
| `corpus_index__get_file_info` | Get table listing for a specific file | "What tables are in treasury_bulletin_1970_01.txt?" |

**Topics you can search:** fiscal_operations, federal_debt, public_debt_operations, ownership, treasury_account, international, capital_movements, currency, savings_bonds, exchange_stabilization

### external-data (CPI and exchange rates)
Data that isn't in the Treasury Bulletins but questions sometimes need.

| Tool | What it does | When to use it |
|------|-------------|----------------|
| `external_data__lookup_cpi` | CPI-U value for a year (+ optional month) | "Adjust for inflation" or "in constant dollars" |
| `external_data__lookup_exchange_rate` | Historical exchange rate by currency/year | "Convert to pounds" or "in foreign currency" |
| `external_data__inflation_adjust` | Compute adjusted value between two years | Direct inflation calculation |

**Available currencies:** USD/GBP, USD/DEM (Deutsche Mark), INR/USD, JPY/USD, CAD/USD

### filesystem (raw file access)
Read any file directly.

| Tool | What it does |
|------|-------------|
| `filesystem__read_file` or `filesystem__read_text_file` | Read file contents |
| `filesystem__list_directory` | List directory contents |
| `filesystem__search_files` | Search files by glob pattern |

**Note:** If the filesystem MCP can't access a path, use shell instead: `cat <file>` works everywhere.

## Your Reference Skills

At `~/.config/goose/skills/` you have detailed guides. Read them with `cat` when you need depth:

| Skill | Read it when... |
|-------|----------------|
| `corpus-fieldguide/SKILL.md` | You need the full archive map — every table code, era, naming pattern |
| `doing-the-math/SKILL.md` | You need computation guidance — averages, growth rates, adjustments |
| `reading-carefully/SKILL.md` | You're extracting data from complex multi-header tables |
| `finding-your-way/SKILL.md` | You can't find a file or table and need navigation strategies |
| `external-knowledge/SKILL.md` | You need the full CPI-U table or exchange rate history (also available via MCP tools above) |

## Decision Tree

1. **Parse the question.** What data? What time period? What computation?
2. **Find the file.** Use `corpus_index__get_files_for_period` or `corpus_index__find_tables` — don't guess filenames.
3. **Need external data?** If the question mentions inflation, CPI, constant dollars, or currency conversion — use the `external_data` tools.
4. **Read the file.** Use shell (`cat`, `grep`, `sed`) or `filesystem__read_file` — whichever is faster.
5. **Extract and compute.** Use Python for all math. Check units and column headers.
6. **Write your answer.** A rough answer in `/app/answer.txt` early is better than no answer late.

## Patterns from Previous Agents

- **Revision trap:** Preliminary data gets revised 3-6 months later. If your number looks wrong, check bulletins from later months.
- **Column headers lie:** Multi-header tables are deceptive. Trace the FULL column path: "Parent > Sub > Column."
- **Method ambiguity:** "Average" = arithmetic mean. "Average YoY growth rate" = sum of annual % changes / years. Not CAGR.
- **Best answers came within 10 tool calls.** After that, verify rather than keep searching.
- **The simple reading is right.** When in doubt, take the straightforward interpretation.
