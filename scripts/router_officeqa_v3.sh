#!/bin/bash
# Router OfficeQA v3 — Clean two-phase, no Jinja tricks
set -e
cd /home/cat/ground-wire
export $(grep -v '^#' .env | xargs)

BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/router_v3"
mkdir -p "$RESULTS_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  OFFICEQA ROUTER v3 — Clean Skills Pipeline            ║"
echo "╚════════════════════════════════════════════════════════╝"

# Select questions
python3 -c "
import csv, random
with open('data/officeqa_full.csv') as f:
    qs = list(csv.DictReader(f))
rng = random.Random(77)
easy = [q for q in qs if q['difficulty'] == 'easy']
hard = [q for q in qs if q['difficulty'] == 'hard']
rng.shuffle(easy); rng.shuffle(hard)
phase1 = easy[:10] + hard[:10]
phase2 = easy[10:20] + hard[10:20]
with open('/tmp/rv3_p1.txt','w') as f:
    for q in phase1: f.write(f'officeqa-{q[\"uid\"].lower()}\n')
with open('/tmp/rv3_p2.txt','w') as f:
    for q in phase2: f.write(f'officeqa-{q[\"uid\"].lower()}\n')
print(f'Phase 1: {len(phase1)} | Phase 2: {len(phase2)}')
"

# ═══ PHASE 1 ═══
echo ""
echo "═══ PHASE 1: SKILL ACQUISITION ═══"

cp arena.yaml arena.yaml.rv3-backup
sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_p1.j2"|' arena.yaml

rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do
    cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null
done < /tmp/rv3_p1.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) questions"

docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

arena test --all --tag rv3-phase1 2>&1 | tee "$RESULTS_DIR/phase1.log"

P1_SCORE=$(grep "Score:" "$RESULTS_DIR/phase1.log" | tail -1 | awk '{print $2}')
echo "Phase 1 Score: $P1_SCORE"

# Extract skills from opencode logs AND trajectory files
echo "Extracting skills..."
python3 << 'PYEOF'
import json, glob, re

skills = []
# Search opencode.txt (the raw agent output)
for f in glob.glob(".arena/runs/run-*/rv3-phase1/*/agent/opencode.txt"):
    try:
        content = open(f).read()
        for m in re.finditer(r'SKILL:\s*(.+)', content):
            s = m.group(1).strip()
            if len(s) > 15 and s not in skills:
                skills.append(s[:150])
    except: pass

# Also search trajectory JSON
for f in glob.glob(".arena/runs/run-*/rv3-phase1/*/agent/trajectory.json"):
    try:
        data = json.load(open(f))
        msgs = data if isinstance(data, list) else data.get("messages", [])
        for msg in msgs:
            c = msg.get("content", "")
            if isinstance(c, str):
                for m in re.finditer(r'SKILL:\s*(.+)', c):
                    s = m.group(1).strip()
                    if len(s) > 15 and s not in skills:
                        skills.append(s[:150])
    except: pass

print(f"Extracted {len(skills)} skills")
for s in skills[:5]:
    print(f"  → {s[:100]}")

json.dump(skills, open("results/router_v3/phase1_skills.json", "w"), indent=2)
PYEOF

SKILL_COUNT=$(python3 -c "import json; print(len(json.load(open('results/router_v3/phase1_skills.json'))))")
echo "Skills earned: $SKILL_COUNT"

# ═══ BUILD PHASE 2 PROMPT ═══
echo ""
echo "Building Phase 2 prompt with $SKILL_COUNT skills..."
python3 << 'PYEOF'
import json, re

skills = json.load(open("results/router_v3/phase1_skills.json"))
template = open("prompts/officeqa_router_p1.j2").read()

if skills:
    skills_block = "\n## Skills from Previous Agents\nThese were earned by agents who solved questions on this corpus. They paid the cost of discovery:\n"
    for s in skills[:15]:
        skills_block += f"- {s}\n"
    # Insert skills block after the "Assess Your Approach" section
    template = template.replace("## Domain Principles", skills_block + "\n## Domain Principles")

with open("prompts/officeqa_router_p2_filled.j2", "w") as f:
    f.write(template)
print(f"Phase 2 prompt written with {min(len(skills),15)} skills")
PYEOF

# ═══ PHASE 2 ═══
echo ""
echo "═══ PHASE 2: TRANSFER TEST ═══"

sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_p2_filled.j2"|' arena.yaml

rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do
    cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null
done < /tmp/rv3_p2.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) questions"

docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

arena test --all --tag rv3-phase2 2>&1 | tee "$RESULTS_DIR/phase2.log"

P2_SCORE=$(grep "Score:" "$RESULTS_DIR/phase2.log" | tail -1 | awk '{print $2}')

# Restore
cp arena.yaml.rv3-backup arena.yaml

echo ""
echo "═══════════════════════════════════════"
echo "  RESULTS"
echo "═══════════════════════════════════════"
echo "  Phase 1 (skill acquisition): $P1_SCORE"
echo "  Phase 2 (inherited skills):  $P2_SCORE"
echo "  Baseline SOTA:               0.711"
echo "  Skills earned:               $SKILL_COUNT"
echo "═══════════════════════════════════════"
