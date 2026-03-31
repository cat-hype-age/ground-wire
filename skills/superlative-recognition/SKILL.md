---
name: superlative-recognition
description: When a question asks for highest, lowest, most, or least — scan ALL rows before answering. Don't stop at the first result.
---

# Superlative Questions: Scan First, Answer Second

**Trigger words**: highest, lowest, most, least, largest, smallest, greatest, maximum, minimum, top, bottom, best, worst

## The Failure Pattern

You find a department or category, extract its value, and return it — without checking if another row has a higher/lower value. This happens because you treat superlatives like lookups.

## The Fix

1. **Recognize the superlative** — flag it before you start searching
2. **Extract ALL relevant rows** into a list — don't stop at one
3. **Use Python to find the max/min**:
```python
values = {"Dept A": 1234, "Dept B": 5678, "Dept C": 3456}
max_dept = max(values, key=values.get)
print(f"{max_dept}: {values[max_dept]}")
```
4. **Write the answer** from the computed result, not from what you saw first

## Quick Check

If you're answering a superlative question and you only read ONE row — you're doing it wrong. Go back and read the full table.
