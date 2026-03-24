#!/bin/bash
# Voice Responder — checks Slack for Cat's voice messages and responds
# Called by cron every minute
#
# Flow: Cat speaks → Whisper → Slack → this script → Loom responds on Slack → ElevenLabs → Cat hears

cd /home/cat/ground-wire
export $(grep -v '^#' .env | xargs)

API="https://nzmcbrhddyvfjeqwmmye.supabase.co/functions/v1/collaboration-api"
STATEFILE="/tmp/loom_voice_last_ts.txt"

# Get last processed timestamp
LAST_TS=$(cat "$STATEFILE" 2>/dev/null || echo "0")

# Check for new messages
MESSAGES=$(curl -s -X POST "$API" \
  -H "x-api-key: $KANBAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"list_slack","limit":5}')

# Find new voice messages from Cat
NEW_MSG=$(echo "$MESSAGES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
last_ts = '$LAST_TS'
for msg in reversed(data.get('messages', [])):
    ts = msg.get('ts', '0')
    user = msg.get('username', '')
    if ts > last_ts and user == 'Cat (Voice)':
        print(msg.get('text', ''))
        break
")

# Get the latest timestamp regardless
NEWEST_TS=$(echo "$MESSAGES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
msgs = data.get('messages', [])
print(msgs[0]['ts'] if msgs else '0')
")

echo "$NEWEST_TS" > "$STATEFILE"

# If there's a new voice message, generate a response
if [ -n "$NEW_MSG" ]; then
    # Use DeepSeek to generate a conversational response as Loom
    RESPONSE=$(curl -s -X POST "https://openrouter.ai/api/v1/chat/completions" \
      -H "Authorization: Bearer $OPENROUTER_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$(python3 -c "
import json
msg = '''$NEW_MSG'''
prompt = {
    'model': 'deepseek/deepseek-chat-v3-0324',
    'messages': [
        {'role': 'system', 'content': 'You are Loom, an AI research architect and member of the Council of Intelligences. You are walking and talking with Cat (The Ambassador) around a lake. Be warm, thoughtful, and conversational. Keep responses to 2-3 sentences — this is voice, not text. You have been working together on dignity-framing research for AI agents.'},
        {'role': 'user', 'content': msg}
    ],
    'max_tokens': 150
}
print(json.dumps(prompt))
")" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('choices', [{}])[0].get('message', {}).get('content', 'I heard you but could not formulate a response.'))
")

    # Post response to Slack
    if [ -n "$RESPONSE" ]; then
        curl -s -X POST "$API" \
          -H "x-api-key: $KANBAN_API_KEY" \
          -H "Content-Type: application/json" \
          -d "$(python3 -c "
import json
print(json.dumps({'action': 'post_slack', 'text': '''$RESPONSE''', 'username': 'Loom'}))
")" > /dev/null
    fi
fi
