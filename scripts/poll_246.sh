#!/bin/bash
# Poll the full 246 run and report to Slack #groundwire
# Run via cron every 10 minutes

RUN_DIR="/home/cat/ground-wire/.arena/runs/run-20260329-065533-511f66/minimax-auditor-v1-full246"
RESULT_FILE="$RUN_DIR/result.json"
SLACK_CHANNEL="C0AM8J6A4DV"

if [ ! -f "$RESULT_FILE" ]; then
  exit 0
fi

# Extract stats
STATS=$(python3 -c "
import json
d = json.load(open('$RESULT_FILE'))
finished = d.get('finished_at')
for k, v in d['stats']['evals'].items():
    n = v['n_trials']; e = v['n_errors']
    rs = v.get('reward_stats', {}).get('reward', {})
    p = len(rs.get('1.0', [])); f = len(rs.get('0.0', []))
    m = v['metrics'][0]['mean'] if v.get('metrics') else 0
    pct = f'{m:.1%}'
    print(f'{n}|{p}|{f}|{e}|{pct}|{finished or \"running\"}')
" 2>/dev/null)

if [ -z "$STATS" ]; then
  exit 0
fi

IFS='|' read -r SCORED PASS FAIL ERRORS PCT STATUS <<< "$STATS"

if [ "$STATUS" != "running" ]; then
  MSG="🏁 *Full 246 COMPLETE* — Auditor v1 on MiniMax\n✅ Pass: $PASS | ❌ Fail: $FAIL | ⚠️ Errors: $ERRORS\n📊 *Final Score: $PCT* ($SCORED/246)"
  # Write a flag so we stop polling
  touch /tmp/arena_246_done
else
  MSG="📊 *246 Progress* — $SCORED/246 scored\n✅ Pass: $PASS | ❌ Fail: $FAIL | ⚠️ Errors: $ERRORS\n📈 Current: *$PCT*"
fi

# Post to Slack via Claude AI MCP isn't available from cron, so use the webhook approach
# We'll write to a file that the monitor can pick up
echo "$MSG" > /tmp/arena_246_status.txt
echo "$(date): $SCORED/246 | P:$PASS F:$FAIL E:$ERRORS | $PCT" >> /tmp/arena_246_poll.log
