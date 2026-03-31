#!/usr/bin/env python3
"""Generate all 246 OfficeQA samples from the CSV file."""
import csv
import json
import os
import shutil
from pathlib import Path

SAMPLES_DIR = Path("/home/cat/ground-wire/.arena/samples")
CSV_PATH = Path("/home/cat/ground-wire/officeqa_full.csv")

# Find a template sample
template_uid = None
for d in SAMPLES_DIR.iterdir():
    if d.is_dir() and (d / "tests" / "evaluate.py").exists():
        template_uid = d.name
        break

if not template_uid:
    print("ERROR: No template sample found. Run 'arena pull' first.")
    exit(1)

template_dir = SAMPLES_DIR / template_uid
print(f"Using template: {template_dir}")

# Read CSV
with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    questions = list(reader)

print(f"Found {len(questions)} questions in CSV")

existing = set(d.name for d in SAMPLES_DIR.iterdir() if d.is_dir())
generated = 0
skipped = 0

for q in questions:
    uid = q["uid"]
    sample_name = f"officeqa-{uid.lower()}"

    if sample_name in existing:
        skipped += 1
        continue

    sample_dir = SAMPLES_DIR / sample_name
    shutil.copytree(template_dir, sample_dir)

    # Write instruction
    (sample_dir / "instruction.md").write_text(q["question"] + "\n")

    # Update task.toml - replace source_id
    toml = (sample_dir / "task.toml").read_text()
    old_id = template_uid.replace("officeqa-", "").upper()
    toml = toml.replace(f'source_id = "{old_id}"', f'source_id = "{uid}"')
    (sample_dir / "task.toml").write_text(toml)

    # Write solution
    (sample_dir / "solution" / "solve.sh").write_text(
        f'#!/bin/bash\necho "{q["answer"]}" > /app/answer.txt\n'
    )

    # Write config.json
    source_docs = [s.strip() for s in q.get("source_docs", "").split("\n") if s.strip()]
    source_files = [s.strip() for s in q.get("source_files", "").split("\n") if s.strip()]

    config = {
        "uid": uid,
        "question": q["question"],
        "expected_answer": q["answer"],
        "difficulty": q.get("difficulty", ""),
        "tolerance": 0.01,
        "source_docs": source_docs,
        "source_files": source_files,
    }
    (sample_dir / "tests" / "config.json").write_text(json.dumps(config, indent=2))
    generated += 1

total = len(list(d for d in SAMPLES_DIR.iterdir() if d.is_dir()))
print(f"Generated {generated} new samples, skipped {skipped} existing")
print(f"Total samples: {total}")

# Verify expected_answer exists in all
broken = 0
for d in SAMPLES_DIR.iterdir():
    cfg = d / "tests" / "config.json"
    if cfg.exists():
        data = json.loads(cfg.read_text())
        if "expected_answer" not in data:
            broken += 1
if broken:
    print(f"WARNING: {broken} samples missing expected_answer!")
else:
    print("All samples have expected_answer ✓")
