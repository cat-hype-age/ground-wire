"""Ground Wire Memory Server — MCP server for persistent agent memory.

Stores observations about the Treasury Bulletin corpus so the agent
can learn from previous questions and reuse knowledge across tasks.

Storage: SQLite + basic keyword search. Intentionally simple —
we want fast lookups, not a vector DB.

Usage:
    python mcp/memory_server.py                     # stdio transport (for arena)
    python mcp/memory_server.py --transport sse      # SSE transport (for dev)
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

DB_PATH = Path(__file__).parent / "memory.db"

mcp = FastMCP(
    "ground-wire-memory",
    instructions=(
        "Persistent memory for Treasury Bulletin corpus analysis. "
        "Use 'remember' to store useful observations about documents, "
        "table structures, and data locations. Use 'recall' to retrieve "
        "relevant memories before searching the corpus."
    ),
)


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
    # Triggers to keep FTS in sync
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


@mcp.tool()
def remember(
    content: str,
    category: str = "observation",
    tags: str = "",
    source_file: str = "",
) -> str:
    """Store an observation about the Treasury Bulletin corpus.

    Use this to save useful knowledge for future questions:
    - Where specific data types are found
    - Table structure patterns in specific bulletins
    - Corrections (e.g., "1939 bulletin uses 'millions' not 'billions'")
    - Successful search strategies

    Args:
        content: The observation to remember.
        category: One of: table_structure, data_location, search_strategy,
                  unit_convention, correction, computation_pattern
        tags: Comma-separated keywords for retrieval (e.g., "defense,expenditure,1940s")
        source_file: The Treasury Bulletin filename this relates to (if any)
    """
    db = get_db()
    db.execute(
        "INSERT INTO memories (category, content, tags, source_file, created_at) VALUES (?, ?, ?, ?, ?)",
        (category, content, tags, source_file, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    count = db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    db.close()
    return f"Stored. Total memories: {count}"


@mcp.tool()
def recall(query: str, limit: int = 10) -> str:
    """Search stored memories for relevant observations.

    Call this BEFORE searching the corpus to check if you already know
    where to find the data or what patterns to expect.

    Args:
        query: Natural language search query (e.g., "defense expenditure table structure")
        limit: Maximum number of results to return.
    """
    db = get_db()

    # FTS search
    results = db.execute(
        """
        SELECT m.id, m.category, m.content, m.tags, m.source_file, m.created_at
        FROM memories_fts f
        JOIN memories m ON f.rowid = m.id
        WHERE memories_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()

    db.close()

    if not results:
        return "No relevant memories found."

    lines = []
    for row in results:
        mid, cat, content, tags, source, created = row
        entry = f"[{cat}] {content}"
        if tags:
            entry += f" (tags: {tags})"
        if source:
            entry += f" (from: {source})"
        lines.append(entry)

    return "\n---\n".join(lines)


@mcp.tool()
def recall_by_category(category: str) -> str:
    """Get all memories in a specific category.

    Categories: table_structure, data_location, search_strategy,
    unit_convention, correction, computation_pattern, observation

    Args:
        category: The category to filter by.
    """
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


@mcp.tool()
def memory_stats() -> str:
    """Show memory statistics — how many observations stored per category."""
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


if __name__ == "__main__":
    transport = "stdio"
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        transport = sys.argv[idx + 1]

    if transport == "sse":
        mcp.run(transport="sse", host="0.0.0.0", port=37777)
    else:
        mcp.run(transport="stdio")
