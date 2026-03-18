#!/bin/bash
# Recall memories from the Ground Wire knowledge base
# Usage: bash ~/.config/opencode/skills/memory-server/recall.sh "search query"
# Or: bash ~/.config/opencode/skills/memory-server/recall.sh --category data_location

DB="/app/memory.db"
SCRIPT_DIR="$(dirname "$0")"

# Initialize DB from seed if needed
if [ ! -f "$DB" ] && [ -f "$SCRIPT_DIR/memory_seed.db" ]; then
    cp "$SCRIPT_DIR/memory_seed.db" "$DB"
fi

if [ ! -f "$DB" ]; then
    echo "No memory database found."
    exit 1
fi

if [ "$1" = "--category" ]; then
    sqlite3 "$DB" "SELECT '[' || category || '] ' || content FROM memories WHERE category = '$2' ORDER BY created_at DESC;"
elif [ "$1" = "--stats" ]; then
    echo "Memory stats:"
    sqlite3 "$DB" "SELECT category, COUNT(*) as count FROM memories GROUP BY category ORDER BY count DESC;"
    echo ""
    sqlite3 "$DB" "SELECT 'Total: ' || COUNT(*) FROM memories;"
else
    # Full-text search
    sqlite3 "$DB" "SELECT '[' || m.category || '] ' || m.content FROM memories_fts f JOIN memories m ON f.rowid = m.id WHERE memories_fts MATCH '$1' ORDER BY rank LIMIT 10;" 2>/dev/null
    if [ $? -ne 0 ]; then
        # Fallback to LIKE search
        sqlite3 "$DB" "SELECT '[' || category || '] ' || content FROM memories WHERE content LIKE '%$1%' LIMIT 10;"
    fi
fi
