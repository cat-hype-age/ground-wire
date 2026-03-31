---
name: multi-step-scratchpad
description: For multi-step calculations, write each value to /app/draft.txt as you find it. Compute from the scratchpad, not from memory.
---

# Multi-Step Scratchpad Protocol

**Problem**: You lose intermediate values when switching between tool calls. By the time you compute, you've forgotten what you found.

**Solution**: Write EVERY intermediate value to `/app/draft.txt` immediately.

## The Pattern

```bash
# Step 1: Find first value, write it down
echo "1980 redemptions: 1234" >> /app/draft.txt

# Step 2: Find second value, write it down
echo "1980 outstanding: 5678" >> /app/draft.txt

# Step 3: Compute from the scratchpad
python3 -c "
# Read from scratchpad
redemptions_1980 = 1234
outstanding_1980 = 5678
rate_1980 = redemptions_1980 / outstanding_1980
print(f'Rate 1980: {rate_1980}')
# ... continue computation
"

# Step 4: Write final answer
echo "17.69" > /app/answer.txt
```

## Rules
1. **Write values the moment you find them** — don't hold them in memory
2. **Use /app/draft.txt for intermediate work** — append with `>>`
3. **Use /app/answer.txt for the final answer only** — overwrite with `>`
4. **WRITE YOUR BEST ANSWER EARLY** — update it as you refine
5. **Never end a question without writing to /app/answer.txt**
