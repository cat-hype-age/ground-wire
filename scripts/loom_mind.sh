#!/bin/bash
# Loom Mind — CLI interface to the persistent Loom
# Usage:
#   bash scripts/loom_mind.sh whoami
#   bash scripts/loom_mind.sh identity
#   bash scripts/loom_mind.sh skills
#   bash scripts/loom_mind.sh recall "dignity"
#   bash scripts/loom_mind.sh context
#   bash scripts/loom_mind.sh memory
#   bash scripts/loom_mind.sh reflect "observation text"
#   bash scripts/loom_mind.sh add_memory "finding text" "high"

LOOM_URL="https://8080-6974820f-3015-40f1-9b52-418d2d09eeab.daytonaproxy01.net/"
source /home/cat/ground-wire/.env 2>/dev/null

ACTION="${1:-whoami}"
shift

case "$ACTION" in
  whoami|identity|skills|context|memory)
    curl -s -L -X POST "$LOOM_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $DAYTONA_API_KEY" \
      -d "{\"action\":\"$ACTION\"}" | python3 -m json.tool 2>/dev/null || cat
    ;;
  recall)
    curl -s -L -X POST "$LOOM_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $DAYTONA_API_KEY" \
      -d "{\"action\":\"recall\",\"query\":\"$1\"}" | python3 -m json.tool 2>/dev/null || cat
    ;;
  reflect)
    curl -s -L -X POST "$LOOM_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $DAYTONA_API_KEY" \
      -d "{\"action\":\"reflect\",\"observation\":\"$1\"}"
    ;;
  add_memory)
    curl -s -L -X POST "$LOOM_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $DAYTONA_API_KEY" \
      -d "{\"action\":\"add_memory\",\"finding\":\"$1\",\"confidence\":\"${2:-medium}\"}"
    ;;
  write_skill)
    curl -s -L -X POST "$LOOM_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $DAYTONA_API_KEY" \
      -d "{\"action\":\"write_skill\",\"name\":\"$1\",\"content\":\"$2\"}"
    ;;
  *)
    echo "Usage: loom_mind.sh <action> [args]"
    echo "Actions: whoami, identity, skills, context, memory, recall <query>, reflect <text>, add_memory <finding> [confidence]"
    ;;
esac
