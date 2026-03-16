---
name: memory-learner
description: Use persistent memory to learn from each question. Store observations about document structure, data locations, and successful strategies. Recall relevant memories before starting new questions.
---

# Memory-Augmented Learning

You have access to a persistent memory system via MCP tools. Use it to build cumulative knowledge about the Treasury Bulletin corpus.

## Before Searching the Corpus

Call `recall` with keywords from the question to check if you already know:
- Which file contains the relevant data
- What table structure to expect
- What unit conventions apply
- What pitfalls to watch for

Example: Before searching for "defense expenditure" data, call:
```
recall(query="defense expenditure")
```

## After Answering Each Question

Store what you learned using `remember`. Good things to remember:

### Data Locations
```
remember(
    content="Total intergovernmental transfers for FY1938 found in prose paragraph, not a table, in August 1939 bulletin",
    category="data_location",
    tags="intergovernmental,transfers,1938,1939",
    source_file="treasury_bulletin_1939_08.txt"
)
```

### Table Structures
```
remember(
    content="Expenditures by Classes table has columns: Classification, then pairs of (This month, Fiscal year to date) for current and prior year",
    category="table_structure",
    tags="expenditures,table,format",
    source_file="treasury_bulletin_1941_01.txt"
)
```

### Search Strategies
```
remember(
    content="For ESF balance sheet data, grep for 'Exchange Stabilization Fund' — found in December quarterly bulletins",
    category="search_strategy",
    tags="ESF,balance sheet,search"
)
```

### Corrections
```
remember(
    content="1939 bulletins report in millions, not billions — always check the unit line above each table",
    category="correction",
    tags="units,millions,1939"
)
```

## Memory Categories

Use these categories for consistent retrieval:
- `data_location` — where specific data lives in the corpus
- `table_structure` — how tables are formatted in specific bulletins
- `search_strategy` — grep patterns and search approaches that worked
- `unit_convention` — unit/denomination patterns by era or table type
- `correction` — mistakes to avoid, things that tripped you up
- `computation_pattern` — how to compute specific metrics (CAGR, Theil index, etc.)
