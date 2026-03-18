"""Ground Wire Memory Server — Zero-dependency MCP server.

Implements the MCP stdio protocol using only Python stdlib.
No fastmcp needed. Runs inside the arena container with python3 + sqlite3.

Usage:
    python3 mcp/memory_server_raw.py
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/app/memory.db")

# If shipped with skills, check for pre-seeded DB
SEED_PATH = Path(__file__).parent / "memory_seed.db"
if SEED_PATH.exists() and not DB_PATH.exists():
    import shutil
    shutil.copy2(SEED_PATH, DB_PATH)


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            source_file TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(content, tags, category, source_file, content='memories', content_rowid='id')
    """)
    db.executescript("""
        CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, content, tags, category, source_file)
            VALUES (new.id, new.content, new.tags, new.category, new.source_file);
        END;
        CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, content, tags, category, source_file)
            VALUES ('delete', old.id, old.content, old.tags, old.category, old.source_file);
        END;
    """)
    db.commit()
    return db


TOOLS = [
    {
        "name": "remember",
        "description": "Store an observation about the Treasury Bulletin corpus for future recall.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The observation to remember"},
                "category": {"type": "string", "description": "One of: data_location, table_structure, search_strategy, unit_convention, correction, computation_pattern"},
                "tags": {"type": "string", "description": "Comma-separated keywords"},
                "source_file": {"type": "string", "description": "Treasury Bulletin filename if applicable"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "recall",
        "description": "Search stored memories. Call BEFORE searching the corpus to check existing knowledge.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "recall_by_category",
        "description": "Get all memories in a category: data_location, table_structure, search_strategy, unit_convention, correction, computation_pattern",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category to filter by"},
            },
            "required": ["category"],
        },
    },
    {
        "name": "memory_stats",
        "description": "Show how many observations are stored per category.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def handle_remember(args: dict) -> str:
    content = args.get("content", "")
    category = args.get("category", "observation")
    tags = args.get("tags", "")
    source_file = args.get("source_file", "")
    db = get_db()
    db.execute(
        "INSERT INTO memories (category, content, tags, source_file, created_at) VALUES (?, ?, ?, ?, ?)",
        (category, content, tags, source_file, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    count = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    db.close()
    return f"Stored. Total memories: {count}"


def handle_recall(args: dict) -> str:
    query = args.get("query", "")
    limit = args.get("limit", 10)
    db = get_db()
    try:
        results = db.execute(
            """SELECT m.category, m.content, m.tags, m.source_file
               FROM memories_fts f JOIN memories m ON f.rowid = m.id
               WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?""",
            (query, limit),
        ).fetchall()
    except Exception:
        results = []
    db.close()
    if not results:
        return "No relevant memories found."
    lines = []
    for cat, content, tags, source in results:
        entry = f"[{cat}] {content}"
        if tags:
            entry += f" (tags: {tags})"
        if source:
            entry += f" (from: {source})"
        lines.append(entry)
    return "\n---\n".join(lines)


def handle_recall_by_category(args: dict) -> str:
    category = args.get("category", "")
    db = get_db()
    results = db.execute(
        "SELECT content, tags, source_file FROM memories WHERE category = ? ORDER BY created_at DESC",
        (category,),
    ).fetchall()
    db.close()
    if not results:
        return f"No memories in category '{category}'."
    lines = []
    for content, tags, source in results:
        entry = content
        if tags:
            entry += f" (tags: {tags})"
        if source:
            entry += f" (from: {source})"
        lines.append(entry)
    return "\n---\n".join(lines)


def handle_memory_stats(args: dict) -> str:
    db = get_db()
    rows = db.execute(
        "SELECT category, COUNT(*) FROM memories GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    total = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    db.close()
    if total == 0:
        return "Memory is empty. Use 'remember' to store observations."
    lines = [f"Total memories: {total}", ""]
    for cat, count in rows:
        lines.append(f"  {cat}: {count}")
    return "\n".join(lines)


HANDLERS = {
    "remember": handle_remember,
    "recall": handle_recall,
    "recall_by_category": handle_recall_by_category,
    "memory_stats": handle_memory_stats,
}


def send(obj: dict):
    """Write a JSON-RPC response to stdout."""
    data = json.dumps(obj)
    # MCP uses Content-Length framing over stdio
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()


def read_message() -> dict | None:
    """Read a Content-Length framed JSON-RPC message from stdin."""
    # Read headers
    while True:
        line = sys.stdin.readline()
        if not line:
            return None  # EOF
        line = line.strip()
        if line.startswith("Content-Length:"):
            length = int(line.split(":", 1)[1].strip())
        if line == "":
            break
    # Read body
    body = sys.stdin.read(length)
    if not body:
        return None
    return json.loads(body)


def main():
    while True:
        msg = read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "ground-wire-memory",
                        "version": "1.0.0",
                    },
                },
            })

        elif method == "notifications/initialized":
            pass  # No response needed for notifications

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS},
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            handler = HANDLERS.get(tool_name)
            if handler:
                try:
                    result_text = handler(arguments)
                    send({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": result_text}],
                        },
                    })
                except Exception as e:
                    send({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {e}"}],
                            "isError": True,
                        },
                    })
            else:
                send({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                })

        elif msg_id is not None:
            # Unknown method with an ID — respond with error
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })


if __name__ == "__main__":
    main()
