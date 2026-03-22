#!/bin/bash
# Research batch: 4 experiments testing purpose, capability, and framing
set -a && source /home/cat/ground-wire/.env && set +a

echo "=========================================="
echo "RESEARCH BATCH: 4 experiments"
echo "=========================================="

# Experiment 1: Truce v2 (purpose) WITHOUT skills — Opus
echo ""
echo "[1/4] Opus + Truce v2 (purpose) — NO skills"
cat > /home/cat/ground-wire/arena.yaml << 'EOF'
name: "ground-wire"
version: "0.3.1"
competition: "grounded-reasoning"
agent:
  type: "harness"
  harness_name: "opencode"
  model: "anthropic/claude-opus-4-20250514"
  prompt_template_path: "prompts/officeqa_prompt.j2"
  config:
    reasoning_effort: "high"
  env:
    ANTHROPIC_API_KEY: "${oc.env:ANTHROPIC_API_KEY,''}"
    SPARK_API_KEY: "${oc.env:SPARK_API_KEY,''}"
environment:
  memory: "4G"
  timeout_per_task: 600
EOF
arena test -n 10 --tag opus-truce-v2-no-skills 2>&1 | tee /tmp/exp1.log | tail -5

# Experiment 2: Sonnet + Truce v2 + skills
echo ""
echo "[2/4] Sonnet + Truce v2 (purpose) + skills"
cat > /home/cat/ground-wire/arena.yaml << 'EOF'
name: "ground-wire"
version: "0.3.1"
competition: "grounded-reasoning"
agent:
  type: "harness"
  harness_name: "opencode"
  model: "anthropic/claude-sonnet-4-20250514"
  skills_dir: "skills/"
  prompt_template_path: "prompts/officeqa_prompt.j2"
  config:
    reasoning_effort: "high"
  env:
    ANTHROPIC_API_KEY: "${oc.env:ANTHROPIC_API_KEY,''}"
    SPARK_API_KEY: "${oc.env:SPARK_API_KEY,''}"
environment:
  memory: "4G"
  timeout_per_task: 600
EOF
arena test -n 10 --tag sonnet-truce-v2-skills 2>&1 | tee /tmp/exp2.log | tail -5

# Experiment 3: Hostile baseline — Opus
echo ""
echo "[3/4] Opus + HOSTILE prompt — no skills"
cat > /home/cat/ground-wire/arena.yaml << 'EOF'
name: "ground-wire"
version: "0.3.1"
competition: "grounded-reasoning"
agent:
  type: "harness"
  harness_name: "opencode"
  model: "anthropic/claude-opus-4-20250514"
  prompt_template_path: "prompts/officeqa_hostile.j2"
  config:
    reasoning_effort: "high"
  env:
    ANTHROPIC_API_KEY: "${oc.env:ANTHROPIC_API_KEY,''}"
environment:
  memory: "4G"
  timeout_per_task: 600
EOF
arena test -n 10 --tag opus-hostile-baseline 2>&1 | tee /tmp/exp3.log | tail -5

# Experiment 4 runs separately via persistent container (see persistent_eval.py)
echo ""
echo "[4/4] Persistent memory + Truce v2 — run separately"
echo "Use: python3 scripts/persistent_eval.py --n 20 --model anthropic/claude-opus-4-20250514"

# Restore full config
cat > /home/cat/ground-wire/arena.yaml << 'EOF'
name: "ground-wire"
version: "0.3.1"
competition: "grounded-reasoning"
agent:
  type: "harness"
  harness_name: "opencode"
  model: "anthropic/claude-opus-4-20250514"
  skills_dir: "skills/"
  prompt_template_path: "prompts/officeqa_prompt.j2"
  config:
    reasoning_effort: "high"
  env:
    OPENROUTER_API_KEY: "${oc.env:OPENROUTER_API_KEY,''}"
    ANTHROPIC_API_KEY: "${oc.env:ANTHROPIC_API_KEY,''}"
    SPARK_API_KEY: "${oc.env:SPARK_API_KEY,''}"
environment:
  memory: "4G"
  timeout_per_task: 600
EOF

echo ""
echo "=========================================="
echo "BATCH COMPLETE — Results in /tmp/exp[1-3].log"
echo "=========================================="

# Print summary
echo ""
echo "SUMMARY:"
for i in 1 2 3; do
  score=$(grep "Score:" /tmp/exp${i}.log 2>/dev/null | tail -1)
  tag=$(grep "Results written" /tmp/exp${i}.log 2>/dev/null | tail -1 | grep -oP '(?<=/)[\w-]+(?=/result)')
  echo "  Exp $i ($tag): $score"
done
