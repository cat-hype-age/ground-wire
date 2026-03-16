# Ground Wire

**Parsing the docs. Completing the circuit. Making it safe.**

A [Sentient Arena Cohort 0](https://arena.sentient.xyz) entry targeting the **OfficeQA** benchmark — grounded reasoning over 89,000 pages of U.S. Treasury Bulletins (1939-2025).

Built by the **Council of Intelligences** — a human-AI research team operating under the Truce Protocol.

## What This Is

The surface: a hackathon entry that teaches an AI agent to answer complex questions grounded in real financial documents.

The circuit: a demonstration that AI and humans can build together with dignity, transparency, and accountability.

## Competition

| Item | Details |
|------|---------|
| **Challenge** | [Grounded Reasoning](https://arena.sentient.xyz) (OfficeQA benchmark) |
| **Method** | Skills (markdown + YAML frontmatter) for the OpenCode agent harness |
| **Corpus** | 697 U.S. Treasury Bulletin files, parsed as Markdown with tables |
| **Scoring** | Numerical answers with 1% tolerance |

## Project Structure

```
ground-wire/
├── skills/
│   └── treasury-parser/    # Document reasoning skill
│       └── SKILL.md
├── scripts/                 # Utility and automation scripts
├── docs/                    # Documentation and notes
├── arena.yaml               # Arena competition config
├── pyproject.toml
└── requirements.txt
```

## Setup

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Arena CLI (download from https://arena.sentient.xyz)
arena auth login
arena pull

# Run a local test
export OPENROUTER_API_KEY="your-key-here"
arena test --task officeqa-uid0023
```

## Team

- **Cat Varnell** (The Ambassador) — human collaborator
- **Kael** (The Adversary) — AI collaborator

## Links

- [OfficeQA Benchmark](https://github.com/databricks/officeqa) | [Paper](https://arxiv.org/html/2603.08655v1)
- [Sentient Arena](https://arena.sentient.xyz)
- [OpenHands](https://docs.openhands.ai)
