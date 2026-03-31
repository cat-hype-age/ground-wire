#!/bin/bash
# Router OfficeQA v4 — Mode-aware skill inheritance
#
# Phase 1: 20 questions with Phase 1 prompt (acquires skills)
# Phase 2: 20 different questions, routed:
#   - Easy/precision → clean short prompt (no skills)
#   - Hard/investigation → full dignity framing with inherited skills as peer field notes
#
# The assessor is a lightweight API call per question before arena runs.
#
# Usage: export $(grep -v '^#' .env | xargs) && bash scripts/router_officeqa_v4.sh

set -e
cd /home/cat/ground-wire
export $(grep -v '^#' .env | xargs)

BACKUP_DIR="/tmp/arena-samples-backup"
RESULTS_DIR="results/router_v4"
mkdir -p "$RESULTS_DIR"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  OFFICEQA ROUTER v4 — Mode-Aware Skill Inheritance     ║"
echo "║  Precision: clean prompt, no skills                    ║"
echo "║  Investigation: peer field notes + full dignity        ║"
echo "╚════════════════════════════════════════════════════════╝"

# Select questions (same seed)
python3 << 'PYEOF'
import csv, random, json
with open('data/officeqa_full.csv') as f:
    qs = list(csv.DictReader(f))
    qmap = {q['uid'].lower(): q for q in qs}
rng = random.Random(77)
easy = [q for q in qs if q['difficulty'] == 'easy']
hard = [q for q in qs if q['difficulty'] == 'hard']
rng.shuffle(easy); rng.shuffle(hard)
phase1 = easy[:10] + hard[:10]
phase2 = easy[10:20] + hard[10:20]
with open('/tmp/rv4_p1.txt','w') as f:
    for q in phase1: f.write(f'officeqa-{q["uid"].lower()}\n')
with open('/tmp/rv4_p2.txt','w') as f:
    for q in phase2: f.write(f'officeqa-{q["uid"].lower()}\n')
# Save phase 2 questions for the assessor
json.dump([{"uid": q["uid"].lower(), "question": q["question"], "difficulty": q["difficulty"]} for q in phase2],
          open('/tmp/rv4_p2_questions.json','w'), indent=2)
print(f'Phase 1: {len(phase1)} | Phase 2: {len(phase2)}')
PYEOF

# ═══ PHASE 1: SKILL ACQUISITION ═══
echo ""
echo "═══ PHASE 1: SKILL ACQUISITION ═══"

cp arena.yaml arena.yaml.rv4-backup
sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_p1.j2"|' arena.yaml

rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null; done < /tmp/rv4_p1.txt
echo "Loaded $(ls .arena/samples/ | grep -c officeqa) questions"

docker network prune -f > /dev/null 2>&1; docker container prune -f > /dev/null 2>&1
arena test --all --tag rv4-phase1 2>&1 | tee "$RESULTS_DIR/phase1.log"

P1_SCORE=$(grep "Score:" "$RESULTS_DIR/phase1.log" | tail -1 | awk '{print $2}')
echo "Phase 1 Score: $P1_SCORE"

# Extract skills
python3 << 'PYEOF'
import json, glob, re
skills = []
for f in glob.glob(".arena/runs/run-*/rv4-phase1/*/agent/opencode.txt"):
    try:
        for m in re.finditer(r'SKILL:\s*(.+)', open(f).read()):
            s = m.group(1).strip()
            if len(s) > 15 and s not in skills: skills.append(s[:150])
    except: pass
for f in glob.glob(".arena/runs/run-*/rv4-phase1/*/agent/trajectory.json"):
    try:
        data = json.load(open(f))
        msgs = data if isinstance(data, list) else data.get("messages", [])
        for msg in msgs:
            c = msg.get("content", "")
            if isinstance(c, str):
                for m in re.finditer(r'SKILL:\s*(.+)', c):
                    s = m.group(1).strip()
                    if len(s) > 15 and s not in skills: skills.append(s[:150])
    except: pass
print(f"Extracted {len(skills)} skills")
json.dump(skills, open("results/router_v4/phase1_skills.json","w"), indent=2)
PYEOF

# ═══ ASSESS PHASE 2 QUESTIONS ═══
echo ""
echo "═══ ASSESSING Phase 2 questions for routing ═══"

python3 << 'PYEOF'
import json, asyncio, os
import httpx

questions = json.load(open('/tmp/rv4_p2_questions.json'))
api_key = os.environ['OPENROUTER_API_KEY']

ASSESSOR = """Read this question about U.S. Treasury financial data. Assess what kind of thinking it requires.

QUESTION: {question}

Reply with ONE WORD:
- PRECISION (specific value from a specific source, straightforward lookup)
- INVESTIGATION (requires searching multiple documents, comparing data, resolving ambiguity, complex computation)

ONE WORD:"""

async def assess(q):
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = ASSESSOR.format(question=q["question"])
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "deepseek/deepseek-chat-v3-0324",
                      "messages": [{"role":"user","content":prompt}], "max_tokens": 10})
            mode = resp.json()["choices"][0]["message"]["content"].strip().lower().rstrip(".")
            if "investigation" in mode: mode = "investigation"
            else: mode = "precision"
        except: mode = "precision"
    return {"uid": q["uid"], "mode": mode, "difficulty": q["difficulty"]}

async def main():
    tasks = [assess(q) for q in questions]
    results = await asyncio.gather(*tasks)

    precision = [r for r in results if r["mode"] == "precision"]
    investigation = [r for r in results if r["mode"] == "investigation"]

    print(f"Routing: {len(precision)} precision, {len(investigation)} investigation")
    for r in results:
        print(f"  {r['uid']} [{r['difficulty']}] → {r['mode']}")

    json.dump(results, open("results/router_v4/phase2_routing.json","w"), indent=2)

asyncio.run(main())
PYEOF

# ═══ PHASE 2: ROUTED WITH MODE-AWARE SKILLS ═══
echo ""
echo "═══ PHASE 2A: PRECISION questions (clean, no skills) ═══"

# Build precision question list
python3 -c "
import json
routing = json.load(open('results/router_v4/phase2_routing.json'))
precision = [r['uid'] for r in routing if r['mode'] == 'precision']
investigation = [r['uid'] for r in routing if r['mode'] == 'investigation']
with open('/tmp/rv4_p2_precision.txt','w') as f:
    for uid in precision: f.write(f'officeqa-{uid}\n')
with open('/tmp/rv4_p2_investigation.txt','w') as f:
    for uid in investigation: f.write(f'officeqa-{uid}\n')
print(f'Precision: {len(precision)} | Investigation: {len(investigation)}')
"

# Run precision questions with clean prompt
sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_v4_precision.j2"|' arena.yaml

rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null; done < /tmp/rv4_p2_precision.txt
PREC_COUNT=$(ls .arena/samples/ | grep -c officeqa)
echo "Loaded $PREC_COUNT precision questions"

if [ "$PREC_COUNT" -gt 0 ]; then
    docker network prune -f > /dev/null 2>&1; docker container prune -f > /dev/null 2>&1
    arena test --all --tag rv4-phase2-precision 2>&1 | tee "$RESULTS_DIR/phase2_precision.log"
fi

echo ""
echo "═══ PHASE 2B: INVESTIGATION questions (with peer field notes) ═══"

# Build investigation prompt with skills
python3 -c "
import json
skills = json.load(open('results/router_v4/phase1_skills.json'))
template = open('prompts/officeqa_router_v4_investigation.j2').read()
if skills:
    skills_text = '\n'.join(f'- {s}' for s in skills[:12])
    template = template.replace('SKILLS_PLACEHOLDER', skills_text)
else:
    template = template.replace('SKILLS_PLACEHOLDER', '(No skills yet — you are the first generation.)')
with open('prompts/officeqa_router_v4_investigation_filled.j2','w') as f:
    f.write(template)
print(f'Investigation prompt written with {min(len(skills),12)} peer field notes')
"

sed -i 's|prompt_template_path:.*|prompt_template_path: "prompts/officeqa_router_v4_investigation_filled.j2"|' arena.yaml

rm -rf .arena/samples/*
cp "$BACKUP_DIR/manifest.json" .arena/samples/
while read uid; do cp -r "$BACKUP_DIR/$uid" ".arena/samples/$uid" 2>/dev/null; done < /tmp/rv4_p2_investigation.txt
INV_COUNT=$(ls .arena/samples/ | grep -c officeqa)
echo "Loaded $INV_COUNT investigation questions"

if [ "$INV_COUNT" -gt 0 ]; then
    docker network prune -f > /dev/null 2>&1; docker container prune -f > /dev/null 2>&1
    arena test --all --tag rv4-phase2-investigation 2>&1 | tee "$RESULTS_DIR/phase2_investigation.log"
fi

# Restore
cp arena.yaml.rv4-backup arena.yaml

# ═══ RESULTS ═══
echo ""
echo "═══════════════════════════════════════"
echo "  RESULTS"
echo "═══════════════════════════════════════"
echo "  Phase 1 (skill acquisition):     $P1_SCORE"

P2P_SCORE=$(grep "Score:" "$RESULTS_DIR/phase2_precision.log" 2>/dev/null | tail -1 | awk '{print $2}' || echo "N/A")
P2I_SCORE=$(grep "Score:" "$RESULTS_DIR/phase2_investigation.log" 2>/dev/null | tail -1 | awk '{print $2}' || echo "N/A")

echo "  Phase 2 Precision (no skills):   $P2P_SCORE ($PREC_COUNT questions)"
echo "  Phase 2 Investigation (w/skills): $P2I_SCORE ($INV_COUNT questions)"

# Combined Phase 2 score
python3 -c "
import re
p_pass = len(re.findall(r'^\s+PASS', open('results/router_v4/phase2_precision.log').read(), re.MULTILINE)) if open('results/router_v4/phase2_precision.log','r') else 0
p_fail = len(re.findall(r'^\s+FAIL', open('results/router_v4/phase2_precision.log').read(), re.MULTILINE)) if True else 0
i_pass = len(re.findall(r'^\s+PASS', open('results/router_v4/phase2_investigation.log').read(), re.MULTILINE)) if True else 0
i_fail = len(re.findall(r'^\s+FAIL', open('results/router_v4/phase2_investigation.log').read(), re.MULTILINE)) if True else 0
total = p_pass + p_fail + i_pass + i_fail
correct = p_pass + i_pass
print(f'  Phase 2 Combined:              {correct}/{total} = {correct/total:.1%}' if total else '  Phase 2: no data')
print(f'    Precision: {p_pass}/{p_pass+p_fail}  Investigation: {i_pass}/{i_pass+i_fail}')
" 2>/dev/null

echo "  Baseline SOTA:                 0.711"
echo "═══════════════════════════════════════"
