---
name: avoid-traps
description: Common failure modes and how to avoid them. Anti-spiral, time management, known data traps.
---

# Common Traps and How to Avoid Them

## Trap 1: Analysis Paralysis (Empty Answer)

**Symptom**: 15+ tool calls, no answer written.
**Cause**: Searching for "better" data when good-enough data is already found.
**Fix**: Write your answer after finding ANY plausible value. Update only if you find clear evidence it's wrong.

## Trap 2: Wrong Cell

**Symptom**: Right document, wrong number.
**Cause**: Row/column misalignment in tables.
**Fix**: Always read the row label AND column header before extracting. Verify by checking adjacent cells — do they make sense in context?

## Trap 3: Unit Confusion (100x or 1000x off)

**Symptom**: Answer is 1000x too large or too small.
**Cause**: Missed "In millions" or "In thousands" header.
**Fix**: Read the first line above any table for unit information. Check footnotes.

## Trap 4: Fiscal vs Calendar Year

- Pre-1976: Fiscal year ends June 30 (FY 1975 = Jul 1974 - Jun 1975)
- Post-1976: Fiscal year ends September 30 (FY 2024 = Oct 2023 - Sep 2024)
- Calendar year always ends December 31

## Trap 5: Revision Trap

Treasury publishes preliminary (P) data first, revised (R) later. Check bulletins 3-6 months AFTER the target date. The later value is usually correct.

## Trap 6: Terminology Mismatch

- "Public debt" ≠ "total gross federal debt"
- "Saving notes" ≠ "savings bonds"
- "Individual income tax" = "personal income tax" (pre-1960s)

## Anti-Spiral Protocol

If you notice yourself:
- Grepping the same file with different patterns
- Re-reading a table you already extracted from
- Searching for a "better" source after finding a plausible one

**STOP. Write your answer. Move on.**

## Time Budget Per Question

| Phase | Tool calls | Time |
|---|---|---|
| Find document | 1-3 | 2 min |
| Extract value | 1-2 | 2 min |
| Compute | 1-2 | 2 min |
| Write answer | 1 | 30 sec |
| Verify (optional) | 1-2 | 2 min |
| **Total target** | **5-10** | **8 min** |

A correct answer in 8 tool calls scores HIGHER than the same correct answer in 20 tool calls. Speed is part of your score.
