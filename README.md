# Where is Indian consumption going?

What 69 months of UPI payments data say about how India spends, cross-checked against cash, bank credit, national accounts, vehicle registrations and company results.

**Soumyadeep Chakraborty** · November 2026 · data to September 2026

| | |
|---|---|
| **PDF briefing** (20 pages) | [docs/Where-is-Indian-consumption-going-Nov-2026.pdf](docs/Where-is-Indian-consumption-going-Nov-2026.pdf) |
| **Interactive report** (every chart has its data table) | [sdchak89.github.io/india-consumption-tracker](https://sdchak89.github.io/india-consumption-tracker/) |
| **Every published number, with its formula and source** | [report/data/numbers.csv](report/data/numbers.csv) |

## The short answer

1. **Merchant UPI is still growing about 25% a year, and the slowdown has levelled off.** ₹101.5 lakh crore in Oct 2025–Sep 2026, up 26.4%, from ₹23.0 lakh crore four years earlier.
2. **UPI's lead over consumption growth is narrowing.** Merchant UPI grew 26.5% in FY26 against 8.5% for consumption in rupees. The gap has shrunk from 50% (FY24) to 29% to 17%. Slower UPI growth ahead need not mean weaker demand.
3. **Cash's share of spending fell while cash balances kept rising.** Cash's estimated share of consumer spending fell from 70–78% (Apr–Jun 2022) to 39–48% (Apr–Jun 2026), yet cash held by the public rose 12% in FY26.
4. **Food is the engine.** Groceries are the largest named category (₹9.5 lakh crore). Fast food grew 108% a year for four years. Liquor-shop UPI is up 70% with an unchanged average payment.
5. **Vehicle buying and loan balances rebounded together** after the September 2025 GST cut: registrations +21–22%, NBFC consumer-durable loans +56%.
6. **Real consumption is growing; prices and confidence are the watch-points.** Real consumption grew 7.2% in FY26, while urban confidence fell and the RBI raised rates in October.

## Reproduce it

Everything in the report is rebuilt from the files in `data/`. A test checks that the rebuild matches the published dataset value for value.

```bash
pip install -r requirements.txt
python pipeline/run.py            # data/ -> build/report.json (every number the report plots)
python -m pytest tests            # rebuild and compare with report/data/report.json
python report/web/build_web.py    # -> docs/index.html, the interactive report
```

The PDF needs Node and Playwright's Chromium:

```bash
npm install && npx playwright install chromium
npm run pdf                       # -> build/briefing.pdf
```

Tested with Python 3.13, pandas 3.0 and numpy 2.5.

## What's where

```
data/                 inputs, as retrieved on 1 Nov 2026 (sources in data/README.md)
  npci/               UPI by merchant category, P2P/P2M, state and district
  macro/              MoSPI national accounts, RBI payments and currency, population
  rbi/                consumer credit levels and growth (raw RBI workbooks in rbi/raw/), cash-share components
  external/           company results, surveys, market and price figures, each with its source link
  tax/  vahan/  ppac/ taxpayers by state, vehicle registrations, fuel volumes
pipeline/             six steps, run in order by run.py
  s1_categories.py    category profiles: growth, CAGR, average payment, share
  s2_geography.py     per-resident UPI by state, city and metro cluster
  s3_core.py          yearly and monthly totals, basket, where the increase went, decomposition
  s4_tax_vehicles_credit.py   income-tax test, vehicles, credit
  s5_cash_geography.py        cash share of consumption, debt-collection break
  s6_assemble.py      scoreboard and panels; writes report.json and numbers.csv
report/
  data/               the published dataset (report.json, ticket_monthly.json, numbers.csv)
  web/                interactive report: template, charts, category cards
  deck/               PDF briefing: page builder, charts, renderer
docs/                 GitHub Pages: the interactive report and the PDF
tests/                rebuild check and headline numbers
```

## Method and limits

Definitions, formulas and limits are in [METHOD.md](METHOD.md). The main ones:

- **Growth** compares months published in both periods, because NPCI lists only its top categories each month.
- **Consumption part of UPI growth** = ln(1 + consumption growth) ÷ ln(1 + UPI growth), using MoSPI's private final consumption (PFCE). Logs, because the two sources of growth compound; we use an exact, order-independent log-accounting split. Worked example in [METHOD.md](METHOD.md#why-the-consumption-split-uses-logs).
- **Cash share** = 1 − digital consumer payments ÷ PFCE, extending Bhuyan, RBI Bulletin (October 2024).
- UPI figures are nominal rupees. ₹1 lakh crore = ₹1 trillion. FY = April–March.
- Per-resident figures are money moved through UPI (including person-to-person transfers), not income or spending. City populations are World Population Review's 2026 estimates, mostly metro areas wider than the districts NPCI reports; a Census-trend district estimate is kept for comparison.
- NPCI's "Others" line is 45% of merchant value and is not broken out. Category growth mixes new users and merchants with spending per person. Results are associations, not causal estimates.
- **Next update:** clothing, electronics, online marketplaces and department stores will be revisited once October–November 2026 data are out (expected December 2026). Diwali moved from 20 October (2025) to 8 November (2026), so October alone misleads; the update compares September–November with the same months a year earlier.

## Licence

- Code (`pipeline/`, `report/`, `tests/`): [MIT](LICENSE).
- The report, charts, text and derived data: [CC BY 4.0](LICENSE-CONTENT.md). Share and adapt freely, with credit.
- Source data belong to their publishers (NPCI, RBI, MoSPI, MoHFW, Vahan, PPAC, CBDT) and are redistributed here for reproducibility with attribution; see [data/README.md](data/README.md).

## Cite

> Chakraborty, Soumyadeep (2026). *Where is Indian consumption going?* India consumption briefing, November 2026. https://github.com/sdchak89/india-consumption-tracker

Corrections and questions are welcome as issues.
