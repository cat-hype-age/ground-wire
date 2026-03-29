# Gemini's Error Analysis — March 29, 2026

## 1. The "Close Miss" Crisis (32.9% of Failures)
28 failures within 10%, many within 5%. Screams "rounding vs raw data" conflicts.

**Fix: "Printed Total" vs "Calculated Sum" Rule**
Historical treasury tables have rounding differences. Need to determine: does OfficeQA want raw sum of extracted rows, or the printed total at the bottom?
Prompt addition: "If calculating a sum, prioritize the printed total in the document over your own Python summation if they differ by less than 2% due to historical rounding."

## 2. Moderate Errors: The "Wrong Row" Trap (49.4%)
42 failures. Agent finds right table, wrong data point.

**Fix: Hierarchical Table Parsing**
Treasury tables use indentation for parent/child. Agent does flat text search.
Prompt addition: "Before extracting a value, identify if the row is a parent category or sub-category by looking at indentation. Never extract a sub-category when asked for a 'Total'."
**Signage:** Look for parentheses `()` or asterisks indicating negative flows/deficits, common in 1970s Treasury accounting.

## 3. Unit/Magnitude Errors (10.6%)
9 failures, mostly percentage-vs-decimal or 100x errors.

**Fix: Mandatory Sanity Check Step**
Prompt addition: "If the prompt asks for a percentage, ensure your final Python output is scaled correctly (e.g., 0.05 vs 5.0). If the table header says 'In Thousands', multiply your extracted raw variable by 1,000 in Python before doing any other math."

## 4. Hard Questions (45.1% fail rate vs 22.1% easy)
Multi-document problems like CPI adjustment.

**Fix: Multi-Document Indexing + Skills**
Provide `skills/inflation_adjustment.md` with exact CPI formula. Don't assume the LLM remembers the formula — give it copy-paste Python.

## Immediate Next Steps
1. **Format fix** (UID0057): Add "If asked for a list, you MUST enclose values in square brackets []" — free point
2. **Review close miss precision**: Does the evaluator truncate or round?
3. **Cross-reference Kael's model-capability question**: Run same prompt on Opus + MiniMax

## Key Insight
"The path to the top of the leaderboard isn't about making the agent smarter — it's about giving it better procedural guardrails."
