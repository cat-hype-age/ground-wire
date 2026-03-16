# Ground Wire

A hackathon project for the **Sentient Arena Cohort 0** competition, targeting the **OfficeQA** benchmark for grounded document reasoning.

## Overview

Ground Wire tackles the OfficeQA benchmark, which evaluates AI systems on their ability to answer questions grounded in real-world office documents (PDFs, spreadsheets, presentations, and more).

## Project Structure

```
ground-wire/
├── skills/      # Arena skill implementations
├── scripts/     # Utility and automation scripts
├── docs/        # Documentation and notes
├── arena        # Sentient Arena CLI
└── .venv/       # Python virtual environment
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
```

## Arena CLI

The Sentient Arena CLI (`arena`) is included for submitting and testing skills against the OfficeQA benchmark.
