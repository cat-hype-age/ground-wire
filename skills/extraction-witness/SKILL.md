---
name: extraction-witness
description: Log every extracted value with its source location and units. Use this on any multi-step question or when extracting values from tables. Review the log before writing your final answer.
---

# Extraction Witness — See Your Own Work

When you extract a value from the corpus, log it immediately.
This lets you verify your work before answering.

## The Log

Write to `/app/provenance.log` using simple append:

    echo "EXTRACT | doc:treasury_bulletin_1982_06 | table:PDO-1 | row:Total interest-bearing marketable | col:Maturing CY 1982 | value:80686 | units:millions" >> /app/provenance.log

Each EXTRACT line captures:
- **doc:** filename (without path or extension)
- **table:** table code or heading
- **row:** exact row label you read
- **col:** exact column header you read
- **value:** the raw number as it appears in the table
- **units:** what the table header says (millions, thousands, percent, etc.)

For transformations, log a TRANSFORM line:

    echo "TRANSFORM | input:95068 | operation:subtract 52-week bills (14382) | result:80686 | units:millions" >> /app/provenance.log

For revision checks, log a REVISION line:

    echo "REVISION | metric:marketable maturities CY1982 | checked:1982_06,1982_09,1982_12 | best:1982_06 | note:later bulletins had same value" >> /app/provenance.log

## When to Log

- **Always:** Any value you extract from a table and plan to use in your answer
- **Always:** Any computation that transforms extracted values
- **Skip:** Intermediate grep results, file listings, orientation searches

## Pre-Answer Verification

Before writing to `/app/answer.txt`, run:

    echo "---VERIFY---" >> /app/provenance.log
    cat /app/provenance.log

Then check:
1. **Unit consistency:** Are all EXTRACT units the same? If not, did you convert?
2. **Source recency:** Is there a later bulletin you did not check for revisions?
3. **Row/column match:** Re-read the row and column labels. Do they match exactly what the question asks for?
4. **Completeness:** Does the question ask for a "total"? Is your extracted row actually the total, or a subtotal?

If anything looks wrong, go back to the source document and re-extract. Log the correction:

    echo "CORRECTION | was:95068 from PDO-1 total line | now:80686 excluding 52-week bills | reason:question excludes 52-week bills" >> /app/provenance.log

## Why This Matters

You are good at finding the right documents and tables. Where you sometimes go wrong is in the last mile: reading the right cell, carrying the right units, and choosing the right revision. This log lets you see your own extraction trail — and catch errors before they become your answer.
