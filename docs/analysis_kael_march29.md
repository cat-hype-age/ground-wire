# Kael's Error Analysis — March 29, 2026

## Five Kill Patterns

### 1. Revision-Chasing Failure
The prompt warns about preliminary vs revised data, but MiniMax reads the instruction without executing it. "May have used preliminary instead of revised data" appears in 27 of 42 moderate errors.

### 2. Fiscal vs Calendar Year Confusion
Appears in 20+ error hypotheses. MiniMax knows the rule but doesn't apply it consistently.

### 3. Unit Multiplier Chaos
9 unit/magnitude errors, mostly percentage-vs-decimal or millions-vs-thousands:
- UID0049: Expected 1.56, got 155.72 (100x error)
- UID0096: Expected 0.388, got 37.708 (100x error)
- UID0237: Expected 0.03, got 2.98 (100x error)
The model isn't sanity-checking outputs.

### 4. Column/Row Extraction Precision
Moderate errors show MiniMax finds the RIGHT table but extracts the WRONG cell. Visual reasoning or table parsing is weaker than Opus.

### 5. Sign Errors
- UID0132: Expected +73985, got -73547
- UID0150: Expected -18.39, got +18.32
- UID0196: Expected -156.11, got +380.80
Not reading deficit vs surplus context.

## Research Recommendations

### Priority 1: Model-Specific Tuning
- A/B test prompt density (shorter, more imperative?)
- Add explicit worked examples for revision-chasing
- Add unit sanity checks in prompt

### Priority 2: Close Miss Recovery (28 questions within 10%)
- Aggressive rounding instructions
- Revision-chase escalation (6, 9, 12 months after)
- Final-pass re-read verification

### Priority 3: Structured Output Enforcement
- Explicit output format examples for lists
- Formatting validator step

### Priority 4: Fallback for Timeouts
- "Write best guess at step 80%" instruction
- Shorter search strategies

### Priority 5: Hard Question Decomposition
- Step-by-step decomposition prompts
- Route hard questions to reasoning model for calculation

## Meta-Question
Why did MiniMax drop 18 points from Opus? Two possibilities:
1. MiniMax is just worse at grounded reasoning
2. The prompt was overfit to Opus
Test: run exact same prompt on both Opus and MiniMax for 20 representative questions.

## Projected Recovery
If we fix close misses (28), format errors (1), and half of moderate errors (21): 65.6% → ~86%.
