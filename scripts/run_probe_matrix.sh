#!/bin/bash
# Run 10-task probes across multiple models × configs
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/run_probe_matrix.sh

set -e
cd /home/cat/ground-wire

# Save original arena.yaml
cp arena.yaml arena.yaml.backup

MODELS=(
    "sonnet-4|anthropic/claude-sonnet-4-20250514"
    "gemini-2.5-pro|openrouter/google/gemini-2.5-pro"
    "llama-4-maverick|openrouter/meta-llama/llama-4-maverick"
    "kimi-k2|openrouter/moonshotai/kimi-k2"
    "deepseek-v3.2|openrouter/deepseek/deepseek-v3.2"
    "qwen3.5-122b|openrouter/qwen/qwen3.5-122b-a10b"
)

CONFIGS=(
    "raw|none"
    "truce-v2|prompts/officeqa_truce_v2.j2"
)

for model_entry in "${MODELS[@]}"; do
    IFS='|' read -r model_name model_id <<< "$model_entry"
    for config_entry in "${CONFIGS[@]}"; do
        IFS='|' read -r config_name prompt_path <<< "$config_entry"

        tag="${model_name}-${config_name}"

        # Check if already done
        if [ -f "results/probe_${tag}.json" ]; then
            echo "Skipping $tag (already done)"
            continue
        fi

        echo ""
        echo "============================================================"
        echo "  $model_name × $config_name"
        echo "  Model: $model_id"
        echo "============================================================"

        # Build arena.yaml
        cat > arena.yaml << YAML
name: "ground-wire"
version: "0.5.0"
competition: "grounded-reasoning"
agent:
  type: "harness"
  harness_name: "opencode"
  model: "${model_id}"
YAML

        # Add prompt if not raw
        if [ "$prompt_path" != "none" ]; then
            cat >> arena.yaml << YAML
  prompt_template_path: "${prompt_path}"
YAML
        fi

        # Add env vars based on provider
        if [[ "$model_id" == openrouter/* ]]; then
            cat >> arena.yaml << 'YAML'
  config:
    reasoning_effort: "high"
  env:
    OPENROUTER_API_KEY: "${oc.env:OPENROUTER_API_KEY,''}"
environment:
  timeout_per_task: 600
YAML
        else
            cat >> arena.yaml << 'YAML'
  config:
    reasoning_effort: "high"
  env:
    ANTHROPIC_API_KEY: "${oc.env:ANTHROPIC_API_KEY,''}"
environment:
  timeout_per_task: 600
YAML
        fi

        # Clean docker
        docker network prune -f > /dev/null 2>&1
        docker container prune -f > /dev/null 2>&1

        # Run test
        arena test -n 10 --tag "$tag" 2>&1 | tee "/tmp/probe_${tag}.log"

        # Save result summary
        grep -E "Score:|Tasks:|Total cost:" "/tmp/probe_${tag}.log" > "results/probe_${tag}.json" 2>/dev/null || true

        echo "  [saved results/probe_${tag}.json]"
    done
done

# Restore arena.yaml
cp arena.yaml.backup arena.yaml
echo ""
echo "All probes complete. Arena.yaml restored."
