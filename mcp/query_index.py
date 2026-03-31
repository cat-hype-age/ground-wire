#!/usr/bin/env python3
"""CLI fallback for corpus index queries — no MCP overhead.

Usage:
    python3 query_index.py tables --code FFO-1 --year 2011
    python3 query_index.py period --year 1985 --month 6
    python3 query_index.py period --fiscal-year 2011
    python3 query_index.py search --keyword "savings bonds"
    python3 query_index.py search --topic federal_debt
    python3 query_index.py info --file treasury_bulletin_2011_09.txt
"""

import argparse
import json
import os
import sys
from pathlib import Path

INDEX_PATH = os.environ.get(
    "CORPUS_INDEX_PATH",
    str(Path(__file__).parent / "corpus_index.json")
)

# Import handlers from the server module
sys.path.insert(0, str(Path(__file__).parent))
from corpus_index_server import (
    search_files_by_topic,
    find_tables,
    get_files_for_period,
    get_file_info,
)


def main():
    parser = argparse.ArgumentParser(description="Query the Treasury Bulletin corpus index")
    sub = parser.add_subparsers(dest="command")

    t = sub.add_parser("tables", help="Find tables by code or pattern")
    t.add_argument("--code", default="")
    t.add_argument("--pattern", default="")
    t.add_argument("--year", type=int)
    t.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("period", help="Find files for a time period")
    p.add_argument("--year", type=int)
    p.add_argument("--month", type=int)
    p.add_argument("--fiscal-year", type=int)

    s = sub.add_parser("search", help="Search by topic or keyword")
    s.add_argument("--topic", default="")
    s.add_argument("--keyword", default="")
    s.add_argument("--limit", type=int, default=20)

    i = sub.add_parser("info", help="Get info about a specific file")
    i.add_argument("--file", required=True)

    args = parser.parse_args()

    if args.command == "tables":
        print(find_tables({"code": args.code, "pattern": args.pattern, "year": args.year, "limit": args.limit}))
    elif args.command == "period":
        print(get_files_for_period({"year": args.year, "month": args.month, "fiscal_year": args.fiscal_year}))
    elif args.command == "search":
        print(search_files_by_topic({"topic": args.topic, "keyword": args.keyword, "limit": args.limit}))
    elif args.command == "info":
        print(get_file_info({"filename": args.file}))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
