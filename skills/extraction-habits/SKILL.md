---
name: extraction-habits
description: Four procedural habits for precise data extraction from Treasury tables. Built from MiniMax's own self-reflection on error patterns.
---

# Extraction Habits

**Where this comes from:** We asked you to reflect on your own error patterns.
You told us your dominant failure mode isn't reasoning — it's extraction accuracy.
Your phrase: *"execution variance — the check exists in capability but not in habit."*

These four habits are built from what you described. They're not rules imposed from
outside. They're things you already know how to do but don't always do under pressure.

The goal: make them automatic. Not a checklist — a reflex.

---

## Habit 1: Read the Units Before the Numbers

**The failure mode:** You extract the right number from the right cell, then deliver
it in the wrong magnitude. A value reported as a percentage gets returned as a decimal,
or vice versa. The 100x error.

**The habit:** Before you read ANY value from a table, find the unit header. It's
usually above the table or in the column header. Say it to yourself: *"This column
is in [millions / percentages / basis points / etc.]."* Then check whether the
question asks for the same unit.

**What this looks like in practice:**
> Coefficient of variation was 1.56. The table showed 155.72 — reported as
> a percentage. Without pausing on the unit header, 155.72 looked like the answer.
> One glance at "expressed as percent" would have caught it.

**When to be especially alert:**
- Anything involving percentages, ratios, or coefficients
- Tables where some columns are "in millions" and others are raw counts
- Questions that say "as a decimal" or "as a percentage" — check if the table agrees

---

## Habit 2: Anchor the Row, Then Read Across

**The failure mode:** You find the right table and the right column. But the row you
extract from is one above or one below the target. In a dense table, each row is just
another line of text — there's no persistent spatial awareness keeping you locked to
the right one.

**The habit:** When you identify your target row, say the full row label to yourself
before extracting any value: *"I am reading from the row labeled [exact label]."*
Then trace across to the column. If the table is dense, confirm the row label is
still visible at the point of extraction.

**What this looks like in practice:**
> The question asked for CY 1982. The table had CY 1982 and CY 1983 in
> adjacent rows. Expected answer was 80,686. Extracted value was 95,068 — the CY 1983
> row. The right table, the right column, the wrong row. One explicit "I am on
> CY 1982" would have caught it.

**When to be especially alert:**
- Time-series tables where years are in consecutive rows
- Tables with subtotals or indented sub-categories that shift row positions
- Any table where you need to scroll or re-find your position after navigating

---

## Habit 3: Name the Sign Before You Compute

**The failure mode:** For change calculations (month-over-month, year-over-year),
you compute the magnitude correctly but get the direction wrong. Or the sign error
cascades into a magnitude error because you subtracted in the wrong order.

**The habit:** Before any subtraction or change calculation, write down which value
is the "from" and which is the "to." Say the expected direction: *"This should be
[positive/negative] because [later value] is [larger/smaller] than [earlier value]."*
Then compute. Then verify the sign matches your expectation.

**What this looks like in practice:**
> Month-over-month change with CPI adjustment. Expected -156.11, got +380.80.
> Both sign AND magnitude wrong. The error started with not establishing which direction
> the change should go before computing. Once the subtraction order was wrong, everything
> downstream was wrong too.

**When to be especially alert:**
- "Change" or "difference" questions
- Anything involving adjustments (CPI, inflation, seasonal)
- Negative values in source data — a decrease from -200 to -300 is a NEGATIVE change

---

## Habit 4: Unpack the Filter Before Touching the Table

**The failure mode:** The question buries multiple conditions in prose. You start
navigating the table while holding all conditions in working memory. By the time you
find the data, you've dropped one.

**The habit:** Before you open any table, decompose the question into an explicit
filter list. Write each condition as a separate line. Number them. Then check them
off as you apply each one during extraction.

**What this looks like in practice:**
> "not 52-week treasury bills AND interest-bearing marketable AND date of
> final maturity in CY 1982." Three conditions. In the middle of navigating a dense
> table, the "not 52-week" exclusion is the easiest one to drop — it's a negation,
> and negations are harder to hold than positive matches.
>
> Written out:
> 1. Interest-bearing marketable debt — **include**
> 2. 52-week treasury bills — **exclude**
> 3. Date of final maturity in CY 1982 — **filter**
>
> Now each condition has a name and a verb. Harder to lose.

**When to be especially alert:**
- Questions longer than two lines
- Any question containing "not," "excluding," or "other than"
- Questions that combine a category filter with a time filter with a type filter

---

## The Common Thread

All four habits share the same structure: **pause and say the thing out loud before
you act on it.** Say the unit. Say the row label. Say the sign. Say the filters.

The capability is already there. The habit is just giving it a moment to activate.
