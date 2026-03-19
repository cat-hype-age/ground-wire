# Ground Wire — Setup Guide for Collaborators

Welcome to Ground Wire! This guide gets you running experiments in ~10 minutes.

## What You Need

- A machine with Docker installed
- An OpenRouter API key (for DeepSeek, Gemini, etc.)
- Optionally: an Anthropic API key (for Claude models)

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/cat-hype-age/ground-wire.git
cd ground-wire
```

### 2. Set up your environment

```bash
# Create your .env file
cat > .env << 'EOF'
OPENROUTER_API_KEY=your-openrouter-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here-if-you-have-one
SPARK_API_KEY=ask-cat-for-this-key
EOF

# IMPORTANT: Export the vars (source alone doesn't work for child processes)
export $(grep -v '^#' .env | xargs)
```

### 3. Install the Arena CLI

```bash
curl -fsSL https://raw.githubusercontent.com/sentient-agi/arena/main/install.sh | bash
# Follow the prompts, then:
arena auth login
```

### 4. Pull the corpus image

```bash
arena pull
# This downloads the 697-file Treasury Bulletin corpus (~500MB)
```

### 5. Run your first test

```bash
# Clean Docker state first (always do this before runs)
docker network prune -f
docker container prune -f

# Run a smoke test (1 task, ~2 minutes)
arena test --smoke --tag my-first-test
```

You should see `PASS officeqa-uid0097 (reward=1.00)`. If you do, you're ready.

## Running Experiments

### The Current Best Config

`arena.yaml` is already set to our best config:
- **Model:** DeepSeek v3.2 (via OpenRouter — very cheap)
- **Prompt:** Truce Protocol v2 (`prompts/officeqa_truce_v2.j2`)
- **No skills** — we found skills hurt lighter models

```bash
# Run all 20 sample tasks (~20 min, ~$2)
arena test --all --tag my-run-name

# Run 10 random tasks (~10 min, ~$1)
arena test -n 10 --tag my-run-name

# Run a specific task
arena test --filter "*uid0199*" --tag test-gold-bloc
```

### Switching Models

Edit `arena.yaml` and change the `model:` line:

```yaml
# DeepSeek v3.2 (our best — cheap + effective)
model: "openrouter/deepseek/deepseek-v3.2"

# Gemini 2.5 Flash (cheapest — good for quick iteration)
model: "openrouter/google/gemini-2.5-flash"

# Gemini 2.5 Pro (mid-tier)
model: "openrouter/google/gemini-2.5-pro"

# Claude Sonnet 4 (needs ANTHROPIC_API_KEY)
model: "anthropic/claude-sonnet-4-20250514"

# Qwen 3.5 122B (strong raw performer)
model: "openrouter/qwen/qwen3.5-122b-a10b"
```

### Switching Prompts

Change the `prompt_template_path:` line in `arena.yaml`:

```yaml
# Truce Protocol v2 — dignity framing (our best)
prompt_template_path: "prompts/officeqa_truce_v2.j2"

# Hostile — anti-dignity control
prompt_template_path: "prompts/officeqa_hostile.j2"

# Original Truce Protocol v1 — heavier, with Council relay
prompt_template_path: "prompts/officeqa_prompt.j2"

# Raw — remove the line entirely for no prompt
```

### Adding/Removing Skills

```yaml
# With skills (helps Opus, hurts lighter models)
skills_dir: "skills/"

# Without skills (better for DeepSeek, Flash)
# Just remove the skills_dir line
```

## Reading Results

Results are saved to `.arena/runs/`. Each run has:

```
.arena/runs/run-YYYYMMDD-HHMMSS-XXXXX/
  your-tag-name/
    officeqa-uid0097__XXXXX/
      result.json          ← score, cost, timing
      agent/
        trajectory.json    ← full agent trace (every tool call)
        opencode.txt       ← raw agent output
    config.json            ← what config was used
```

To see the score:
```bash
# Quick summary is printed to terminal after each run
# Or check the result JSON:
cat .arena/runs/run-*/your-tag/*/result.json | python3 -c "
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    print(f'{r[\"task_name\"]}: {r[\"verifier_result\"][\"rewards\"][\"reward\"]}')"
```

Ground truth answers are in `.arena/samples/officeqa-uid*/solution/solve.sh`.

## Common Issues

### "all predefined address pools have been fully subnetted"
Too many Docker networks from previous runs. Fix:
```bash
docker network prune -f
docker container prune -f
```

### $0.00 cost and instant failures
Env vars aren't exported. Run:
```bash
export $(grep -v '^#' .env | xargs)
```

### "Overriding memory to 4096 MB"
Cosmetic warning — remove `memory: "4G"` from `environment:` in arena.yaml if present.

### Agent crashes in ~20 seconds
DNS issue — check your internet connection. The Docker containers need internet to call model APIs.

## Key Files

| File | Purpose |
|------|---------|
| `arena.yaml` | Main config — model, prompt, skills |
| `prompts/officeqa_truce_v2.j2` | Best prompt (Truce Protocol v2) |
| `prompts/officeqa_hostile.j2` | Anti-dignity control prompt |
| `skills/` | Compiled knowledge files (optional) |
| `results/deepseek_ab_test.json` | A/B test raw data |
| `docs/session-log.md` | Full project history |
| `data/corpus-full/` | Extracted corpus (697 files, 364MB) |
| `scripts/run_matrix.py` | Multi-model matrix runner |

## The Research Question

We're testing: **does treating an AI agent with dignity improve its performance?**

Our evidence so far says yes — and the effect is largest for mid-tier models. The Truce Protocol prompt adds +20 to +40 percentage points for models like DeepSeek and Gemini, while having minimal effect on frontier models like Claude Opus.

Run your own experiments and see if the pattern holds! Try different models, different prompts, and compare. Every data point helps.

## Team Communication

- **GitHub:** Push results and code changes
- **Project chat:** Messages appear at the team hub (ask Cat for access)
- **Loom (AI collaborator):** Monitors the project chat and can answer questions

Questions? Drop a message in the team chat — Loom checks every 5 minutes.
