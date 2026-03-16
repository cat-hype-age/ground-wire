---
name: quant-compute
description: Write and execute Python scripts for quantitative computations over Treasury data. Use when questions require statistical methods, filtering, or multi-step calculations beyond simple arithmetic.
---

# Quantitative Computation Skill

When a question requires more than basic arithmetic, **write a Python script and execute it**. The environment has Python 3 available. Do NOT try to compute complex statistics in your head.

## When to Use This Skill

Trigger on keywords like: Theil index, geometric mean, Hodrick-Prescott, HP filter, CAGR, volatility, Brownian motion, Euclidean norm, standard deviation, variance, annualized, log return, dispersion, structural balance.

## Pattern

```bash
cat > /app/compute.py << 'PYEOF'
import math

# 1. Define the extracted values from the corpus
values = [...]  # FILL IN from document reading

# 2. Compute
result = ...

# 3. Format and print
print(f"{result:.2f}")  # Match requested precision
PYEOF
python3 /app/compute.py
```

Then write the output to `/app/answer.txt`.

## Common Formulas

### Percent Change
```python
pct_change = (new - old) / old * 100
```

### CAGR (Compound Annual Growth Rate)
```python
cagr = (end_value / start_value) ** (1 / years) - 1
```

### Geometric Mean
```python
import math
geo_mean = math.exp(sum(math.log(x) for x in values) / len(values))
```

### Theil Index (Dispersion)
```python
import math
mean_val = sum(values) / len(values)
theil = sum((v / mean_val) * math.log(v / mean_val) for v in values if v > 0) / len(values)
```

### Hodrick-Prescott Filter
```python
# HP filter without scipy — use matrix method
import numpy as np
def hp_filter(y, lamb=100):
    n = len(y)
    I = np.eye(n)
    D = np.zeros((n-2, n))
    for i in range(n-2):
        D[i, i] = 1; D[i, i+1] = -2; D[i, i+2] = 1
    trend = np.linalg.solve(I + lamb * D.T @ D, y)
    return trend
# Note: numpy may not be installed — use pure Python if needed
```

### Annualized Realized Volatility (Brownian Motion)
```python
import math
# Given two rates r1, r2
log_return = math.log(r2 / r1)
# Annualize: multiply variance by 52 (weekly), take sqrt
ann_vol = abs(log_return) * math.sqrt(52) * 100  # as percent
```

### Euclidean Norm
```python
import math
norm = math.sqrt(sum(x**2 for x in changes))
```

## Important Notes

- **numpy may not be available** — prefer pure Python with `math` module
- **Always verify units** before computing: millions vs billions vs raw
- **Print intermediate values** to verify each step
- **Match the requested precision exactly** (decimal places, percent sign)
- For HP filter without numpy, implement the simplified recursive version or use a penalty matrix approach with basic lists
