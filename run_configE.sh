#!/bin/bash
# Config E: Kitchen Sink PLUS (parse-first + stop-when-done + MCP corpus index)
set -e
source .env 2>/dev/null || export $(grep -v '^#' .env | xargs)

HARBOR=/home/cat/.arena/venv/bin/harbor

echo "=== Config E: Kitchen Sink PLUS (diverse 20) ==="
echo "Prompt: officeqa_auditor_plus.j2 (parse-first, stop-when-done, speed)"
echo "Skills: 9 Kitchen Sink"
echo "MCP: corpus-index server"
echo "Model: MiniMax M2.5"
echo ""

$HARBOR run -y \
  --job-name "configE-kitchen-plus-diverse20" \
  -a opencode \
  -m "openrouter/minimax/minimax-m2.5" \
  --ak "prompt_template_path=prompts/officeqa_auditor_plus.j2" \
  --ak "skills_dir=skills/" \
  --ak "reasoning_effort=high" \
  --ae "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" \
  -p .arena/samples \
  -t "officeqa-uid0010" -t "officeqa-uid0011" -t "officeqa-uid0012" -t "officeqa-uid0013" \
  -t "officeqa-uid0036" -t "officeqa-uid0037" -t "officeqa-uid0038" -t "officeqa-uid0040" \
  -t "officeqa-uid0045" -t "officeqa-uid0066" -t "officeqa-uid0072" -t "officeqa-uid0078" \
  -t "officeqa-uid0100" -t "officeqa-uid0109" -t "officeqa-uid0113" -t "officeqa-uid0163" \
  -t "officeqa-uid0176" -t "officeqa-uid0197" -t "officeqa-uid0212" -t "officeqa-uid0243"

echo ""
echo "=== Config E Results ==="
pass=0; fail=0
for dir in jobs/configE-kitchen-plus-diverse20/officeqa-uid*; do
    uid=$(basename "$dir" | sed 's/officeqa-\(uid[0-9]*\)__.*/\1/' | tr '[:lower:]' '[:upper:]')
    rf="$dir/verifier/reward.txt"
    if [ -f "$rf" ]; then
        score=$(cat "$rf" | head -1 | tr -d '[:space:]')
        if [ "$score" = "1.0" ] || [ "$score" = "1" ]; then
            echo "PASS $uid"; pass=$((pass+1))
        else
            echo "FAIL $uid"; fail=$((fail+1))
        fi
    fi
done
echo "---"
echo "Config E: $pass/$(($pass+$fail)) = $(echo "scale=0; $pass * 100 / ($pass + $fail)" | bc)%"
