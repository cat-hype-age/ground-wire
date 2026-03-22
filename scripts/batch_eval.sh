#!/bin/bash
# Batch evaluation — swap arena samples in groups, run arena test --all
# Tests the full 246 questions by cycling through batches of 20
#
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/batch_eval.sh

set -e
cd /home/cat/ground-wire

SAMPLES_DIR=".arena/samples"
BACKUP_DIR="/tmp/arena-samples-backup"
ALL_SAMPLES_DIR="/tmp/arena-all-samples"
RESULTS_FILE="results/full_eval/batch_results.json"
TAG_PREFIX="batch"

# Backup original 20 samples
echo "=== BATCH EVAL: Full 246-question OfficeQA ==="
rm -rf "$BACKUP_DIR"
cp -r "$SAMPLES_DIR" "$BACKUP_DIR"
echo "Original 20 samples backed up"

# Collect ALL sample directories (our generated 226 + original 20)
# They're already in .arena/samples/ from our earlier generation
ALL_UIDS=$(ls "$SAMPLES_DIR" | grep "^officeqa-" | sort)
TOTAL=$(echo "$ALL_UIDS" | wc -l)
echo "Total samples available: $TOTAL"

# Process in batches of 20
BATCH_SIZE=20
BATCH_NUM=0
ALL_RESULTS="[]"

echo "$ALL_UIDS" | while read -r batch_line; do
    echo "$batch_line"
done | split -l $BATCH_SIZE - /tmp/batch_

for batch_file in /tmp/batch_*; do
    BATCH_NUM=$((BATCH_NUM + 1))
    BATCH_UIDS=$(cat "$batch_file")
    BATCH_COUNT=$(echo "$BATCH_UIDS" | wc -l)

    echo ""
    echo "=========================================="
    echo "  BATCH $BATCH_NUM ($BATCH_COUNT tasks)"
    echo "=========================================="

    # Clear samples dir and populate with this batch only
    rm -rf "$SAMPLES_DIR"/*

    # Copy manifest
    cp "$BACKUP_DIR/manifest.json" "$SAMPLES_DIR/" 2>/dev/null || echo '{"version":"batch"}' > "$SAMPLES_DIR/manifest.json"

    # Copy this batch's samples
    for uid in $BATCH_UIDS; do
        if [ -d "$BACKUP_DIR/$uid" ]; then
            cp -r "$BACKUP_DIR/$uid" "$SAMPLES_DIR/$uid"
        elif [ -d "/tmp/arena-all-generated/$uid" ]; then
            cp -r "/tmp/arena-all-generated/$uid" "$SAMPLES_DIR/$uid"
        fi
    done

    echo "  Loaded $(ls "$SAMPLES_DIR" | grep officeqa | wc -l) tasks"

    # Clean Docker
    docker network prune -f > /dev/null 2>&1
    docker container prune -f > /dev/null 2>&1

    # Run arena test
    TAG="${TAG_PREFIX}-${BATCH_NUM}"
    echo "  Running arena test --all --tag $TAG"
    arena test --all --tag "$TAG" 2>&1 | tee "/tmp/batch_${BATCH_NUM}.log"

    # Extract results
    SCORE=$(grep "Score:" "/tmp/batch_${BATCH_NUM}.log" | tail -1 | awk '{print $2}')
    PASSED=$(grep -c "PASS" "/tmp/batch_${BATCH_NUM}.log" || echo 0)
    FAILED=$(grep -c "FAIL" "/tmp/batch_${BATCH_NUM}.log" || echo 0)

    echo "  Batch $BATCH_NUM: $PASSED pass, $FAILED fail, score=$SCORE"
done

# Restore original samples
rm -rf "$SAMPLES_DIR"
cp -r "$BACKUP_DIR" "$SAMPLES_DIR"
echo ""
echo "Original samples restored"
echo "=== BATCH EVAL COMPLETE ==="

# Clean up
rm -f /tmp/batch_*
