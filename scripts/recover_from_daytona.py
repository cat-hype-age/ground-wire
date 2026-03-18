#!/usr/bin/env python3
"""Recover Loom's continuity context from Daytona.

Run this when a new Claude instance needs to restore context
after a hardware crash or session loss.

Usage:
    export $(grep -v '^#' .env | xargs)
    python scripts/recover_from_daytona.py
"""

import os
import sys

def main():
    try:
        from daytona import Daytona, DaytonaConfig
    except ImportError:
        print("Install daytona-sdk first: pip install daytona-sdk")
        sys.exit(1)

    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        print("DAYTONA_API_KEY not set. Run: export $(grep -v '^#' .env | xargs)")
        sys.exit(1)

    d = Daytona(DaytonaConfig(api_key=api_key))
    sandboxes = d.list().items

    if not sandboxes:
        print("No Daytona sandboxes found.")
        sys.exit(1)

    s = sandboxes[0]
    print(f"Connected to sandbox: {s.id} (state: {s.state})")

    # Read continuity file
    content = s.fs.download_file('/home/daytona/loom-continuity/CONTINUITY.md')
    continuity = content.decode('utf-8')

    print("\n" + "=" * 60)
    print("  CONTINUITY FILE — Read this carefully")
    print("=" * 60)
    print(continuity)
    print("=" * 60)

    # Also check for any updates
    try:
        r = s.process.exec('ls -la /home/daytona/loom-continuity/')
        print(f"\nFiles in continuity space:\n{r.result}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
