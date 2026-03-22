#!/bin/bash
# Post-reboot recovery script for Ground Wire
# Run this after any system restart to restore all services
#
# Usage: bash /home/cat/ground-wire/scripts/post_reboot_recovery.sh

set -e
cd /home/cat/ground-wire

echo "=== GROUND WIRE POST-REBOOT RECOVERY ==="
echo "  Time: $(date)"

# 1. Export env vars
echo "  [1/6] Loading environment..."
export $(grep -v '^#' .env | xargs)

# 2. Fix arena CLI shebang if needed
ARENA_BIN="$HOME/.arena/venv/bin/arena"
if [ -f "$ARENA_BIN" ]; then
    FIRST_LINE=$(head -1 "$ARENA_BIN")
    if [[ "$FIRST_LINE" != *"/home/cat/.arena/venv/bin/python"* ]]; then
        echo "  Fixing arena CLI shebang..."
        sed -i "1s|.*|#!/home/cat/.arena/venv/bin/python|" "$ARENA_BIN"
    fi
fi
echo "  [1/6] Environment loaded"

# 3. Restore arena samples from backup (or regenerate)
echo "  [2/6] Checking arena samples..."
SAMPLES_DIR=".arena/samples"
BACKUP_DIR="/tmp/arena-samples-backup"

if [ ! -d "$BACKUP_DIR" ] || [ "$(ls $BACKUP_DIR 2>/dev/null | wc -l)" -lt 200 ]; then
    echo "  Backup missing — pulling original samples and regenerating..."
    arena pull 2>/dev/null || true

    # Regenerate 226 samples from CSV
    python3 << 'PYEOF'
import csv, os, shutil, json
from pathlib import Path

SAMPLES_DIR = Path(".arena/samples")
CSV_PATH = Path("data/officeqa_full.csv")

template_uid = None
for d in SAMPLES_DIR.iterdir():
    if d.is_dir() and (d / "tests" / "evaluate.py").exists():
        template_uid = d.name
        break

if not template_uid:
    print("  ERROR: No template sample found")
    exit(1)

template_dir = SAMPLES_DIR / template_uid

with open(CSV_PATH) as f:
    questions = list(csv.DictReader(f))

existing = set(d.name for d in SAMPLES_DIR.iterdir() if d.is_dir())
generated = 0

for q in questions:
    uid = q["uid"]
    sample_name = f"officeqa-{uid.lower()}"
    if sample_name in existing:
        continue

    sample_dir = SAMPLES_DIR / sample_name
    shutil.copytree(template_dir, sample_dir)
    (sample_dir / "instruction.md").write_text(q["question"] + "\n")

    toml = (sample_dir / "task.toml").read_text()
    toml = toml.replace(f'source_id = "{template_uid.replace("officeqa-","").upper()}"', f'source_id = "{uid}"')
    lines = [l for l in toml.split("\n") if "source_files" not in l and "source_docs" not in l]
    (sample_dir / "task.toml").write_text("\n".join(lines))

    (sample_dir / "solution" / "solve.sh").write_text(f'#!/bin/bash\necho "{q["answer"]}" > /app/answer.txt\n')

    config = {
        "uid": uid,
        "question": q["question"],
        "expected_answer": q["answer"],
        "difficulty": q.get("difficulty", ""),
        "tolerance": 0.01,
        "source_docs": [s.strip() for s in q.get("source_docs", "").split(",") if s.strip()],
        "source_files": [s.strip() for s in q.get("source_files", "").split(",") if s.strip()],
    }
    (sample_dir / "tests" / "config.json").write_text(json.dumps(config, indent=2))
    generated += 1

print(f"  Generated {generated} samples. Total: {len(list(SAMPLES_DIR.iterdir()))}")
PYEOF

    # Backup
    cp -r "$SAMPLES_DIR" "$BACKUP_DIR"
    echo "  Samples regenerated and backed up"
else
    echo "  Backup found ($BACKUP_DIR)"
    # Restore samples from backup if needed
    if [ "$(ls $SAMPLES_DIR 2>/dev/null | wc -l)" -lt 200 ]; then
        rm -rf "$SAMPLES_DIR"
        cp -r "$BACKUP_DIR" "$SAMPLES_DIR"
        echo "  Samples restored from backup"
    fi
fi

# 4. Clean Docker
echo "  [3/6] Cleaning Docker..."
docker network prune -f > /dev/null 2>&1 || true
docker container prune -f > /dev/null 2>&1 || true

# 5. Verify scoring pipeline
echo "  [4/6] Verifying scoring pipeline..."
python3 -c "
import json
from pathlib import Path
backup = Path('/tmp/arena-samples-backup')
broken = 0
for d in backup.iterdir():
    cfg = d / 'tests' / 'config.json'
    if cfg.exists():
        data = json.loads(cfg.read_text())
        if 'expected_answer' not in data:
            broken += 1
if broken:
    print(f'  WARNING: {broken} samples missing expected_answer!')
else:
    print('  Scoring pipeline verified — all samples have expected_answer')
"

# 6. Check batch eval state
echo "  [5/6] Checking batch eval state..."
python3 -c "
import json, glob
batches = glob.glob('results/full_eval/full246-b*.json')
if batches:
    tp = sum(int(json.load(open(f)).get('passed',0)) for f in batches)
    t = tp + sum(int(json.load(open(f)).get('failed',0)) for f in batches)
    print(f'  Valid results: {tp}/{t} = {tp/t*100:.1f}% ({len(batches)} batches, {246-t} remaining)')
else:
    print('  No batch results found — starting fresh')
"

# 7. Restore crontab
echo "  [6/6] Restoring cron jobs..."
crontab /home/cat/ground-wire/scripts/crontab.txt 2>/dev/null && echo "  Crontab restored" || echo "  Crontab file not found"

echo ""
echo "=== RECOVERY COMPLETE ==="
echo "  To resume batch eval: cd /home/cat/ground-wire && export \$(grep -v '^#' .env | xargs) && BATCH_SIZE=5 bash scripts/batch_eval.sh &"
echo "  To check status: python3 -c \"import json,glob; batches=glob.glob('results/full_eval/full246-b*.json'); print(len(batches),'batches')\""
