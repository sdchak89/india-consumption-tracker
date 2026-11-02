# Data

All files were retrieved on 1 November 2026. Values are as published at that date; publishers revise past figures, sometimes without notice. Large files are gzipped (pandas reads them directly).

## NPCI (UPI)

npci.org.in refused scripted access on 1 November 2026, so NPCI's tables were taken from the archive at measure.thisindianlife.today, which mirrors NPCI's UPI ecosystem statistics. The merchant-category table was spot-checked against NPCI's own August 2025 table, and its P2M total equals NPCI's separate P2P/P2M table in every month.

| File | What it is |
|---|---|
| `npci/merchant_categories_monthly.csv` | UPI merchant payments by category (MCC), Jan 2021–Sep 2026. Value in ₹ crore, payments in million. NPCI lists only its top categories each month; other months are marked "Not separately published". `total` = all merchant (P2M) payments; `others` = NPCI's residual line |
| `npci/p2p_p2m_monthly.csv` | UPI person-to-person and person-to-merchant totals, from April 2020 (rupees, counts) |
| `npci/state_monthly.csv.gz` | UPI by state of the payer, from April 2023 |
| `npci/district_monthly.csv.gz` | UPI by district, from March 2026 |
| `npci/district_snapshot.csv` | District concordance to the 2011 census, metro clusters and 2026 population estimates (state projection × 2011 district share) |

## National accounts, payments, population

| File | Source |
|---|---|
| `macro/gdp_pfce_annual.csv`, `macro/gdp_pfce_quarterly.csv` | MoSPI National Accounts API, base 2022-23, release of 31 Aug 2026 (GDP, PFCE; current and constant prices) |
| `macro/atm_cash_withdrawals_monthly.csv`, `macro/card_spend_monthly.csv` | RBI Payment System Indicators |
| `macro/currency_annual_fy_end.csv` | RBI Handbook of Statistics on the Indian Economy, Table 36 (release of 31 Jul 2026) |
| `macro/size_ratios_fy.csv` | FY totals and ratios: GDP and PFCE (MoSPI), UPI and P2M (NPCI), ATM and card payments (RBI PSI), currency with the public (RBI) |
| `macro/state_population_projection.csv` | Report of the Technical Group on Population Projections 2011–2036, National Commission on Population, MoHFW (July 2020) |
| `macro/census_district_growth.csv` | Census of India 2001 and 2011 populations (Table A-2) for Bengaluru Urban, Kolkata, Mumbai, Mumbai Suburban and their states, used for the city population sensitivity |

## Credit, cash, tax, vehicles, fuel

| File | Source |
|---|---|
| `rbi/raw/SIBC30102026E.xlsx`, `rbi/raw/NBFCCREDIT06102026.xlsx` | The RBI workbooks as published: sectoral deployment of bank credit (30 Oct 2026 release) and NBFC sectoral credit (6 Oct 2026 release) |
| `rbi/consumer_credit_levels.csv` | Outstanding personal and retail loans by loan type, banks and NBFCs, at each date in the two workbooks (₹ crore), with the RBI row label. Used for the credit growth and for where the year's increase went |
| `rbi/credit_growth_prepost.csv` | Year-on-year growth of consumer credit by lender and loan type: RBI sectoral deployment of bank credit (30 Oct 2026 release) and RBI NBFC sectoral credit (6 Oct 2026 release) |
| `rbi/cash_residual_components.csv` | Monthly digital consumer-payment components, Jun 2020–Sep 2026, ₹ crore (RBI PSI; NPCI P2M) |
| `rbi/cash_share_quarterly.csv` | Quarterly digital totals, PFCE and cash share range |
| `rbi/cash_residual_article_tables.csv` | The published estimates in Bhuyan, RBI Bulletin, October 2024, used to validate the method |
| `rbi/CASH_METHOD.md` | Cash-share method, definitions and validation |
| `rbi/rupay_credit_card_on_upi.csv` | UPI payments on RuPay credit cards by financial year (Ministry of Finance reply to Rajya Sabha Q889, NPCI data; FY25 to October 2024) |
| `tax/state_income_tax.csv` | Positive-tax income-tax filers per 1,000 people by state (Ministry of Finance reply to Lok Sabha Question 946, 10 Feb 2025; all assessee types), with state UPI shares |
| `vahan/vahan_state_monthly.csv.gz` | Vehicle registrations by state, class and month (Vahan4 public dashboard) |
| `ppac/petroleum_consumption_monthly.csv` | Product-wise petroleum consumption (PPAC) |

## Company results, surveys, markets and prices

| File | What it is |
|---|---|
| `external/external_figures.csv` | Every figure the report takes from company results, RBI surveys, CPI and policy releases, industry bodies, market indices and gold-price reports: the period and value as published, the publisher and the source link. Measures differ (revenue, order value, same-store growth, volume), so rows are not comparable with each other |

## Rights

Each dataset belongs to its publisher and is redistributed here, with attribution, so the analysis can be reproduced. If you publish one of these datasets and would like it handled differently, please open an issue.
