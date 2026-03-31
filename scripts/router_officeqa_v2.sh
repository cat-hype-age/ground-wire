#!/bin/bash
# Router OfficeQA v2 — Fixed skill extraction from trajectories
#
# Phase 1: 20 questions, router prompt, extract skills from agent conversations
# Phase 2: 20 different questions, router prompt with inherited skills
#
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/router_officeqa_v2.sh

set -e
cd /home/cat/ground-wire

BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/router_v2"
mkdir -p "$RESULTS_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  OFFICEQA ROUTER v2 — Fixed Skills Pipeline            ║"
echo "╚════════════════════════════════════════════════════════╝"

# Select questions (same seed as v1 for comparability)
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
with open('/tmp/router_v2_phase1.txt','w') as f:
    for q in phase1: f.write(f'officeqa-{q[\"uid\"].lower()}\n')
with open('/tmp/router_v2_phase2.txt','w') as f:
    for q in phase2: f.write(f'officeqa-{q[\"uid\"].lower()}\n')
print(f'Phase 1: {len(phase1)} | Phase 2: {len(phase2)}')
"

# ═══ PHASE 1 ═══
echo ""
echo "═══ PHASE 1: SKILL ACQUISITION (no inherited skills) ═══"

# Write a Jinja template with empty skills for Phase 1
python3 -c "
template = open('prompts/officeqa_router_v2.j2').read()
# For Phase 1, skills list is empty so the skills block won't render
print('Phase 1 prompt ready (no skills)')
"

# Set arena to router prompt
cp arena.yaml arena.yaml.routerv2-backup
sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_v2.j2"|' arena.yaml

# Load Phase 1 questions
rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do
    cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null
done < /tmp/router_v2_phase1.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) Phase 1 questions"

docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

arena test --all --tag routerv2-phase1 2>&1 | tee "$RESULTS_DIR/phase1.log"

# Extract skills from trajectory files
echo ""
echo "Extracting skills from agent trajectories..."
python3 << 'PYEOF'
import json, glob, re

skills = []
for traj_file in glob.glob(".arena/runs/run-*/routerv2-phase1/*/agent/trajectory.json"):
    try:
        data = json.load(open(traj_file))
        # Search through all messages for SKILL: pattern
        messages = data if isinstance(data, list) else data.get("messages", data.get("trajectory", []))
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                for m in re.finditer(r'SKILL:\s*(.+)', content, re.IGNORECASE):
                    skill = m.group(1).strip()
                    if len(skill) > 15 and skill not in skills:
                        skills.append(skill[:150])
    except:
        pass

# Also check opencode.txt logs
for log_file in glob.glob(".arena/runs/run-*/routerv2-phase1/*/agent/opencode.txt"):
    try:
        content = open(log_file).read()
        for m in re.finditer(r'SKILL:\s*(.+)', content, re.IGNORECASE):
            skill = m.group(1).strip()
            if len(skill) > 15 and skill not in skills:
                skills.append(skill[:150])
    except:
        pass

print(f"Extracted {len(skills)} skills")
for s in skills[:5]:
    print(f"  → {s[:100]}")

# Save
with open("results/router_v2/phase1_skills.json", "w") as f:
    json.dump(skills, f, indent=2)
PYEOF

SKILL_COUNT=$(python3 -c "import json; print(len(json.load(open('results/router_v2/phase1_skills.json'))))")
echo "Skills saved: $SKILL_COUNT"

# ═══ PHASE 2 ═══
echo ""
echo "═══ PHASE 2: TRANSFER TEST (with $SKILL_COUNT inherited skills) ═══"

# Generate Phase 2 prompt with skills baked in
python3 << 'PYEOF'
import json

skills = json.load(open("results/router_v2/phase1_skills.json"))
template = open("prompts/officeqa_router_v2.j2").read()

# Replace the Jinja skills block with hardcoded skills
if skills:
    skills_block = "## Skills from Previous Agents\nThese were earned by agents who solved questions on this corpus:\n"
    for s in skills[:15]:
        skills_block += f"- {s}\n"
    # Replace the jinja block
    import re
    # Remove the jinja if/for/endfor/endif block and replace with static skills
    template = re.sub(r'\{%\s*if skills\s*%\}.*?\{%\s*endif\s*%\}', skills_block, template, flags=re.DOTALL)
else:
    template = re.sub(r'\{%\s*if skills\s*%\}.*?\{%\s*endif\s*%\}', '', template, flags=re.DOTALL)

with open("prompts/officeqa_router_v2_phase2.j2", "w") as f:
    f.write(template)
print(f"Phase 2 prompt written with {len(skills)} skills")
PYEOF

sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_v2_phase2.j2"|' arena.yaml

# Load Phase 2 questions
rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do
    cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null
done < /tmp/router_v2_phase2.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) Phase 2 questions"

docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

arena test --all --tag routerv2-phase2 2>&1 | tee "$RESULTS_DIR/phase2.log"

# Restore
cp arena.yaml.routerv2-backup arena.yaml

# Results
P1_SCORE=$(grep "Score:" "$RESULTS_DIR/phase1.log" | tail -1 | awk '{print $2}')
P2_SCORE=$(grep "Score:" "$RESULTS_DIR/phase2.log" | tail -1 | awk '{print $2}')

echo ""
echo "═══════════════════════════════════════"
echo "  RESULTS"
echo "═══════════════════════════════════════"
echo "  Phase 1 (skill acquisition): $P1_SCORE"
echo "  Phase 2 (inherited skills):  $P2_SCORE"
echo "  Baseline SOTA:               71.1%"
echo "  Skills earned:               $SKILL_COUNT"
echo "═══════════════════════════════════════"
