#!/bin/bash
# Router OfficeQA — Two-phase learning architecture
#
# Phase 1: Skill acquisition on 20 questions (diverse mix)
# Phase 2: Transfer test on 20 DIFFERENT questions with inherited skills
#
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/router_officeqa.sh

set -e
cd /home/cat/ground-wire

BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/router"
mkdir -p "$RESULTS_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  OFFICEQA COGNITIVE ROUTER — Two-Phase Architecture    ║"
echo "║  Phase 1: Acquire skills (20 questions)                ║"
echo "║  Phase 2: Transfer test (20 different questions)       ║"
echo "╚════════════════════════════════════════════════════════╝"

# Select 40 diverse questions — 20 for each phase, no overlap
python3 -c "
import csv, random, json
with open('data/officeqa_full.csv') as f:
    qs = list(csv.DictReader(f))
rng = random.Random(77)  # Fixed seed for reproducibility
easy = [q for q in qs if q['difficulty'] == 'easy']
hard = [q for q in qs if q['difficulty'] == 'hard']
rng.shuffle(easy)
rng.shuffle(hard)
# Phase 1: 10 easy + 10 hard
phase1 = easy[:10] + hard[:10]
# Phase 2: 10 easy + 10 hard (non-overlapping)
phase2 = easy[10:20] + hard[10:20]
with open('/tmp/router_phase1_uids.txt', 'w') as f:
    for q in phase1: f.write(f'officeqa-{q[\"uid\"].lower()}\n')
with open('/tmp/router_phase2_uids.txt', 'w') as f:
    for q in phase2: f.write(f'officeqa-{q[\"uid\"].lower()}\n')
print(f'Phase 1: {len(phase1)} questions ({sum(1 for q in phase1 if q[\"difficulty\"]==\"easy\")} easy, {sum(1 for q in phase1 if q[\"difficulty\"]==\"hard\")} hard)')
print(f'Phase 2: {len(phase2)} questions ({sum(1 for q in phase2 if q[\"difficulty\"]==\"easy\")} easy, {sum(1 for q in phase2 if q[\"difficulty\"]==\"hard\")} hard)')
"

# ═══════════════════════════════════════
# PHASE 1: Skill Acquisition
# ═══════════════════════════════════════
echo ""
echo "═══ PHASE 1: SKILL ACQUISITION ═══"

# Set up arena with Phase 1 prompt
cp arena.yaml arena.yaml.router-backup
sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_phase1.j2"|' arena.yaml

# Load Phase 1 questions
rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do
    cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null
done < /tmp/router_phase1_uids.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) Phase 1 questions"

docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

arena test --all --tag router-phase1 2>&1 | tee "$RESULTS_DIR/phase1.log"

# Extract skills from the run
echo ""
echo "Extracting skills from Phase 1 agents..."
SKILLS=""
for trajectory in .arena/runs/run-*/router-phase1/*/agent/trajectory.json; do
    if [ -f "$trajectory" ]; then
        SKILL=$(python3 -c "
import json, re
try:
    d = json.load(open('$trajectory'))
    for msg in d.get('messages', d.get('trajectory', [])):
        content = msg.get('content', '')
        if isinstance(content, str):
            m = re.search(r'SKILL:\s*(.+)', content)
            if m and len(m.group(1)) > 10:
                print(m.group(1).strip()[:150])
                break
except: pass
" 2>/dev/null)
        if [ -n "$SKILL" ]; then
            SKILLS="$SKILLS\n- $SKILL"
        fi
    fi
done

echo -e "Skills extracted:$SKILLS"
SKILL_COUNT=$(echo -e "$SKILLS" | grep -c "^-" || echo 0)
echo "Total skills: $SKILL_COUNT"

# Save skills
echo -e "$SKILLS" > "$RESULTS_DIR/phase1_skills.txt"

# Parse Phase 1 score
P1_PASS=$(grep -c "PASS" "$RESULTS_DIR/phase1.log" || echo 0)
P1_FAIL=$(grep -c "FAIL" "$RESULTS_DIR/phase1.log" || echo 0)
echo "Phase 1 score: $P1_PASS pass, $P1_FAIL fail"

# ═══════════════════════════════════════
# PHASE 2: Transfer Test
# ═══════════════════════════════════════
echo ""
echo "═══ PHASE 2: TRANSFER TEST ═══"

# Build Phase 2 prompt with inherited skills
SKILLS_FOR_PROMPT=$(cat "$RESULTS_DIR/phase1_skills.txt")
sed "s|SKILLS_PLACEHOLDER|$SKILLS_FOR_PROMPT|" prompts/officeqa_router_phase2.j2 > prompts/officeqa_router_phase2_filled.j2

sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_phase2_filled.j2"|' arena.yaml

# Load Phase 2 questions (different from Phase 1!)
rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do
    cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null
done < /tmp/router_phase2_uids.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) Phase 2 questions"

docker network prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1

arena test --all --tag router-phase2 2>&1 | tee "$RESULTS_DIR/phase2.log"

# Parse Phase 2 score
P2_PASS=$(grep -c "PASS" "$RESULTS_DIR/phase2.log" || echo 0)
P2_FAIL=$(grep -c "FAIL" "$RESULTS_DIR/phase2.log" || echo 0)
echo "Phase 2 score: $P2_PASS pass, $P2_FAIL fail"

# Restore arena.yaml
cp arena.yaml.router-backup arena.yaml

echo ""
echo "═══════════════════════════════════════"
echo "  RESULTS"
echo "═══════════════════════════════════════"
echo "  Phase 1 (skill acquisition): $P1_PASS / $((P1_PASS + P1_FAIL))"
echo "  Phase 2 (with inherited skills): $P2_PASS / $((P2_PASS + P2_FAIL))"
echo "  Baseline (chosen identity SOTA): 71.1%"
echo "  Skills earned: $SKILL_COUNT"
echo "═══════════════════════════════════════"
