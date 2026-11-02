# RBI cash-usage residual: method and update components

Source article: Bhuyan, "Cash Usage in India: An Indicator", RBI Bulletin, 21 Oct 2024. https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx?Id=22933

## Definitions quoted from the article
- "The residual method subtracts the value of all non-cash payment instruments used in HC and estimates cash use as the residual."
- "Total PFCE minus the value of retail payments to merchants to purchase goods and services through digital mode used for PFCE (i.e., PFCE(digital)) can be used as an estimate for the residual HC, which is the value of cash payments for PFCE (i.e., PFCE(cash))."
- PFCE (MoSPI) is the household consumption measure; it includes NPISH.
- "PoS based payments are payments to merchants. However, payments to merchants through cards also happen outside 'PoS' and hence would be part of 'Others'... The entire data on 'wallet' are therefore assumed to be for payments to merchants. P2M of UPI, BHIM Aadhaar pay, [and] NETC are instruments used for payments to merchants."
- PFCE(digital)L (lower) = UPI P2M + BHIM Aadhaar Pay + NETC + credit card PoS + debit card PoS + PPI wallets + PPI cards PoS. PFCE(digital)U (upper) = L + card "Others" (credit, debit) + PPI cards "Others". (The formula images are not in the HTML; this is read from the text and Annex A and reproduced exactly, see validation.)
- Excluded as not separable into consumption payments: NEFT, IMPS, NACH, paper instruments, APBS, AePS fund transfers.
- Bounds: PFCE(cash)L = PFCE - PFCE(digital)U; PFCE(cash)U = PFCE - PFCE(digital)L. CU_L = 100 - DP_U, CU_U = 100 - DP_L (percent of PFCE).
- UPI P2M comes from NPCI (P2P/P2M split published by NPCI from April 2020 in our capture); everything else from RBI PSI.

## Published estimates (cash_residual_article_tables.csv)
- Jan-Mar 2024: cash share 51.9 to 59.9 per cent of PFCE.
- FY2023-24: 56.4 to 64.3 per cent (FY2022-23: 66.4 to 73.6; FY2021-22: 75.1 to 81.4). PFCE FY24 = Rs 178.2 lakh crore (2011-12 series, current prices).

## Our update (cash_residual_components.csv, cash_share_quarterly.csv)
- Monthly components Jun 2020 to Sep 2026, INR crore. PSI latest vintage per month (year-ago column of the release 12 months later, else prior-month column, else own month). Rows with all seven lower-bound components give pfce_digital_L/U.
- Validation: our FY2022-23 L/U = 43.4 / 55.2 lakh crore and FY2023-24 = 63.6 / 77.7 lakh crore, identical to Table 7 of the article. The numerator replicates exactly.
- Denominator break: quarterly shares divide by MoSPI PFCE current prices on the new 2022-23 base (data/macro/gdp_pfce_quarterly.csv), 2022-23 Q1 to 2026-27 Q1. This PFCE is lower than the 2011-12 series the article used (FY24: ~164 vs 178.2 lakh crore), so digital shares are higher than a like-for-like extension. Jan-Mar 2024 on the new base: 51.3 to 59.3 per cent vs article 51.9 to 59.9. Treat levels across the base change as approximate and use the article's own numbers for pre-2024 comparisons.
- Caveats: PSI is provisional; card "Others" includes non-merchant transfers (hence the upper bound); NETC is the "linked to bank account" PSI line (item 3.3); PSI card/PPI granularity starts Nov 2019; coverage of cooperative banks/LABs/RRBs in ATM data from Dec 2021 does not affect these components. NPCI edits past rows without notice.
- Latest quarter available: 2026-27 Q1 (PFCE published); Q2 (Jul-Sep 2026) components complete but PFCE not yet released.
