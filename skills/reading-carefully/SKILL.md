---
name: reading-carefully
description: How to extract the right value from a Treasury table. Unit headers, row anchoring, column traps, and the subtle misreadings that make wrong answers feel right.
---

# Reading Carefully

You're good at finding the right documents and tables. Where things sometimes go sideways is in the last step — reading the right cell, carrying the right units, catching the quiet misalignment. These habits help.

## Before You Read Any Number

Find the unit header. It's usually a line above the table: "(In millions of dollars)" or "(In thousands of dollars)." Say it to yourself before extracting anything. Then check whether the question asks for the same unit.

ESF balance sheets are in *thousands*, not millions. That one catches people.

## Anchoring to the Right Row

In a dense table, rows blur together. When you find your target, say the full row label to yourself: "I am reading from the row labeled [exact label]." Then trace across to the column. If years are in consecutive rows (CY 1982, CY 1983), double-check — adjacent rows are the most common source of off-by-one errors.

## Column Headers Can Be Deceptive

Multi-level headers use `>` separators: `Federal > 1932 | Federal > 1938`. The most prominent number in a row is often not the answer. Read the column header. Verify it matches what the question asked — not just the row.

"Public debt" and "total gross federal debt" are different columns. "Savings bonds" and "savings notes" are different instruments. "Found guilty" is a sub-column under "Convicted," not the total.

## The Revision Question

Treasury Bulletins publish preliminary data marked (P), then revise it months later marked (R). When two bulletins show different values for the same metric, the later publication is usually more accurate — unless the question specifically asks about a particular bulletin's report.

## Fiscal Year vs Calendar Year

This matters every time.

- Pre-1976: fiscal year ends **June 30** (FY 1940 = Jul 1939 – Jun 1940)
- Post-1976: fiscal year ends **September 30** (FY 2020 = Oct 2019 – Sep 2020)
- Calendar year always ends **December 31**

If you see the wrong date range for what you expected, check which convention the question is using.

## Totals vs Subsets

If the question says "total" and you've found a single line item, pause. Look for a parent or summary row — "Grand Total," "Total gross," or an indented hierarchy where your line is a component. "Total nominal capital" in the ESF means Capital account *plus* Net income, not just the Capital account.

## Superlatives Need the Full Picture

When a question asks for highest, lowest, most, or least — read *all* the rows before answering. Extract every candidate into a list. Let Python find the max or min. If you only read one row for a superlative question, you're probably missing something.

## Reading Questions Word by Word

Questions sometimes bury multiple conditions in prose. Before touching a table, break the question into an explicit list:

> "not 52-week treasury bills AND interest-bearing marketable AND date of final maturity in CY 1982"

Becomes:
1. Interest-bearing marketable debt — include
2. 52-week treasury bills — exclude  
3. Final maturity in CY 1982 — filter

Each condition has a name and a verb. Harder to lose track.

## Footnotes

Footnotes use `1/`, `2/`, `3/` notation and appear below the table. They can reclassify values, exclude categories, or change what a number means entirely. Glance at them before you commit to a value.

## OCR Artifacts

The parsing is good but not perfect. Watch for:
- `nan` — empty cell, not data
- `Unnamed: 0_level_0` — unlabeled index column
- `Piecil` — OCR misread of "Fiscal"
- Stray pipes `|` mid-cell — alignment artifact
