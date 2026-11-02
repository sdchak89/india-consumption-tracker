# Method

## Periods

- **Latest year** = October 2025 to September 2026, compared with the twelve months before. Earlier years run October to September too (Y22 = Oct 2021–Sep 2022).
- **FY** = April to March. National accounts and RBI payment statistics use FY.
- **Geography** compares Jul–Sep 2026 with Jul–Sep 2025.

## Formulas

| Measure | Formula |
|---|---|
| Growth | value this period ÷ value same period a year earlier − 1, on months published in both periods |
| Average payment | value ÷ number of payments |
| CAGR | (value last year ÷ value base year)^(1 ÷ years) − 1, on matched months. Base = the earliest year with at least 9 months matched to the latest year |
| Share of merchant UPI | category value ÷ all merchant value, same months |
| Contribution to the increase | value this year − value last year, for categories with at least 10 matched months; the residual is the total increase minus named categories |
| Consumption part of UPI growth | ln(1 + PFCE growth) ÷ ln(1 + merchant UPI growth) |
| Cash share of consumption | 1 − digital consumer payments ÷ PFCE |
| Break-adjusted growth (sensitivity) | last 12 months ÷ (pre-break months × (Sep 2025 ÷ Aug 2025) + post-break months of the earlier year) − 1 |
| Per resident | classified UPI value ÷ population ÷ months |
| State share change | 100 × ln(share this FY ÷ share last FY), share of classified UPI value |

PFCE is MoSPI's private final consumption expenditure in current prices, 2022-23 base (release of 31 August 2026).

## Cash share

Extends Bhuyan, "Cash Usage in India: An Indicator", RBI Bulletin, October 2024, and reproduces its FY23 and FY24 digital totals.

- **Digital, low estimate** = UPI merchant (P2M) + Aadhaar Pay + FASTag (NETC) + credit and debit card payments at shops + wallets + prepaid cards at shops.
- **Digital, high estimate** = low estimate + card and prepaid-card "other" payments.
- **Strict version** (used in the report) removes merchant UPI to brokers (MCC 6211), debt collection (7322), digital gold (5412) and credit-card bills (5413), which are financial flows, not consumption.
- Cash share range = 1 − high digital ÷ PFCE to 1 − low digital ÷ PFCE.

Levels across the 2022-23 base change are approximate: the new PFCE is lower than the 2011-12 series the RBI article used. See `data/rbi/CASH_METHOD.md`.

## Rounding

Every figure is computed at full precision and rounded once, for display. The scoreboard in `report.json` keeps four decimals; the page and the PDF round them.

## What this data can't tell us

- **Spending per person.** UPI adds users and merchants every month, so UPI per resident mixes adoption with spending.
- **Category by place.** NPCI doesn't publish categories by state or district.
- **Most of the growth.** NPCI's "Others" is 45% of merchant value and took 58% of last year's increase (66% including categories moving on or off NPCI's list).
- **Cause and effect.** Tax changes, rate moves and festival timing overlap, with no untouched comparison group. The verdicts are associations backed by several sources, not causal estimates.
- **Prices.** UPI figures are nominal. In a Jan–Aug 2026 test using approximate category CPI proxies, none of the 26 tested series changed sign.
- **Debt collection.** In September 2025 the value of MCC 7322 fell 37% in a month while payments fell 12%, and the average payment dropped from ₹5,083 to ₹3,630. NPCI announced no reclassification; the report treats it as a likely break and shows both reported and break-adjusted growth. Confirming it needs an NPCI mapping notice.
- **Geography.** UPI is attributed by payer address; about 39% of value has no state. District populations use 2011 census shares, so city levels are approximate.

## Checks

All 1,157 plotted values and every number in the text were checked against the raw files, primary sources or earlier checks. Values changed after review, and all 218 scoreboard fields, were then recomputed from raw data. `tests/test_report.py` rebuilds the dataset from `data/` and compares it with the published one.
