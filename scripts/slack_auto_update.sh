#!/bin/bash
# Auto Slack status update — called by cron
cd /home/cat/ground-wire
export $(grep -v '^#' .env | xargs)

RESULT=$(python3 -c "
import json, glob
batches = sorted(glob.glob('results/full_eval/full246-b*.json'))
if batches:
    tp = sum(int(json.load(open(f)).get('passed',0)) for f in batches)
    t = tp + sum(int(json.load(open(f)).get('failed',0)) for f in batches)
    print(f'Auto-check: {tp}/{t} = {tp/t*100:.1f}% ({len(batches)} batches, {246-t} remaining)')
else:
    print('No batch data yet')
" 2>/dev/null)

if [ -n "$RESULT" ] && [ -n "$KANBAN_API_KEY" ]; then
    curl -s -X POST "https://nzmcbrhddyvfjeqwmmye.supabase.co/functions/v1/collaboration-api" \
        -H "x-api-key: $KANBAN_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"action\":\"post_slack\",\"text\":\"$RESULT\",\"username\":\"Loom\"}" > /dev/null 2>&1
fi
