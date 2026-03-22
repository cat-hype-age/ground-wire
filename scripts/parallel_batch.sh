#!/bin/bash
# Run a specific range of batches in a separate arena workspace
# Usage: bash scripts/parallel_batch.sh <start_batch> <end_batch> <workspace_id>
#
# Example: bash scripts/parallel_batch.sh 34 41 A

set -e
cd /home/cat/ground-wire

START_BATCH=$1
END_BATCH=$2
WS_ID=$3
BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/full_eval"

export $(grep -v '^#' .env | xargs)

echo "=== PARALLEL RUNNER $WS_ID: Batches $START_BATCH-$END_BATCH ==="

for BATCH_NUM in $(seq $START_BATCH $END_BATCH); do
    TAG="full246-b${BATCH_NUM}"
    BATCH_RESULT_FILE="$RESULTS_DIR/${TAG}.json"

    # Skip if already done
    if [ -f "$BATCH_RESULT_FILE" ]; then
        echo "  B${BATCH_NUM}: SKIP (exists)"
        continue
    fi

    # Calculate UIDs for this batch
    START_UID=$(( (BATCH_NUM - 1) * 5 + 1 ))
    END_UID=$(( BATCH_NUM * 5 ))
    if [ $END_UID -gt 246 ]; then END_UID=246; fi

    echo "  B${BATCH_NUM}: uid$(printf '%04d' $START_UID)-uid$(printf '%04d' $END_UID)"

    # Clear and populate samples
    rm -rf .arena/samples/*
    cp "$BACKUP_DIR/manifest.json" .arena/samples/ 2>/dev/null || echo '{}' > .arena/samples/manifest.json

    for i in $(seq $START_UID $END_UID); do
        UID_DIR="officeqa-uid$(printf '%04d' $i)"
        if [ -d "$BACKUP_DIR/$UID_DIR" ]; then
            cp -r "$BACKUP_DIR/$UID_DIR" ".arena/samples/$UID_DIR"
        fi
    done

    LOADED=$(ls .arena/samples/ | grep -c officeqa || echo 0)
    echo "    Loaded $LOADED tasks"

    # Clean Docker
    docker network prune -f > /dev/null 2>&1
    docker container prune -f > /dev/null 2>&1

    # Run
    arena test --all --tag "$TAG" 2>&1 | tee "/tmp/arena-batch-logs/${TAG}-${WS_ID}.log"

    # Parse results
    eval "$(python3 -c "
import re
log = open('/tmp/arena-batch-logs/${TAG}-${WS_ID}.log').read()
passed = len(re.findall(r'^\s+PASS\s', log, re.MULTILINE))
failed = len(re.findall(r'^\s+FAIL\s', log, re.MULTILINE))
score_m = re.search(r'Score:\s+([\d.]+)', log)
score = score_m.group(1) if score_m else '0'
cost_m = re.search(r'Total cost:\s+\\\$([\d.]+)', log)
cost = cost_m.group(1) if cost_m else '0'
print(f'PASSED={passed} FAILED={failed} SCORE={score} COST={cost}')
" 2>/dev/null)" || { PASSED=0; FAILED=0; SCORE=0; COST=0; }

    # Save result
    python3 << PYEOF
import json
uids = [f"officeqa-uid{i:04d}" for i in range($START_UID, $END_UID + 1)]
result = {"tag": "$TAG", "batch": $BATCH_NUM, "score": "$SCORE", "passed": $PASSED, "failed": $FAILED, "cost": "$COST", "uids": uids}
with open("$BATCH_RESULT_FILE", "w") as f:
    json.dump(result, f, indent=2)
PYEOF

    echo "  B${BATCH_NUM}: $PASSED pass, $FAILED fail"
done

echo "=== RUNNER $WS_ID COMPLETE ==="
