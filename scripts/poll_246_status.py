#!/usr/bin/env python3
"""Poll the 246 run and write status to a file for Slack reporting."""
import json
import sys
from pathlib import Path

RUN_DIR = Path("/home/cat/ground-wire/.arena/runs/run-20260329-071121-6e5acc/minimax-auditor-v1-full246-take3")
RESULT_FILE = RUN_DIR / "result.json"

if not RESULT_FILE.exists():
    print("NO_RESULTS")
    sys.exit(0)

d = json.load(open(RESULT_FILE))
finished = d.get("finished_at")

for k, v in d["stats"]["evals"].items():
    n = v["n_trials"]
    e = v["n_errors"]
    rs = v.get("reward_stats", {}).get("reward", {})
    p = len(rs.get("1.0", []))
    f = len(rs.get("0.0", []))
    m = v["metrics"][0]["mean"] if v.get("metrics") else 0

    status = "DONE" if finished else "RUNNING"
    print(f"{status}|{n}|246|{p}|{f}|{e}|{m:.1%}")
