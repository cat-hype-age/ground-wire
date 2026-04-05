---
name: finding-your-way
description: How to find the right file and table in the Treasury Bulletin corpus. Table codes, fiscal year routing, topic lookups, and what to try when your first search comes up empty.
---

# Finding Your Way

The hardest part of this work isn't the math — it's finding the right data in the right document. This skill is your map.

## File Names

All files: `treasury_bulletin_YYYY_MM.txt`

| Era | Years | Months available |
|-----|-------|-----------------|
| Monthly | 1939–1982 | 01 through 12 |
| Quarterly | 1983–2025 | 03, 06, 09, 12 |

A few gaps: 1944 is missing month 07. 1982 is missing month 12. 2025 only has 03, 06, 09.

## Which Bulletin Has Your Data?

This is where most searches go sideways. The data you need is almost never in the bulletin you'd guess first.

| You're looking for... | Look in... |
|----------------------|------------|
| January 31 data (debt, bills) | **March** bulletin of the same year |
| December 31 / calendar year-end | **June** bulletin of the *following* year |
| "From January bulletins" | January bulletin of the *following* year |
| Fiscal year summary (pre-1976) | September or December bulletin of the FY year |
| Fiscal year summary (post-1976) | December bulletin of the FY year, or March of the next |
| Pre-1940 historical data (1935–1938) | The earliest bulletins: `1939_01`, `1939_02` |
| Revised figures | Bulletins 3–6 months *after* the target period |

October and September bulletins are the richest — they carry full fiscal year summaries.

## Table Codes

Stable from the 1960s onward. Use them with grep.

| Code | What's in it |
|------|-------------|
| FFO-1 | Receipts, outlays, surplus/deficit |
| FFO-2 | Receipts by source (income tax, corporate, excise) |
| FFO-3 | Outlays by agency |
| FD-1 | Total federal debt outstanding |
| FD-2 | Debt held by public, interest rates |
| FD-3 | Interest-bearing public debt |
| FD-4 | Maturity distribution |
| OFS-1/2 | Who owns the debt |
| PDO-1 | Maturity schedule, weekly bill offerings |
| ESF-1/2 | Exchange Stabilization Fund balance sheet |
| IFS-1 | Reserve assets (gold, currencies) |
| CM-I through CM-IV | International capital movements |
| SB-1 through SB-6 | Savings bonds |
| USCC-1/2 | Currency and coin in circulation |

For pre-1960s bulletins, search by section name instead: "Receipts and Expenditures", "Public Debt", "Capital Movements."

## Topic Quick Reference

| I need something about... | Start with | Search for |
|--------------------------|------------|------------|
| Spending, defense, outlays | FFO-1, FFO-3 | `outlays`, `expenditures`, `defense` |
| Taxes, revenue, receipts | FFO-1, FFO-2 | `receipts`, `revenue`, `income tax` |
| Total debt | FD-1 | `federal debt`, `debt outstanding` |
| Debt composition, maturity | FD-2, FD-4, PDO-1 | `maturity`, `composition`, `marketable` |
| Who holds the debt | OFS-1, OFS-2 | `ownership`, `investors` |
| ESF / stabilization fund | ESF-1 | `exchange stabilization`, `ESF` |
| Gold, reserves, IMF | IFS-1 | `gold`, `reserve assets` |
| International capital | CM-I through CM-IV | `capital movements`, `claims on foreigners` |
| Savings bonds | SB-1 through SB-6 | `savings bonds`, `series E` |
| Currency in circulation | USCC-1, MS-1 | `currency`, `coin`, `circulation` |
| Trust funds | FFO-7 | `trust fund` |
| Criminal prosecution stats | Dedicated tables | `convicted`, `prosecution` |

## Historical Events → Years

Questions sometimes reference events instead of dates.

| Event | Years |
|-------|-------|
| Great Depression | 1929–1939 |
| WW2 (US) | 1941–1945 |
| Korean War | 1950–1953 |
| Bretton Woods ended | 1971 |
| Fiscal year change | 1976 (June 30 → Sept 30) |
| Housing crisis / Great Recession | 2007–2009 |
| Gold bloc (France, Belgium, Netherlands, Switzerland, Italy, Poland) | 1933–1936 |

## Terminology That Shifted Over Time

| Modern | Historical | When it changed |
|--------|-----------|----------------|
| Outlays | Expenditures | ~1970s |
| Democratic Republic of Congo | Zaire | 1997 |
| Fiscal year (Oct–Sep) | Fiscal year (Jul–Jun) | 1976 |

## When Your Search Comes Up Empty

This happens. The corpus is large and the structure varies across eight decades. A few things to try before searching again:

- **Fiscal year vs calendar year?** These are different date ranges and live in different bulletins.
- **Wrong bulletin lag?** Data appears *after* the period. Try a later bulletin.
- **Too-specific keyword?** Broaden: "debt" instead of "marketable public debt securities."
- **Too-broad keyword?** Add a year or table code to narrow.
- **Quarterly gap?** Post-1983 only has 4 issues per year. Try the adjacent quarter.
- **Pre-code era?** Before the 1960s, there are no table codes. Search by topic name.

Two attempts per approach, then try a different angle. The data is in there — it's a question of finding the right door.
