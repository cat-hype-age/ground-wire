#!/bin/bash
# Batch evaluation — swap arena samples in groups, run arena test --all
# Tests the full 246 questions by cycling through batches
#
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/batch_eval.sh
#
# Optional: BATCH_SIZE=10 bash scripts/batch_eval.sh

set -e
cd /home/cat/ground-wire

SAMPLES_DIR=".arena/samples"
BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/full_eval"
SPLIT_DIR="/tmp/arena-batch-splits"
LOG_DIR="/tmp/arena-batch-logs"
BATCH_SIZE="${BATCH_SIZE:-5}"
RESULTS_JSON="$RESULTS_DIR/batch_full_246.json"

# Resume support — skip batches that already have results
RESUME="${RESUME:-true}"

mkdir -p "$RESULTS_DIR" "$LOG_DIR"

echo "=== BATCH EVAL: Full 246-question OfficeQA ==="
echo "  Batch size: $BATCH_SIZE"
echo "  Resume: $RESUME"

# Backup samples if not already backed up
if [ ! -d "$BACKUP_DIR" ]; then
    cp -r "$SAMPLES_DIR" "$BACKUP_DIR"
    echo "  Samples backed up to $BACKUP_DIR"
else
    echo "  Using existing backup at $BACKUP_DIR"
fi

# Collect ALL sample UIDs from backup
ALL_UIDS=$(ls "$BACKUP_DIR" | grep "^officeqa-" | sort)
TOTAL=$(echo "$ALL_UIDS" | wc -l)
echo "  Total samples: $TOTAL"

# Split into batch files (use unique prefix to avoid collisions)
rm -rf "$SPLIT_DIR"
mkdir -p "$SPLIT_DIR"
echo "$ALL_UIDS" | split -l "$BATCH_SIZE" - "$SPLIT_DIR/chunk_"

NUM_BATCHES=$(ls "$SPLIT_DIR"/chunk_* | wc -l)
echo "  Batches: $NUM_BATCHES (of $BATCH_SIZE each)"
echo ""

BATCH_NUM=0
TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_ERROR=0
TOTAL_COST=0

for batch_file in "$SPLIT_DIR"/chunk_*; do
    BATCH_NUM=$((BATCH_NUM + 1))
    BATCH_UIDS=$(cat "$batch_file")
    BATCH_COUNT=$(echo "$BATCH_UIDS" | wc -l)
    TAG="full246-b${BATCH_NUM}"

    echo "=========================================="
    echo "  BATCH $BATCH_NUM / $NUM_BATCHES ($BATCH_COUNT tasks)"
    echo "=========================================="

    # Resume: check if this batch already has results
    BATCH_RESULT_FILE="$RESULTS_DIR/${TAG}.json"
    if [ "$RESUME" = "true" ] && [ -f "$BATCH_RESULT_FILE" ]; then
        B_PASS=$(python3 -c "import json; d=json.load(open('$BATCH_RESULT_FILE')); print(d.get('passed',0))" 2>/dev/null || echo 0)
        B_FAIL=$(python3 -c "import json; d=json.load(open('$BATCH_RESULT_FILE')); print(d.get('failed',0))" 2>/dev/null || echo 0)
        echo "  SKIPPING (already completed: $B_PASS pass, $B_FAIL fail)"
        TOTAL_PASS=$((TOTAL_PASS + B_PASS))
        TOTAL_FAIL=$((TOTAL_FAIL + B_FAIL))
        echo ""
        continue
    fi

    # Clear samples dir and populate with this batch only
    rm -rf "$SAMPLES_DIR"/*
    cp "$BACKUP_DIR/manifest.json" "$SAMPLES_DIR/" 2>/dev/null || echo '{"version":"batch"}' > "$SAMPLES_DIR/manifest.json"

    for uid in $BATCH_UIDS; do
        if [ -d "$BACKUP_DIR/$uid" ]; then
            cp -r "$BACKUP_DIR/$uid" "$SAMPLES_DIR/$uid"
        fi
    done

    LOADED=$(ls "$SAMPLES_DIR" | grep -c officeqa || echo 0)
    echo "  Loaded $LOADED tasks into samples dir"

    # Clean Docker between batches
    docker network prune -f > /dev/null 2>&1
    docker container prune -f > /dev/null 2>&1

    # Run arena test
    echo "  Running: arena test --all --tag $TAG"
    arena test --all --tag "$TAG" 2>&1 | tee "$LOG_DIR/${TAG}.log"

    # Extract results from log — use python for reliable parsing
    eval "$(python3 -c "
import re
log = open('$LOG_DIR/${TAG}.log').read()
# Count PASS/FAIL from reward lines only (not headers)
passed = len(re.findall(r'^\s+PASS\s', log, re.MULTILINE))
failed = len(re.findall(r'^\s+FAIL\s', log, re.MULTILINE))
score_m = re.search(r'Score:\s+([\d.]+)', log)
score = score_m.group(1) if score_m else '0'
cost_m = re.search(r'Total cost:\s+\\\$([\d.]+)', log)
cost = cost_m.group(1) if cost_m else '0'
print(f'PASSED={passed} FAILED={failed} SCORE={score} COST={cost}')
" 2>/dev/null)" || { PASSED=0; FAILED=0; SCORE=0; COST=0; }

    TOTAL_PASS=$((TOTAL_PASS + PASSED))
    TOTAL_FAIL=$((TOTAL_FAIL + FAILED))

    # Save per-batch result
    python3 << PYEOF
import json
result = {
    'tag': '$TAG',
    'batch': $BATCH_NUM,
    'score': '$SCORE',
    'passed': $PASSED,
    'failed': $FAILED,
    'cost': '$COST',
    'uids': $(echo "$BATCH_UIDS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip().split('\n')))")
}
with open('$BATCH_RESULT_FILE', 'w') as f:
    json.dump(result, f, indent=2)
PYEOF

    echo "  Batch $BATCH_NUM: $PASSED pass, $FAILED fail, score=$SCORE, cost=\$$COST"
    echo "  Running total: $TOTAL_PASS pass, $TOTAL_FAIL fail"
    echo ""
done

# Aggregate all batch results
echo "=========================================="
echo "  AGGREGATING RESULTS"
echo "=========================================="

python3 -c "
import json, glob
results = []
for f in sorted(glob.glob('$RESULTS_DIR/full246-b*.json')):
    results.append(json.load(open(f)))
total_pass = sum(r['passed'] for r in results)
total_fail = sum(r['failed'] for r in results)
total = total_pass + total_fail
score = total_pass / total if total > 0 else 0
aggregate = {
    'total_questions': total,
    'passed': total_pass,
    'failed': total_fail,
    'score': round(score, 4),
    'batches': results,
}
with open('$RESULTS_JSON', 'w') as f:
    json.dump(aggregate, f, indent=2)
print(f'  FINAL SCORE: {total_pass}/{total} = {score:.1%}')
print(f'  Saved: $RESULTS_JSON')
"

# Restore original samples
rm -rf "$SAMPLES_DIR"
cp -r "$BACKUP_DIR" "$SAMPLES_DIR"
echo ""
echo "  Original samples restored"
echo "=== BATCH EVAL COMPLETE ==="
