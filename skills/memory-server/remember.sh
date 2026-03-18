#!/bin/bash
# Store a new memory in the Ground Wire knowledge base
# Usage: bash ~/.config/opencode/skills/memory-server/remember.sh "category" "content" "tags"

DB="/app/memory.db"
SCRIPT_DIR="$(dirname "$0")"

# Initialize DB from seed if needed
if [ ! -f "$DB" ] && [ -f "$SCRIPT_DIR/memory_seed.db" ]; then
    cp "$SCRIPT_DIR/memory_seed.db" "$DB"
fi

CATEGORY="${1:-observation}"
CONTENT="$2"
TAGS="${3:-}"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -z "$CONTENT" ]; then
    echo "Usage: remember.sh <category> <content> [tags]"
    echo "Categories: data_location, table_structure, search_strategy, unit_convention, correction, computation_pattern"
    exit 1
fi

sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, content TEXT NOT NULL, tags TEXT NOT NULL DEFAULT '', source_file TEXT DEFAULT '', created_at TEXT NOT NULL);"
sqlite3 "$DB" "INSERT INTO memories (category, content, tags, source_file, created_at) VALUES ('$CATEGORY', '$CONTENT', '$TAGS', '', '$NOW');"
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM memories;")
echo "Stored. Total memories: $COUNT"
