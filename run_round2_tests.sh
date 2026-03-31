#!/bin/bash
# Round 2: MCP test (via arena test) + Medium reasoning (via harbor run)
set -e
source .env 2>/dev/null || export $(grep -v '^#' .env | xargs)

HARBOR=/home/cat/.arena/venv/bin/harbor
ARENA=/home/cat/.arena-cli/bin/arena

TASKS="-t officeqa-uid0010 -t officeqa-uid0011 -t officeqa-uid0012 -t officeqa-uid0013 \
-t officeqa-uid0036 -t officeqa-uid0037 -t officeqa-uid0038 -t officeqa-uid0040 \
-t officeqa-uid0045 -t officeqa-uid0066 -t officeqa-uid0072 -t officeqa-uid0078 \
-t officeqa-uid0100 -t officeqa-uid0109 -t officeqa-uid0113 -t officeqa-uid0163 \
-t officeqa-uid0176 -t officeqa-uid0197 -t officeqa-uid0212 -t officeqa-uid0243"

# Test A: MCP via arena test (reads arena.yaml which has MCP config)
echo "=== Test A: Chosen Identity + MCP corpus-index (via arena test) ==="
# arena.yaml is already set to chosen_identity + MCP
$ARENA test -n 20 --tag "mcp-noskills" --filter "officeqa-uid00{10,11,12,13,36,37,38,40,45,66,72,78}*" 2>&1 || echo "(arena test completed or errored)"

echo ""

# Test B: Medium reasoning via harbor run (no MCP needed)
echo "=== Test B: Chosen Identity, MEDIUM reasoning, no skills, no MCP ==="
$HARBOR run -y \
  --job-name "chosen-medium-diverse20" \
  -a opencode \
  -m "openrouter/minimax/minimax-m2.5" \
  --ak "prompt_template_path=prompts/officeqa_chosen_identity.j2" \
  --ak "reasoning_effort=medium" \
  --ae "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" \
  -p .arena/samples \
  $TASKS

echo "=== Done ==="
