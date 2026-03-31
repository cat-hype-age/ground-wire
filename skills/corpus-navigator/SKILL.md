---
name: corpus-navigator
description: Quick dispatch table, anti-spiral recovery, and OCR traps for Treasury Bulletin corpus navigation.
---

# Corpus Navigator

## Topic → Where to Start

Quick-dispatch table. Find your topic, get the action.

| I need... | Table/section | Which bulletins | Search tip |
|-----------|--------------|-----------------|------------|
| National defense spending | FFO-3 / "Expenditures" | FY-end bulletins (Oct-Dec post-76, Jul-Sep pre-76) | `grep -l "national defense" treasury_bulletin_YYYY_*.txt` |
| Income tax receipts | FFO-2 / "Receipts by Source" | FY-end bulletins | `grep -l "individual income" treasury_bulletin_YYYY_*.txt` |
| Total public debt | FD-1 / "Debt Outstanding" | Any month — reported monthly | `grep -l "FD-1\|Debt Outstanding" treasury_bulletin_YYYY_*.txt` |
| Debt composition (bills vs bonds) | FD-2 / PDO-1 | Any month | `grep -l "FD-2\|Composition" treasury_bulletin_YYYY_*.txt` |
| Savings bonds data | Dedicated savings bond tables | Any month | `grep -l "Savings Bonds" treasury_bulletin_YYYY_*.txt` |
| Federal Reserve notes / money supply | MFS-1/2 / "Money in Circulation" | 2-3 months after reporting date | `grep -l "MFS\|Money in Circulation" treasury_bulletin_YYYY_*.txt` |
| International claims/liabilities | IFS / "Capital Movements" | Spring + Fall issues (post-83) | `grep -l "IFS\|Capital Movement" treasury_bulletin_YYYY_*.txt` |
| ESF balance sheet | ESF-1 | Quarterly issues | `grep -l "ESF\|Exchange Stabilization" treasury_bulletin_YYYY_*.txt` |
| Bank deposits | Banking sections | 2-3 months after reporting date | `grep -l "bank deposits\|banking" treasury_bulletin_YYYY_*.txt` |
| Gold/silver holdings | "Monetary Statistics" / ESF-1 | Any bulletin with monetary section | `grep -l "gold\|silver\|monetary" treasury_bulletin_YYYY_*.txt` |
| Criminal prosecution stats | Dedicated tables | FY-end bulletins | `grep -l "convicted\|prosecution" treasury_bulletin_YYYY_*.txt` |

---

## Anti-Spiral Protocol

**If you've searched 5+ files without finding the data, STOP.**

| Check | Common fix |
|-------|-----------|
| Fiscal year vs calendar year? | FY pre-76 ends June, post-76 ends Sept. CY ends Dec. |
| Right bulletin lag? | Data appears AFTER the period. Try later bulletins. |
| Right era for table codes? | Pre-1960s has no codes. Use section headers instead. |
| Terminology changed? | "Zaire" → "DR Congo" (1997). "Excise" vs "Internal revenue". |
| Quarterly gap? | Post-1983 only has 4 bulletins/year. Try adjacent quarter. |
| Too-specific keyword? | Try broader: "debt" instead of "marketable public debt securities". |
| Too-broad keyword? | Add year or table code to narrow results. |

### Terminology Shifts

| Modern term | Historical term | Transition |
|-------------|----------------|------------|
| Democratic Republic of Congo | Zaire | 1997 |
| Outlays | Expenditures | ~1970s |
| Fiscal year (Oct-Sep) | Fiscal year (Jul-Jun) | 1976 |
| Individual income taxes | Income tax | varies |
| Marketable securities | Public debt securities | varies |

---

## Known OCR Traps

When reading parsed tables, watch for:

- `nan` — empty cell, not the number
- `Unnamed: 0_level_0` — unlabeled index column from parsing
- `Piecil` — OCR misread of "Fiscal"
- `>` in headers — multi-level column separator, not data
- Stray pipes `|` mid-cell — column alignment artifact

**"Total" rows may include subcategories.** Always read the full row label. "Total" under "Convicted" is not the same as "Grand total."
