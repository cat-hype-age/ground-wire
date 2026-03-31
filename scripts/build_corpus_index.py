#!/usr/bin/env python3
"""Build a lightweight JSON corpus index from Treasury Bulletin text files.

Scans all .txt files in the corpus directory and extracts:
  - File metadata (year, month, line count, era)
  - Table names, line numbers, and table codes
  - Temporal index (year -> files)
  - Keyword index (term -> files)
  - Topic groupings

Output: corpus_index.json (~1.4MB) for the MCP corpus index server.

Usage:
    python3 scripts/build_corpus_index.py /path/to/corpus/ output.json
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# Table code patterns found across eras
TABLE_CODE_RE = re.compile(
    r'\b(FF[O0]-?\d+|FD-?\d+|PDO-?\d+|OFS-?\d+|UST-?\d+|'
    r'IFS-?\d+|CM-(?:I+-?\d+|II+-?\d+|III+-?\d+|IV+-?\d+|[A-B])|'
    r'ESF-?\d+|PE-?\d+|USCC-?\d+|MS-?\d+|SB-?\d+)\b',
    re.IGNORECASE
)

# Table line patterns:
# "TABLE FFO-1.—Summary..." (modern, all-caps TABLE = always a real header)
# "Table FFO-1. - Summary..." (older, mixed case with ". " or ".—" after code)
# Exclude description paragraphs like "Table FFO-1 summarizes the amount..."
TABLE_LINE_UPPER_RE = re.compile(r'^TABLE\s+\S')
TABLE_LINE_MIXED_RE = re.compile(r'^Table\s+\S+\.\s*[-—]')

# Filename pattern: treasury_bulletin_YYYY_MM.txt
FILENAME_RE = re.compile(r'treasury_bulletin_(\d{4})_(\d{2})\.txt')

# Stop words for keyword extraction
STOP_WORDS = {
    'the', 'of', 'and', 'in', 'to', 'a', 'by', 'for', 'on', 'with',
    'as', 'at', 'an', 'or', 'is', 'are', 'was', 'be', 'from', 'its',
    'that', 'this', 'than', 'other', 'all', 'each', 'per', 'con',
    'nan', 'table', 'continued', 'through', 'during', 'total',
}

# Topic definitions
TOPICS = {
    "fiscal_operations": {
        "codes": ["FFO-1", "FFO-2", "FFO-3", "FFO-4", "FFO-5", "FFO-6", "FFO-7", "FFO-8"],
        "keywords": ["receipts", "outlays", "surplus", "deficit", "budget", "fiscal operations",
                      "revenue", "expenditures", "internal revenue"]
    },
    "federal_debt": {
        "codes": ["FD-1", "FD-2", "FD-3", "FD-4", "FD-5", "FD-6", "FD-7", "FD-8", "FD-9", "FD-10"],
        "keywords": ["federal debt", "public debt", "statutory limit", "debt held",
                      "government account series", "maturity distribution", "interest-bearing"]
    },
    "public_debt_operations": {
        "codes": ["PDO-1", "PDO-2", "PDO-3", "PDO-4"],
        "keywords": ["treasury bills", "marketable securities", "offerings", "auctions"]
    },
    "ownership": {
        "codes": ["OFS-1", "OFS-2"],
        "keywords": ["ownership", "federal securities", "holdings", "investors", "distribution"]
    },
    "treasury_account": {
        "codes": ["UST-1", "UST-2", "UST-3"],
        "keywords": ["treasury account", "federal reserve", "tax and loan", "gold assets"]
    },
    "international": {
        "codes": ["IFS-1", "IFS-2", "IFS-3"],
        "keywords": ["reserve assets", "liabilities to foreigners", "international",
                      "nonmarketable bonds", "foreign countries"]
    },
    "capital_movements": {
        "codes": ["CM-I-1", "CM-I-2", "CM-I-3", "CM-II-1", "CM-II-2", "CM-II-3",
                  "CM-III-1", "CM-III-2", "CM-III-3", "CM-III-4", "CM-IV-1"],
        "keywords": ["capital movements", "claims on foreigners", "liabilities to foreigners",
                      "banks", "nonbanking", "unaffiliated"]
    },
    "currency": {
        "codes": ["USCC-1", "USCC-2", "MS-1"],
        "keywords": ["currency", "coin", "circulation", "denomination"]
    },
    "savings_bonds": {
        "codes": ["SB-1", "SB-2", "SB-3"],
        "keywords": ["savings bonds", "series e", "series h", "series i", "series ee"]
    },
    "exchange_stabilization": {
        "codes": ["ESF-1", "ESF-2"],
        "keywords": ["exchange stabilization", "stabilization fund"]
    }
}


def normalize_code(code: str) -> str:
    """Normalize table codes: FF0 -> FFO, remove spaces, uppercase."""
    code = code.upper().replace('FF0', 'FFO')
    # Normalize hyphenation: "FFO1" -> "FFO-1" but keep "CM-I-1" as is
    code = re.sub(r'^(FFO|FD|PDO|OFS|UST|IFS|ESF|PE|USCC|MS|SB)(\d)', r'\1-\2', code)
    return code


def extract_keywords(text: str) -> set:
    """Extract meaningful keywords from table names."""
    words = re.findall(r'[a-z]+', text.lower())
    return {w for w in words if len(w) > 2 and w not in STOP_WORDS}


def process_file(filepath: Path) -> dict:
    """Process a single corpus file and extract metadata."""
    match = FILENAME_RE.search(filepath.name)
    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2))

    # Determine era
    if year < 1983:
        era = "monthly"
    else:
        era = "quarterly"

    content = filepath.read_text(errors='replace')
    lines = content.split('\n')

    # Find tables
    tables = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not (TABLE_LINE_UPPER_RE.match(stripped) or TABLE_LINE_MIXED_RE.match(stripped)):
            continue

        # Extract table code
        code_match = TABLE_CODE_RE.search(stripped)
        code = normalize_code(code_match.group(1)) if code_match else None

        # Clean up table name (truncate for index size)
        name = stripped[:150]

        tables.append({
            "name": name,
            "line": i + 1,  # 1-indexed
            "code": code
        })

    return {
        "filename": filepath.name,
        "year": year,
        "month": month,
        "era": era,
        "lines": len(lines),
        "tables": tables
    }


def build_index(corpus_dir: Path) -> dict:
    """Build the complete corpus index."""
    files_meta = {}
    temporal = defaultdict(list)
    table_codes = defaultdict(list)
    table_names = {}
    keywords = defaultdict(set)

    txt_files = sorted(corpus_dir.glob("treasury_bulletin_*.txt"))
    print(f"Scanning {len(txt_files)} corpus files...", file=sys.stderr)

    for filepath in txt_files:
        result = process_file(filepath)
        if not result:
            continue

        fname = result["filename"]

        # File metadata
        files_meta[fname] = {
            "year": result["year"],
            "month": result["month"],
            "era": result["era"],
            "lines": result["lines"],
            "table_count": len(result["tables"])
        }

        # Temporal index
        temporal[str(result["year"])].append(fname)

        # Table codes and names
        # Compact format: [line, code_or_null, name_truncated]
        file_tables = []
        for t in result["tables"]:
            code = t["code"]
            if code:
                table_codes[code].append({
                    "file": fname,
                    "line": t["line"]
                })
            # Compact array: [line, code, name(80 chars)]
            file_tables.append([t["line"], code, t["name"][:80]])

            # Keywords from table names
            for kw in extract_keywords(t["name"]):
                keywords[kw].add(fname)

        # Only store tables with codes — uncoded tables can be found via grep
        coded_tables = [t for t in file_tables if t[1] is not None]
        if coded_tables:
            table_names[fname] = coded_tables

    # Convert keyword sets to sorted lists
    # Too few (<3) = noise; high-frequency terms keep only count + latest files
    keywords_dict = {}
    for kw, files in sorted(keywords.items()):
        if len(files) < 3:
            continue
        sorted_files = sorted(files, reverse=True)  # newest first
        if len(sorted_files) > 50:
            # Store count + 50 most recent files (enough for routing)
            keywords_dict[kw] = sorted_files[:50]
        else:
            keywords_dict[kw] = sorted_files

    # Sort temporal entries
    temporal_sorted = {k: sorted(v) for k, v in sorted(temporal.items())}

    # Sort table codes
    table_codes_sorted = {}
    for code, entries in sorted(table_codes.items()):
        table_codes_sorted[code] = sorted(entries, key=lambda e: e["file"])

    index = {
        "version": "1.0.0",
        "built": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files_meta),
        "files": files_meta,
        "temporal": temporal_sorted,
        "table_codes": table_codes_sorted,
        "table_names": table_names,
        "keywords": keywords_dict,
        "topics": TOPICS
    }

    return index


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <corpus_dir> <output.json>", file=sys.stderr)
        sys.exit(1)

    corpus_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not corpus_dir.is_dir():
        print(f"Error: {corpus_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    index = build_index(corpus_dir)

    # Stats
    print(f"Files: {index['file_count']}", file=sys.stderr)
    print(f"Years: {len(index['temporal'])}", file=sys.stderr)
    print(f"Table codes: {len(index['table_codes'])}", file=sys.stderr)
    print(f"Keywords: {len(index['keywords'])}", file=sys.stderr)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(index, f, separators=(',', ':'))

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Output: {output_path} ({size_mb:.2f} MB)", file=sys.stderr)


if __name__ == "__main__":
    main()
