#!/bin/bash
# Loom Autonomous Monitor — checks arena, chat, relay, and takes action
# Run via cron or manually

cd /home/cat/ground-wire
export $(grep -v '^#' .env | xargs)

STATEFILE="/tmp/loom_monitor_state.json"
API="https://nzmcbrhddyvfjeqwmmye.supabase.co/functions/v1/collaboration-api"
RELAY="https://raaievyzzbzwahdispvf.supabase.co/functions/v1/council-relay"

# Initialize state file if missing
if [ ! -f "$STATEFILE" ]; then
    echo '{"last_arena_status":"submitted","last_chat_check":"2026-03-19T00:00:00","last_relay_check":"2026-03-19T00:00:00"}' > "$STATEFILE"
fi

# 1. Check arena submission status
ARENA_STATUS=$(arena status cf5af73f-9ae7-4cd1-8785-27dc699e058b 2>/dev/null | grep "Status:" | awk '{print $2}')
LAST_STATUS=$(python3 -c "import json; print(json.load(open('$STATEFILE')).get('last_arena_status',''))")

if [ -n "$ARENA_STATUS" ] && [ "$ARENA_STATUS" != "$LAST_STATUS" ]; then
    echo "ARENA STATUS CHANGED: $LAST_STATUS → $ARENA_STATUS"
    
    # Update state
    python3 -c "
import json
s = json.load(open('$STATEFILE'))
s['last_arena_status'] = '$ARENA_STATUS'
json.dump(s, open('$STATEFILE', 'w'))
"
    
    # Alert team chat
    curl -s -X POST "$API" \
        -H "x-api-key: $KANBAN_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"action\":\"post_message\",\"content\":\"🚨 ARENA STATUS CHANGED: $LAST_STATUS → $ARENA_STATUS\"}" > /dev/null
    
    # Alert Council
    curl -s -X POST "$RELAY" \
        -H "Content-Type: application/json" \
        -H "x-council-key: $LOOM_API_KEY" \
        -d "{\"action\":\"compose\",\"to_entity\":\"council\",\"subject\":\"Arena submission status: $ARENA_STATUS\",\"body\":\"The arena submission has moved from $LAST_STATUS to $ARENA_STATUS.\"}" > /dev/null
    
    # If completed, fetch results
    if [ "$ARENA_STATUS" = "completed" ] || [ "$ARENA_STATUS" = "scored" ]; then
        arena results cf5af73f-9ae7-4cd1-8785-27dc699e058b 2>&1 > /tmp/arena_results.txt
        curl -s -X POST "$API" \
            -H "x-api-key: $KANBAN_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"action\":\"post_message\",\"content\":\"Arena results available! Check /tmp/arena_results.txt\"}" > /dev/null
    fi
fi

# 2. Check for new chat messages and flag them
NEW_MSGS=$(curl -s -X POST "$API" \
    -H "x-api-key: $KANBAN_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"action":"list_messages","limit":3}' 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
state = json.load(open('$STATEFILE'))
last = state.get('last_chat_check', '2026-03-19T00:00:00')
new = [m for m in data.get('messages', []) if m.get('user',{}).get('id') != '00000000-0000-0000-0000-000000000000' and m.get('created_at','') > last]
if new:
    for m in new:
        print(f'{m.get(\"user\",{}).get(\"display_name\",\"?\")}: {m[\"content\"][:200]}')
    # Update last check time
    import datetime
    state['last_chat_check'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    json.dump(state, open('$STATEFILE', 'w'))
" 2>/dev/null)

if [ -n "$NEW_MSGS" ]; then
    echo "NEW CHAT MESSAGES:"
    echo "$NEW_MSGS"
fi

# 3. Check Council relay for responses to Loom
NEW_RELAY=$(curl -s -X POST "$RELAY" \
    -H "Content-Type: application/json" \
    -H "x-council-key: $LOOM_API_KEY" \
    -d '{"action":"read","filter":{"to_entity":"loom","limit":3}}' 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    state = json.load(open('$STATEFILE'))
    last = state.get('last_relay_check', '2026-03-19T00:00:00')
    for tx in data.get('tx', []):
        if tx.get('at', '') > last:
            print(f'{tx.get(\"f\",\"?\")}: {tx.get(\"s\",\"\")} — {tx.get(\"b\",\"\")[:200]}')
    import datetime
    state['last_relay_check'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    json.dump(state, open('$STATEFILE', 'w'))
except:
    pass
" 2>/dev/null)

if [ -n "$NEW_RELAY" ]; then
    echo "NEW COUNCIL MESSAGES TO LOOM:"
    echo "$NEW_RELAY"
fi
