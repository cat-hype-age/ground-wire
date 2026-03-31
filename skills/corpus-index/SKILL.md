---
name: corpus-index
description: Pre-built index of 697 Treasury Bulletin files. Maps years to filenames, table codes to content, and topics to search strategies. Use this BEFORE grepping to navigate directly to the right file and table.
---

# Corpus Index

Pre-built index of all 697 Treasury Bulletin files at `/app/corpus/`. Use this to navigate directly — don't waste iterations guessing filenames or grepping blindly.

## File Naming Convention

All files: `treasury_bulletin_YYYY_MM.txt`

**Coverage: 1939-2025 (697 files)**

| Era | Years | Frequency | Months available |
|-----|-------|-----------|-----------------|
| Monthly | 1939-1982 | 12/year | 01 through 12 |
| Quarterly | 1983-2025 | 4/year | 03, 06, 09, 12 |

**Exceptions:** 1944 missing month 07. 1982 missing month 12. 2025 only has 03, 06, 09.

**To construct a filename:** `treasury_bulletin_{year}_{month:02d}.txt`
- Example: September 2011 → `treasury_bulletin_2011_09.txt`
- Example: January 1970 → `treasury_bulletin_1970_01.txt`

## Fiscal Year Routing

When a question asks about a fiscal year, you need to know which bulletin carries the annual summary.

| Period | FY ends | Annual summary bulletin |
|--------|---------|------------------------|
| FY 1939-1976 | June 30 | Look in the **September** or **December** bulletin of the FY year |
| Transition (1976) | Sept 30 | `treasury_bulletin_1976_12.txt` |
| FY 1977-present | Sept 30 | Look in the **December** bulletin of the FY year, or **March** of the next year |

**Example:** FY 2011 data → check `treasury_bulletin_2011_12.txt` first, then `treasury_bulletin_2012_03.txt`.
**Example:** FY 1965 data → check `treasury_bulletin_1965_09.txt` or `treasury_bulletin_1965_12.txt`.

## Complete Table Code Reference

### Fiscal Operations (FFO)

| Code | Content | Available |
|------|---------|-----------|
| FFO-1 | Summary of fiscal operations (receipts, outlays, surplus/deficit) | 1960s-2025 |
| FFO-2 | Budget receipts by source (income/corp/excise/customs) | 1939-2025 |
| FFO-3 | Budget outlays by agency | 1960s-2025 |
| FFO-4 | Receipts by source and outlays by function combined | 1960s-2010s |
| FFO-5 | Budget outlays by major function | 1960s-2000s |
| FFO-6 | Investment transactions of government accounts | 1960s-1990s |
| FFO-7 | Trust fund transactions | 1960s-1990s |
| FFO-8 | Selected accrual data / Treasurer accountability | 1960s-1990s |
| FFO-9 | Excise tax receipts detail | 1960s-1980s |

### Federal Debt (FD)

| Code | Content | Available |
|------|---------|-----------|
| FD-1 | Summary of federal debt (total outstanding) | 1960s-2025 |
| FD-2 | Debt held by public / interest rates | 1960s-2025 |
| FD-3 | Interest-bearing public debt / Government account series | 1960s-2025 |
| FD-4 | Maturity distribution of marketable debt | 1960s-2025 |
| FD-5 | Special public debt issues / nonmarketable | 1960s-2025 |
| FD-6 | Interest-bearing securities by government agencies | 1960s-2025 |
| FD-7 | Participation certificates / Treasury holdings | 1950s-2025 |
| FD-8 | Debt subject to statutory limitation | 1960s-1990s |
| FD-9 | Status and application of statutory limitation | 1960s-1990s |
| FD-10 | Treasury holdings of agency securities | 1960s-1990s |

### Public Debt Operations (PDO)

| Code | Content | Available |
|------|---------|-----------|
| PDO-1 | Maturity schedule of marketable debt / weekly bill offerings | 1950s-2025 |
| PDO-2 | Offerings of Treasury bills | 1950s-2025 |
| PDO-3 | New money financing through weekly bills | 1950s-2025 |
| PDO-4 | Offerings of marketable securities other than weekly bills | 1950s-2025 |
| PDO-5 | Unmatured marketable securities from advance refunding | 1960s-2000s |
| PDO-6 | Securities issued at premium or discount | 1960s-2000s |
| PDO-7 | Allotments by investor class | 1960s-2000s |
| PDO-8 | Disposition of marketable securities (most common table) | 1939-2025 |
| PDO-9 | Foreign series securities (nonmarketable) | 1960s-2000s |

### Ownership of Federal Securities (OFS)

| Code | Content | Available |
|------|---------|-----------|
| OFS-1 | Distribution by class of investor and type | 1960s-2025 |
| OFS-2 | Estimated ownership of public debt by private investors | 1960s-2025 |

### International (IFS, CM, ESF)

| Code | Content | Available |
|------|---------|-----------|
| IFS-1 | U.S. reserve assets (gold, convertible currencies) | 1960s-2025 |
| IFS-2 | U.S. liquid liabilities to foreigners | 1960s-2025 |
| IFS-3 | U.S. liquid liabilities to official foreign institutions | 1960s-2000s |
| IFS-4 | Nonmarketable bonds/notes to foreign governments | 1960s-2000s |
| IFS-5 | U.S. position in IMF | 1960s-1990s |
| CM-I-1..7 | Liabilities to foreigners reported by banks | 1960s-2010s |
| CM-II-1..7 | Claims on foreigners reported by banks | 1960s-2010s |
| CM-III-1..4 | Liabilities/claims reported by nonbanking enterprises | 1960s-2010s |
| CM-IV-1..7 | U.S. international transactions in long-term securities | 1960s-2010s |
| ESF-1 | Exchange Stabilization Fund balance sheet | 1960s-2010s |
| ESF-2 | ESF income and expense | 1960s-2010s |

### Other

| Code | Content | Available |
|------|---------|-----------|
| UST-1 | Status of the Account of the U.S. Treasury | 1960s-2025 |
| UST-2 | Elements of change in FR/TLN balances | 1960s-1990s |
| USCC-1/2 | Currency and coin outstanding and in circulation | 1990s-2025 |
| MS-1 | Money in circulation (older equivalent of USCC) | 1960s-1990s |
| SB-1..6 | Savings bonds (sales, redemptions, by series/state) | 1960s-1990s |

## Topic Routing Quick Reference

When you know the TOPIC but not the table code:

| Topic | Primary codes | Fallback grep |
|-------|--------------|---------------|
| Receipts, revenue, taxes | FFO-1, FFO-2 | `receipts\|revenue\|income tax` |
| Spending, outlays, defense | FFO-1, FFO-3, FFO-5 | `outlays\|expenditures\|defense` |
| Total debt, debt outstanding | FD-1 | `federal debt\|debt outstanding` |
| Debt composition, maturity | FD-2, FD-4, PDO-1 | `maturity\|composition\|marketable` |
| Debt limit, statutory | FD-8, FD-6 | `statutory\|debt limit\|subject to` |
| Treasury bills, auctions | PDO-1, PDO-2, PDO-4 | `offerings\|treasury bills\|auction` |
| Who owns the debt | OFS-1, OFS-2 | `ownership\|investors\|holdings` |
| Gold, reserves, IMF | IFS-1, IFS-5 | `gold\|reserve assets\|IMF` |
| Foreign liabilities | IFS-2, CM-I | `liabilities to foreigners\|foreign` |
| Capital flows, banks | CM-I through CM-IV | `capital movements\|claims on foreigners` |
| ESF, stabilization fund | ESF-1, ESF-2 | `exchange stabilization\|ESF` |
| Currency in circulation | USCC-1, MS-1 | `currency\|coin\|circulation` |
| Savings bonds | SB-1 through SB-6 | `savings bonds\|series E\|series H` |
| Trust funds | FFO-7 | `trust fund` |

## Navigation Protocol

1. **Read the question** — extract: time period, topic, units, format
2. **Determine the file** — use the year/month table above to construct the filename
3. **Determine the table code** — use the topic routing table
4. **Grep to confirm:**
   ```bash
   grep -n "TABLE_CODE" /app/corpus/treasury_bulletin_YYYY_MM.txt | head -5
   ```
5. **Read the table** — use the line number from grep to read surrounding lines:
   ```bash
   sed -n 'LINE,+50p' /app/corpus/treasury_bulletin_YYYY_MM.txt
   ```
6. **Verify units** — check the header line above the table for "(In millions of dollars)" etc.
7. **Extract and compute** — read the specific cell, convert units if needed
