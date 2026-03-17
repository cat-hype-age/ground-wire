---
name: pre-learned-knowledge
description: Knowledge accumulated from previous runs and corpus exploration. READ THIS before searching the corpus — it will prevent common mistakes and guide you to the right bulletins.
---

# Pre-Learned Knowledge Base

This knowledge was compiled from previous agents' experience with the Treasury Bulletin corpus. **Read it carefully before starting your search.** It will save you time and prevent known errors.


## Computation Patterns — How to Calculate

- **Percent change: (new - old) / old * 100. CAGR: (end/start)^(1/years) - 1. Geometric mean: (x1*x2*...*xn)^(1/n). Always use Python for complex math.**
  *(keywords: percent change,CAGR,geometric mean,formulas)*

- **Theil index: T = (1/n) * sum(xi/mean * ln(xi/mean)) where xi are individual values and mean is their average. Use Python.**
  *(keywords: theil index,dispersion,formula)*

- **Euclidean norm: sqrt(x1^2 + x2^2 + ... + xn^2). Used when question asks for the 'norm of absolute changes'.**
  *(keywords: euclidean norm,formula)*


## Known Traps — Mistakes to Avoid

- **TRAP: 'Total nominal capital' in ESF means Total Capital (capital account + net income), NOT just the Capital account. The Capital account is fixed at ~$200M.**
  *(keywords: ESF,nominal capital,trap)*

- **Gold bloc countries (1933-1936): France, Belgium, Netherlands, Switzerland, Italy, Poland. Later bulletins (1940+) may have DIFFERENT values for 1935 data due to revisions.**
  *(keywords: gold bloc,countries,1935)*

- **TRAP: 'Total public debt outstanding' does NOT include agency securities (FHA, etc.). For 'total gross federal debt', use the broader 'Total Federal securities outstanding' measure.**
  *(keywords: debt,public debt,agency,trap)*

- **TRAP: 'convicted AND found guilty' means the specific 'Found guilty' sub-column, NOT 'Total convicted' which includes 'Plead guilty'. Always map question phrases to the MOST SPECIFIC matching column.**
  *(keywords: question reading,sub-column,found guilty)*

- **ALWAYS write a numeric answer to /app/answer.txt. A wrong number might score 1.0 (1% tolerance). No number always scores 0. Never give up.**
  *(keywords: answer,surrender,mandatory)*


## Data Locations — Where Specific Data Lives

- **ESF (Exchange Stabilization Fund) balance sheet data is in quarterly bulletins under table code ESF-1. Total capital = Capital account + Net income (loss). Units are in THOUSANDS of dollars.**
  *(keywords: ESF,balance sheet,capital,thousands)*

- **International capital movement data for 1935 is in treasury_bulletin_1939_01.txt (January 1939 bulletin), page 49. This is the authoritative source for that era.**
  *(keywords: capital movement,1935,international,gold bloc)*

- **Total gross federal debt including agency securities: look for 'Total Federal securities outstanding' in Table OFS-1, NOT 'Total public debt outstanding' which excludes agency securities.**
  *(keywords: federal debt,gross,agency,OFS-1)*

- **Treasury bill breakdowns (regular weekly/annual vs tax anticipation) as of January 31: found in MARCH bulletins in the maturity schedule table (PDO-1 or similar).**
  *(keywords: treasury bills,maturity,PDO-1,january,march)*


## Search Strategy — Where to Find Data

- **January 31 data (e.g., debt outstanding as of Jan 31) is found in MARCH bulletins, NOT February. The February bulletin typically only has data through December of the prior month.**
  *(keywords: january,debt,timing,march)*

- **December 31 data (calendar year-end snapshots) is found in JUNE bulletins of the following year, NOT December. Table FO-1 'as of Dec. 31' appears in June issues.**
  *(keywords: december,calendar year,june,FO-1)*

- **When a question says 'from January bulletins', use the January bulletin of the FOLLOWING year. E.g., January 1970 bulletin contains January 1969 data.**
  *(keywords: january,bulletin,timing)*

- **Pre-1940 historical data (1935, 1936, etc.) is in the EARLIEST bulletins in the corpus (1939_01, 1939_02). These contain multi-year historical tables.**
  *(keywords: 1935,1936,historical,early)*

- **October/September bulletins contain full fiscal year summaries. These are the richest sources for annual data.**
  *(keywords: fiscal year,annual,october,september)*

- **Different bulletins may have DIFFERENT values for the same metric due to revisions. Earlier bulletins may have preliminary data; later ones have revised. Check which the question points to.**
  *(keywords: revisions,preliminary,revised)*


## Corpus Structure — How Documents Are Organized

- **CRITICAL STRUCTURAL BREAK IN 1983: Pre-1983 bulletins are MONTHLY (12/year). Post-1983 bulletins are QUARTERLY (4/year). Don't search for monthly data after 1983.**
  *(keywords: monthly,quarterly,1983,frequency)*

- **Post-1983 quarterly bulletins have seasonal content rotation: trust fund reports appear mainly in Fall issues, international capital data in Spring and Fall.**
  *(keywords: seasonal,quarterly,trust fund,international)*

- **Table codes (FFO-1, FD-1, etc.) are stable from the 1960s onward. Use them for grep. Pre-1960s bulletins use descriptive section names instead.**
  *(keywords: table codes,FFO,FD,grep)*

- **Reporting basis changed in 1955: interest on public debt switched from 'due and payable' to 'accrual' basis. Values before and after 1955 are NOT directly comparable.**
  *(keywords: reporting basis,1955,accrual,interest)*


## Unit Conventions — Watch the Denominations

- **Tables say '(In millions of dollars)' at the top. Questions may ask for billions: divide by 1000. Or raw dollars: multiply by 1,000,000.**
  *(keywords: millions,billions,conversion)*

- **ESF balance sheet units are in THOUSANDS of dollars, not millions. Convert carefully.**
  *(keywords: ESF,thousands,units)*
