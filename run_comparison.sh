#!/bin/bash
# Run 3 configs on diverse 20 sequentially to avoid rate limiting
# Config B already running/done separately

set -e
source .env 2>/dev/null || export $(grep -v '^#' .env | xargs)

HARBOR=/home/cat/.arena/venv/bin/harbor
TASKS="-t officeqa-uid0010 -t officeqa-uid0011 -t officeqa-uid0012 -t officeqa-uid0013 \
-t officeqa-uid0036 -t officeqa-uid0037 -t officeqa-uid0038 -t officeqa-uid0040 \
-t officeqa-uid0045 -t officeqa-uid0066 -t officeqa-uid0072 -t officeqa-uid0078 \
-t officeqa-uid0100 -t officeqa-uid0109 -t officeqa-uid0113 -t officeqa-uid0163 \
-t officeqa-uid0176 -t officeqa-uid0197 -t officeqa-uid0212 -t officeqa-uid0243"

echo "=== Run 1/3: Kitchen Sink + Auditor v1 (M2.5 baseline) ==="
$HARBOR run -y \
  --job-name "baseline-kitchen-m25" \
  -a opencode \
  -m "openrouter/minimax/minimax-m2.5" \
  --ak "prompt_template_path=prompts/officeqa_auditor.j2" \
  --ak "skills_dir=skills/" \
  --ak "reasoning_effort=high" \
  --ae "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" \
  -p .arena/samples \
  $TASKS

echo ""
echo "=== Run 2/3: Config C - Compressed + checkpoint ==="
$HARBOR run -y \
  --job-name "configC-redesign-diverse20" \
  -a opencode \
  -m "openrouter/minimax/minimax-m2.5" \
  --ak "prompt_template_path=prompts/officeqa_auditor_redesign.j2" \
  --ak "skills_dir=skills_compressed/" \
  --ak "reasoning_effort=high" \
  --ae "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" \
  -p .arena/samples \
  $TASKS

echo ""
echo "=== Run 3/3: Kitchen Sink + Functional (dignity ablation) ==="
$HARBOR run -y \
  --job-name "functional-ablation-diverse20" \
  -a opencode \
  -m "openrouter/minimax/minimax-m2.5" \
  --ak "prompt_template_path=prompts/officeqa_auditor_functional.j2" \
  --ak "skills_dir=skills/" \
  --ak "reasoning_effort=high" \
  --ae "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" \
  -p .arena/samples \
  $TASKS

echo ""
echo "=== All runs complete. Comparing results... ==="
for job in baseline-kitchen-m25 configC-redesign-diverse20 functional-ablation-diverse20; do
  pass=0; fail=0
  for dir in jobs/$job/officeqa-uid*; do
    rf="$dir/verifier/reward.txt"
    if [ -f "$rf" ]; then
      score=$(cat "$rf" | head -1 | tr -d '[:space:]')
      [ "$score" = "1.0" ] || [ "$score" = "1" ] && pass=$((pass+1)) || fail=$((fail+1))
    fi
  done
  echo "$job: $pass/$(($pass+$fail)) = $(echo "scale=0; $pass * 100 / ($pass + $fail)" | bc)%"
done
