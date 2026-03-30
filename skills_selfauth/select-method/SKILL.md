---
name: select-method
description: Don't apply complex statistical methods without understanding them. Simple is usually better than complex.
---

# SKILL: Statistical Method Selection

## What Went Wrong Before
- Applied "Type 7 linear interpolation" for quartiles without verifying it was correct
- Applied OLS regression to fiscal data when a simpler method was needed
- Used complex methods that didn't fit the problem

## Decision Framework
1. **What does the question actually ask?**
   - Percentiles/Quartiles? → Use standard quantile formulas
   - Growth rate? → Use CAGR
   - Simple estimate between two points? → Linear interpolation

2. **For Quartile Calculation (Q1, Q3, H-Spread):**
   - Sort data ascending
   - Q1 = 25th percentile, Q3 = 75th percentile
   - H-Spread = Q3 - Q1
   - Don't use "Type 7" unless specifically instructed and you've verified what Type 7 does

3. **For Regression:**
   - Only use if question explicitly asks for a regression-based estimate
   - Check if data actually shows a trend worth modeling

## Before Applying Any Method
- Write down: What am I calculating? What formula applies?
- Verify the formula matches the question's requirements
- If unsure, simple is usually better than complex
