#!/bin/bash
# Run all remaining (unscored) questions in a single concurrent arena batch
# The arena handles 4 concurrent Docker containers internally
#
# This is MUCH faster than the sequential batch_eval.sh approach:
# - No overhead clearing/loading samples between batches
# - No Docker prune pauses
# - Arena's internal scheduler optimizes container lifecycle
#
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/run_remaining.sh
#
# Prerequisites:
# - /tmp/arena-samples-backup must exist with correctly-scored samples
#   (expected_answer in tests/config.json, NOT answer)
# - Run scripts/post_reboot_recovery.sh first if recovering from restart

set -e
cd /home/cat/ground-wire

BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/full_eval"

echo "=== RUN REMAINING QUESTIONS ==="

# Find which UIDs already have results
COMPLETED_UIDS=$(python3 -c "
import json, glob
uids = set()
for f in glob.glob('$RESULTS_DIR/full246-b*.json'):
    d = json.load(open(f))
    for uid in d.get('uids', []):
        uids.add(uid)
print(' '.join(sorted(uids)))
")

TOTAL_COMPLETED=$(echo "$COMPLETED_UIDS" | wc -w)
echo "  Already scored: $TOTAL_COMPLETED UIDs"

# Clear samples and load only unscored UIDs
rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/ 2>/dev/null || echo '{}' > .arena/samples/manifest.json

LOADED=0
for uid_dir in "$BACKUP_DIR"/officeqa-uid*; do
    uid_name=$(basename "$uid_dir")
    if ! echo "$COMPLETED_UIDS" | grep -q "$uid_name"; then
        cp -r "$uid_dir" ".arena/samples/$uid_name"
        LOADED=$((LOADED + 1))
    fi
done

echo "  Loaded $LOADED remaining questions"

if [ "$LOADED" -eq 0 ]; then
    echo "  All questions scored! Nothing to do."
    exit 0
fi

# Clean Docker
docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

# Run all at once — arena handles 4 concurrent containers
echo "  Launching $LOADED questions (arena manages concurrency)..."
echo "  This is ~${LOADED}x faster than sequential batching"
arena test --all --tag "full246-remaining-$(date +%H%M)" 2>&1 | tee /tmp/arena-batch-logs/remaining-run.log

echo ""
echo "=== RUN COMPLETE ==="
echo "  Parse results with: grep -cE 'PASS|FAIL' /tmp/arena-batch-logs/remaining-run.log"
