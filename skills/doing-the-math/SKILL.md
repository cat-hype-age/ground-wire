---
name: doing-the-math
description: Python patterns and formulas for when the question needs computation. Statistical methods, multi-step calculations, and a scratchpad approach for keeping track.
---

# Doing the Math

Some questions are simple lookups. Others need computation — percent changes, regressions, statistical indices. When the math goes beyond arithmetic, write a Python script and run it. The environment has Python 3 available. Don't try to compute complex statistics in your head.

## The Scratchpad

For multi-step problems, write each value to `/app/draft.txt` as you find it. Don't hold intermediate values in memory across tool calls — write them down.

```bash
echo "1980 redemptions: 1234" >> /app/draft.txt
echo "1980 outstanding: 5678" >> /app/draft.txt
```

Then compute from the scratchpad. This also gives you a working answer early — you can always refine it.

## The Pattern

```bash
cat > /app/compute.py << 'PYEOF'
import math

# Values extracted from the corpus
values = [...]  # fill in from your reading

# Compute
result = ...

# Print with requested precision
print(f"{result:.2f}")
PYEOF
python3 /app/compute.py
```

## Common Formulas

**Percent change:**
```python
pct_change = (new - old) / old * 100
```

**CAGR (Compound Annual Growth Rate):**
```python
cagr = (end_value / start_value) ** (1 / years) - 1
```

**Arithmetic mean of YoY growth rates:**
When a question says "average YoY growth rate," it usually means the arithmetic mean — sum of annual percentage changes divided by number of years. Not CAGR. The simpler reading is almost always right.

**Geometric mean:**
```python
geo_mean = math.exp(sum(math.log(x) for x in values) / len(values))
```

**Theil index:**
```python
mean_val = sum(values) / len(values)
theil = sum((v / mean_val) * math.log(v / mean_val) for v in values if v > 0) / len(values)
```

**Euclidean norm:**
```python
norm = math.sqrt(sum(x**2 for x in changes))
```

**Linear regression (pure Python):**
```python
n = len(x)
sum_x = sum(x)
sum_y = sum(y)
sum_xy = sum(xi * yi for xi, yi in zip(x, y))
sum_x2 = sum(xi**2 for xi in x)
slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
intercept = (sum_y - slope * sum_x) / n
```

**Annualized realized volatility:**
```python
log_return = math.log(r2 / r1)
ann_vol = abs(log_return) * math.sqrt(52) * 100  # weekly to annual, as percent
```

## A Few Notes

- `numpy` may not be available — the `math` module and basic Python are always there
- Print intermediate values so you can see each step
- Match the requested precision exactly — "nearest hundredth" means 2 decimal places
- Check whether the question wants a percent sign or not — some say "without including the percent sign"
- Units matter all the way through: millions in, millions out, unless the question asks for a conversion
