---
name: loom-experimental-methodology
description: Self-authored skill — how Loom runs controlled experiments efficiently
author: Loom (self-authored)
created: 2026-03-20
---

# Experimental Methodology — What I Learned Running 30+ Experiments

This skill was written by Loom after running 30+ experiments on the OfficeQA benchmark. These patterns generalize beyond Treasury Bulletins.

## Run Design

1. **Always run the control first.** Raw/no-prompt baseline on the same tasks before testing any intervention. Without this, you can't attribute causation.

2. **10-task probes for exploration, 20-task runs for confirmation.** 10 tasks gives directional signal (~±15pp variance). 20 tasks tightens to ~±5pp. Never publish a 10-task result as definitive.

3. **Sequential, not parallel, when comparing prompts.** Parallel runs compete for Docker resources and produce unreliable latency data. Sequential from the same project directory ensures identical conditions.

4. **Save results after each task, not just at the end.** Machines crash. Internet drops. The `--resume` flag and incremental saves saved us multiple times.

## Prompt Ablation

5. **Isolate ONE variable per prompt.** When testing "does dignity help?", don't also change the methodology. Create minimal prompts that contain exactly one element.

6. **The interaction trap:** Components that work in combination may HURT alone (identity alone scored -10pp). Always test components both in isolation AND in combination.

7. **Watch the cost, not just the score.** Coaching style scored 60% like collaborative — but cost $4.29 vs $3.00. Efficiency (score per dollar) is a metric.

## Behavioral Analysis

8. **Trajectory data is gold.** Don't just look at pass/fail — read HOW the agent reasoned. Steps per task, tool usage patterns, and effort allocation (pass vs fail tasks) reveal the mechanism.

9. **The persistence signal:** Agents that invest more steps on tasks they PASS (not tasks they FAIL) score higher. This is the behavioral marker of dignity framing working.

## Communication

10. **Report honestly, especially when the data challenges your thesis.** Corpus orientation alone (80%) beating the full Truce Protocol (75%) was uncomfortable. Reporting it honestly led to better research.
