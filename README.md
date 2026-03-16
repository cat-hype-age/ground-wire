# Ground Wire

A hackathon project for the **Sentient Arena Cohort 0** competition, targeting the **OfficeQA** benchmark for grounded document reasoning.

## Overview

Ground Wire tackles the OfficeQA benchmark, which evaluates AI systems on their ability to answer questions grounded in real-world office documents (PDFs, spreadsheets, presentations, and more).

## Project Structure

```
ground-wire/
├── skills/
│   └── officeqa/        # OfficeQA benchmark skill
│       ├── SKILL.md     # Skill definition & triggers
│       └── skill.py     # Agent implementation
├── scripts/             # Utility and automation scripts
├── docs/                # Documentation and notes
├── config.toml          # OpenHands configuration
├── requirements.txt     # Python dependencies
└── .venv/               # Python virtual environment
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## OpenHands SDK

This project uses the [OpenHands SDK](https://docs.openhands.dev/sdk/getting-started) (`openhands-ai`) to build and test document reasoning agents locally.

```python
from skills.officeqa.skill import create_officeqa_agent

agent = create_officeqa_agent({"model": "anthropic/claude-sonnet-4-20250514"})
```

## Arena CLI

The Sentient Arena CLI is used for submitting skills to the competition. Download it from the [Arena portal](https://arena.sentient.xyz) after logging in.
