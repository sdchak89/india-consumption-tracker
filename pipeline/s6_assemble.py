"""Step 6. Add the scoreboard, the category panels' monthly series, the food split and the raw
monthly table, then write build/report.json (every number the web page and the PDF plot) and
build/numbers.csv (each registered figure with its calculation and source)."""
import json
import pandas as pd
from common import BUILD, W, WL, isnan, load_npci, read_json, write_json

v, c, names = load_npci()
O = read_json("d3.json")
REG = read_json("reg3.json")
P = pd.read_csv(BUILD / "category_profiles.csv", dtype={"mcc": str}).set_index("mcc")

# ---- scoreboard: 28 selected categories, full precision, rounded once on display ----
SHORT = {
    "5411": "Groceries", "6211": "Securities brokers", "7322": "Debt collection (loan repayments) †",
    "5541": "Fuel stations", "4814": "Telecom", "4900": "Utilities", "5812": "Restaurants", "5814": "Fast food",
    "5912": "Pharmacies", "5732": "Electronics shops", "5691": "Men's & women's clothing",
    "9399": "Government services", "5921": "Liquor shops", "5262": "Online marketplaces", "5137": "Uniforms",
    "5651": "Family clothing", "5451": "Dairies", "5311": "Department stores", "5462": "Bakeries",
    "5422": "Meat shops", "4112": "Railways", "5331": "Variety stores", "5813": "Bars", "5441": "Confectionery",
    "5993": "Paan & cigarette shops", "7230": "Salons", "7622": "Electronics repair", "4121": "Taxis",
}


def r4(x):
    return None if isnan(x) else round(float(x), 4)


score = []
for m in sorted(SHORT, key=lambda m: (-round(P.loc[m, "val_26_cr"] / 1e5, 2), m)):  # displayed value, ties by MCC
    p = P.loc[m]
    yrs = p["years"]
    score.append(dict(
        mcc=m, n=SHORT[m], val=round(p["val_26_cr"] / 1e5, 2),
        yv=r4(p["yoy_v"]), yc=r4(p["yoy_c"]),            # value and payment growth, last year, matched months
        t0=r4(p["tkt_base"]), t1=r4(p["tkt_26_all"]),    # average payment (₹): base year (matched months) -> latest year (all months)
        cagr=r4(p["val_cagr"]), mk=r4(p["tot_cagr_same"]),  # category CAGR vs all merchant UPI, same months
        yrs=None if isnan(yrs) else int(yrs),
    ))
O["score"] = score

# ---- monthly series for the category panels ----
PANELS = ["5411", "5812", "5814", "5541", "5912", "6211", "7322", "5732", "5262", "5691", "5921", "4814"]
O["cardser"] = {
    m: [{"m": i.strftime("%Y-%m"), "v": None if isnan(v[m][i]) else round(float(v[m][i])),
         "c": None if isnan(c[m][i]) else round(float(c[m][i]), 1)} for i in v.loc["2022-01":].index]
    for m in PANELS
}

# ---- food at home (groceries) vs eating out (restaurants + fast food), ₹ lakh crore ----
foodY = []
for k, (a, b) in W.items():
    home = v["5411"].loc[a:b].sum()
    away = v[["5812", "5814"]].loc[a:b].sum().sum()
    foodY.append(dict(y=WL[k], home=round(home / 1e5, 2), away=round(away / 1e5, 2), share=O["foodshare"][k]))
O["foodY"] = foodY

# ---- the raw monthly table, as published (None = not separately published) ----
O["raw"] = {
    "months": [i.strftime("%Y-%m") for i in v.index],
    "cats": {m: {"n": names[m], "v": [None if isnan(x) else x for x in v[m]], "c": [None if isnan(x) else x for x in c[m]]}
             for m in v.columns},
}

# ---- context for the per-resident figures ----
# All UPI (classified + unclassified) per person, against GDP per person; and Bengaluru's figure if its
# population share kept rising at its 2001–11 pace (the 2011-share estimate understates fast-growing districts).
from common import DATA
st = pd.read_csv(DATA / "npci" / "state_monthly.csv.gz")
st = st[(st.metric == "value") & st.period.isin(["2026-07", "2026-08", "2026-09"])]
pop = pd.read_csv(DATA / "macro" / "state_population_projection.csv")
pop26 = pop[pop.year == 2026]
india_pop = pop26.population_persons.sum()
gdp = pd.read_csv(DATA / "macro" / "gdp_pfce_annual.csv").pivot_table(index="period", columns="series", values="value")
cen = pd.read_csv(DATA / "macro" / "census_district_growth.csv").set_index("area")
b01, b11 = cen.loc["Bangalore (Bengaluru Urban district)", ["census_2001", "census_2011"]]
k01, k11 = cen.loc["Karnataka", ["census_2001", "census_2011"]]
share26 = (b11 / k11) * ((b11 / k11) / (b01 / k01)) ** 1.5
kar26 = pop26.set_index("state").loc["Karnataka", "population_persons"]
dist = pd.read_csv(DATA / "npci" / "district_monthly.csv.gz")
blr = dist[(dist.metric == "value") & (dist.district == "Bengaluru (Urban)") & dist.period.isin(["2026-07", "2026-08", "2026-09"])].value.sum()
O["geo_context"] = dict(
    all_upi_pr_month=round(st.value.sum() / india_pop / 3),
    gdp_per_person_fy26=round(gdp.loc["2025-26", "GDP_current"] * 1e7 / india_pop),
    blr_pop_trend_mn=round(kar26 * share26 / 1e6, 1),
    blr_v_pr_month_trend=round(blr / (kar26 * share26) / 3),
)
REG.append(dict(id="geo_context", value=json.dumps(O["geo_context"]),
                calculation="all UPI incl. unclassified, Jul–Sep 2026 ÷ 2026 population ÷ 3; GDP FY26 current prices ÷ 2026 population; "
                            "Bengaluru 2026 share = 2011 share × (2011 share ÷ 2001 share)^1.5, × Karnataka 2026 projection",
                source="NPCI state and district tables; MoSPI NAS (31 Aug 2026); MoHFW projections; Census 2001 and 2011"))

# ---- RuPay credit cards on UPI as a share of merchant UPI (Rajya Sabha Q889, NPCI data via MoF) ----
cc = pd.read_csv(DATA / "rbi" / "rupay_credit_card_on_upi.csv")
cc = cc[cc.metric == "value"].set_index("period").value / 1e7          # ₹ crore
p2m = lambda a, b: v["total"].loc[a:b].sum()
O["cc_on_upi"] = dict(fy24=round(cc["FY 2023-24"] / p2m("2023-04", "2024-03") * 100, 1),
                      apr_oct_2024=round(cc["FY 2024-25"] / p2m("2024-04", "2024-10") * 100, 1))
REG.append(dict(id="cc_on_upi", value=json.dumps(O["cc_on_upi"]),
                calculation="RuPay credit card UPI value ÷ merchant UPI value, FY24 (Apr 2023–Mar 2024) and Apr–Oct 2024 (first seven months of FY25)",
                source="Ministry of Finance reply to Rajya Sabha Q889 (NPCI data); NPCI merchant category table"))

# ---- 2001–11 population-share change of the other metro cores (direction of the 2011-share bias) ----
sh = lambda a, s, y: cen.loc[a, y] / cen.loc[s, y] * 100
O["metro_share_2001_2011"] = {
    "Bengaluru": [round(sh("Bangalore (Bengaluru Urban district)", "Karnataka", y), 2) for y in ["census_2001", "census_2011"]],
    "Kolkata": [round(sh("Kolkata", "West Bengal", y), 2) for y in ["census_2001", "census_2011"]],
    "Mumbai": [round((cen.loc["Mumbai", y] + cen.loc["Mumbai Suburban", y]) / cen.loc["Maharashtra", y] * 100, 2)
               for y in ["census_2001", "census_2011"]],
}
REG.append(dict(id="metro_share_2001_2011", value=json.dumps(O["metro_share_2001_2011"]),
                calculation="district population ÷ state population × 100, Census 2001 and 2011 (Mumbai = Mumbai + Mumbai Suburban)",
                source="Census of India 2011, Table A-2 (data/macro/census_district_growth.csv)"))

# ---- where the year's increase in non-housing consumer credit went (banks Sep→Sep, NBFCs Aug→Aug) ----
lv = pd.read_csv(DATA / "rbi" / "consumer_credit_levels.csv")
lv = lv.pivot_table(index=["lender", "line"], columns="date", values="outstanding_inr_crore", aggfunc="first")
d_bank = lv.loc["bank", "2026-09-30"] - lv.loc["bank", "2025-09-19"]
d_nbfc = lv.loc["nbfc", "2026-08-31"] - lv.loc["nbfc", "2025-08-31"]
bank_other = d_bank["personal_total"] - d_bank[["housing", "vehicle", "consumer_durables", "education", "credit_cards", "gold"]].sum()
nbfc_other = d_nbfc["retail_total"] - d_nbfc[["housing", "vehicle", "gold", "consumer_durables"]].sum()
parts = [("Vehicle", d_bank["vehicle"], d_nbfc["vehicle"]),
         ("Consumer durables", d_bank["consumer_durables"], d_nbfc["consumer_durables"]),
         ("Education", d_bank["education"], 0.0),
         ("Credit cards", d_bank["credit_cards"], 0.0),
         ("Gold loans", d_bank["gold"], d_nbfc["gold"]),
         ("Personal and other", bank_other, nbfc_other)]
tot_inc = sum(b + n for _, b, n in parts)
O["credit_split"] = dict(
    total_lakh_cr=round(tot_inc / 1e5, 2),
    rows=[dict(line=k, bank_cr=round(float(b)), nbfc_cr=round(float(n)), lakh_cr=round((b + n) / 1e5, 2),
               share=round((b + n) / tot_inc * 100, 1)) for k, b, n in parts])
REG.append(dict(id="credit_split", value=json.dumps(O["credit_split"], ensure_ascii=False),
                calculation="increase in outstanding: banks 19 Sep 2025 → 30 Sep 2026, NBFCs 31 Aug 2025 → 31 Aug 2026; housing excluded; "
                            "personal and other = bank personal loans minus housing, vehicle, durables, education, cards and gold "
                            "+ NBFC retail loans minus housing, vehicle, gold and durables",
                source="RBI SIBC 30 Oct 2026 and NBFC sectoral credit 6 Oct 2026 (data/rbi/consumer_credit_levels.csv, data/rbi/raw/)"))

# ---- figures from outside NPCI and the official datasets (company results, surveys, markets) ----
ext = pd.read_csv(DATA / "external" / "external_figures.csv", dtype=str).fillna("")
O["external"] = ext[["id", "measure", "earlier_period", "earlier_value", "latest_period", "latest_value", "unit", "publisher"]].to_dict("records")
for r in ext.itertuples():
    late = f"{r.latest_value} ({r.latest_period})"
    REG.append(dict(id="ext_" + r.id, value=f"{r.earlier_value} ({r.earlier_period}) → {late}" if r.earlier_value else late,
                    calculation=r.measure + (f"; {r.note}" if r.note else ""), source=f"{r.publisher}: {r.source_url}"))

for k in ["raw", "cardser", "score", "foodY"]:  # published key order
    O[k] = O.pop(k)
write_json(O, "report.json")
pd.DataFrame(REG).to_csv(BUILD / "numbers.csv", index=False)
print("step 6: report.json with", len(O), "blocks;", len(REG), "registered figures in numbers.csv")

# ---- average merchant payment by month and its change on a year earlier (deck exhibit) ----
tkt = v["total"] * 1e7 / (c["total"] * 1e6)
tyoy = (tkt / tkt.shift(12) - 1) * 100
write_json([{"m": i.strftime("%Y-%m"), "t": round(float(tkt[i]), 1), "y": round(float(tyoy[i]), 1)} for i in v.loc["2024-01":].index],
           "ticket_monthly.json")
