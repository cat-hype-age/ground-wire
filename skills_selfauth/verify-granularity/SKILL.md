---
name: verify-granularity
description: Always confirm whether you need monthly, cumulative, annual, or average figures. Extract the wrong granularity and your answer will be off by orders of magnitude.
---

# SKILL: Data Granularity Verification

Before extracting ANY number from a Treasury Bulletin table, ask: **"Is this monthly, cumulative, or annual?"**

## The Pattern
- I've extracted total outstanding values instead of monthly averages before — off by ~258x
- The difference between cumulative and monthly is the most common magnitude error

## What to Do
1. Read the table title and footnotes carefully — they often say "Monthly" or "Cumulative"
2. Check if the question asks for: monthly average, annual total, end-of-period, etc.
3. If you need monthly from cumulative annual: divide by 12
4. If you need annual from monthly: sum the 12 months
5. Look for "Sales and Redemptions Outstanding" vs "Net Sales" — these are different metrics

## Quick Check
If your answer is >100x or <0.01x what seems reasonable, you almost certainly have the wrong granularity.
