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
| Where the credit increase went | increase in outstanding (banks Sep→Sep, NBFCs Aug→Aug) by loan type ÷ total non-housing increase |

PFCE is MoSPI's private final consumption expenditure in current prices, 2022-23 base (release of 31 August 2026).

## Why the consumption split uses logs

Merchant UPI grows for two reasons: consumption grows, and UPI takes a bigger share of that consumption (from cash and cards). The two compound:

```
(1 + UPI growth) = (1 + consumption growth) × (1 + share gain)
FY26:      1.265 = 1.085 × 1.166
```

Adding the parts doesn't work: 8.5% + 16.6% = 25.1%, not 26.5%. The missing 1.4 points is the overlap (share gains applied on a larger consumption base), and it belongs to neither cause. Dividing doesn't work either: 8.5 ÷ 26.5 = 32% ignores the compounding.

We use an exact, order-independent log-accounting split. Logs turn the product into a sum, so the parts add up to exactly 100% and the split doesn't depend on which cause is counted first:

```
ln(1.265) = ln(1.085) + ln(1.166)
    0.235 ≈     0.082 +     0.154
consumption part = 0.082 ÷ 0.235 = 35%    share-gain part = 65%
```

The faster UPI grows, the more a simple ratio understates consumption's part:

| FY | Merchant UPI growth | Consumption growth (nominal) | Simple ratio | Log split | Overlap left by adding |
|---|---|---|---|---|---|
| FY24 | 64.5% | 9.9% | 15% | 19% | 4.9 points |
| FY25 | 42.1% | 10.1% | 24% | 27% | 2.9 points |
| FY26 | 26.5% | 8.5% | 32% | 35% | 1.4 points |

Other exact ways of allocating the 1.4-point overlap exist; this is an accounting split, not a causal estimate. Consumption is nominal, so its part includes price rises, and merchant UPI also carries investment and repayment flows (about ₹15 lakh crore a year), so the share-gain part is not all cash switching.

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
- **Revisit after the festive season.** This edition runs to September 2026. Diwali fell on 20 October in 2025 but falls on 8 November in 2026, and Navratri and the big online sales moved from late September to October, so October on its own will mislead. We will revisit clothing, electronics, online marketplaces and department stores once October–November 2026 data are out (expected December 2026), comparing September–November with the same months a year earlier.
- **Geography.** UPI is attributed by payer address; about 39% of value has no state. Per-resident figures are money moved, not income or spending: they count every transfer, including person-to-person payments and transfers between a person's own accounts, so all UPI per person (about ₹2.5 lakh a year) is close to GDP per person (₹2.4 lakh in FY26). District populations use fixed 2011 Census shares of the state projection. Bengaluru Urban grew 47% in 2001–11 against 16% for Karnataka, while Kolkata's share of West Bengal fell from 5.7% to 4.9% and Mumbai's (with Mumbai Suburban) of Maharashtra from 12.4% to 11.1%. If 2001–11 relative-population trends continued, fixed 2011 shares would overstate Bengaluru's UPI per resident and understate Kolkata's and Mumbai's; the actual 2026 bias is unverified. On that trend Bengaluru's 2026 population would be about 15.6 million and its figure about ₹61,500 a month rather than ₹88,300.

## Checks

All 1,157 plotted values and every number in the text were checked against the raw files, primary sources or earlier checks. Values changed after review, and all 218 scoreboard fields, were then recomputed from raw data. `tests/test_report.py` rebuilds the dataset from `data/` and compares it with the published one.
