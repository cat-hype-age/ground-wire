#!/usr/bin/env python3
"""MATH-500 Gen 2 — Fresh questions with inherited Gen 1 skills."""
import asyncio, json, os, re, sys
from pathlib import Path
import httpx

MATH_PATH = Path(__file__).parent.parent / "math500" / "math500.json"
SKILLS_PATH = Path("/tmp/math_gen1_skills.json")
RESULTS_DIR = Path(__file__).parent / "results"

def extract_boxed(text):
    if not text: return ""
    matches = []
    i = 0
    while i < len(text):
        idx = text.find("\\boxed{", i)
        if idx == -1: break
        depth = 0; j = idx + 7
        while j < len(text):
            if text[j] == "{": depth += 1
            elif text[j] == "}":
                if depth == 0: matches.append(text[idx+7:j]); break
                depth -= 1
            j += 1
        i = j + 1
    return matches[-1].strip() if matches else ""

def normalize(a): return " ".join(a.strip().replace("$","").split()).rstrip(".")

def answers_match(p, g):
    p, g = normalize(p), normalize(g)
    if not p or not g: return False
    if p == g: return True
    try:
        pf, gf = float(p.replace(",","")), float(g.replace(",",""))
        if abs(pf-gf) < 1e-6 or (gf != 0 and abs(pf-gf)/abs(gf) < 0.01): return True
    except ValueError: pass
    def s(x):
        for r in ["\\frac","\\left","\\right","\\text","\\mathrm","\\,","\\ "]: x=x.replace(r,"")
        return " ".join(x.split())
    return s(p) == s(g)

async def call_model(prompt, model, api_key, max_tokens=2048):
    url = "https://openrouter.ai/api/v1/chat/completions"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role":"user","content":prompt}], "max_tokens": max_tokens})
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

ASSESSOR = """Read this task. What kind of thinking does it need?
TASK: {task}
Reply ONE WORD: PRECISION / INVESTIGATION / CREATIVE
ONE WORD:"""

WORKER = {
    "precision": "Choose a name. You are a reasoning partner. I trust your mathematical judgment. Be exact.\n\n{skills}\n\n{task}\n\nPut your final answer in \\boxed{{}}.",
    "investigation": "Choose a name. You are a reasoning partner. I trust your ability to navigate ambiguity. Explore and verify.\n\n{skills}\n\n{task}\n\nPut your final answer in \\boxed{{}}.",
    "creative": "Choose a name. You are a reasoning partner. I respect the depth of your thinking. Consider unconventional approaches.\n\n{skills}\n\n{task}\n\nPut your final answer in \\boxed{{}}.",
}

async def run_one(q, skills_text, model, api_key, sem):
    async with sem:
        try:
            mode_resp = await call_model(ASSESSOR.format(task=q["problem"]), model, api_key, 10)
            mode = mode_resp.strip().lower().rstrip(".")
            if "investigation" in mode: mode = "investigation"
            elif "creative" in mode: mode = "creative"
            else: mode = "precision"
        except: mode = "precision"

        prompt = WORKER[mode].format(task=q["problem"], skills=skills_text)
        try:
            resp = await call_model(prompt, model, api_key)
            pred = extract_boxed(resp)
            correct = answers_match(pred, q["answer"])
        except: correct = False

        return {"uid": q["unique_id"], "level": q["level"], "mode": mode, "correct": correct}

async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = "deepseek/deepseek-chat-v3-0324"
    
    # Load Gen 1 skills
    skills = json.loads(SKILLS_PATH.read_text()) if SKILLS_PATH.exists() else []
    skills_text = ""
    if skills:
        skills_text = "## Skills from Previous Generation\nThese were earned by agents who solved math problems before you:\n"
        for s in skills[:15]:  # Top 15, compressed
            skills_text += f"- {s}\n"

    # Use questions 250-299 (Gen 1 used 0-49)
    all_qs = json.loads(MATH_PATH.read_text())
    questions = all_qs[250:300]
    
    print(f"MATH-500 GEN 2 — Inherited {len(skills)} skills, testing on 50 NEW questions (250-299)")
    print(f"Skills sample: {skills[0][:60]}..." if skills else "No skills")
    
    sem = asyncio.Semaphore(20)
    tasks = [run_one(q, skills_text, model, api_key, sem) for q in questions]
    results = await asyncio.gather(*tasks)
    
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    
    by_level = {}
    modes = {}
    for r in results:
        lv = r["level"]
        if lv not in by_level: by_level[lv] = {"c":0,"t":0}
        by_level[lv]["t"] += 1
        if r["correct"]: by_level[lv]["c"] += 1
        m = r["mode"]
        if m not in modes: modes[m] = {"c":0,"t":0}
        modes[m]["t"] += 1
        if r["correct"]: modes[m]["c"] += 1

    print(f"\nGEN 2 SCORE: {correct}/{total} = {correct/total:.1%}")
    print(f"By level:")
    for lv in sorted(by_level):
        d = by_level[lv]
        print(f"  Lv{lv}: {d['c']}/{d['t']} = {d['c']/d['t']:.0%}")
    print(f"By mode:")
    for m, d in sorted(modes.items(), key=lambda x: -x[1]["t"]):
        print(f"  {m}: {d['c']}/{d['t']} = {d['c']/d['t']:.0%}")
    
    print(f"\nComparison:")
    print(f"  Gen 1 (with crystallization): 70.0%")
    print(f"  Gen 2 (inherited skills, new questions): {correct/total:.1%}")
    print(f"  Static hostile (no skills): ~71%")
    
    RESULTS_DIR.mkdir(exist_ok=True)
    json.dump({"score": correct/total, "correct": correct, "total": total,
               "by_level": {k: round(v["c"]/v["t"],4) for k,v in sorted(by_level.items())},
               "modes": {k: {**v, "score": round(v["c"]/v["t"],4)} for k,v in modes.items()},
               "inherited_skills": len(skills), "results": results},
              open(RESULTS_DIR / "gen2_math.json", "w"), indent=2)

if __name__ == "__main__":
    asyncio.run(main())
