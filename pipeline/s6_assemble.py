"""Step 6. Add the scoreboard, the category panels' monthly series, the food split and the raw
monthly table, then write build/report.json (every number the web page and the PDF plot) and
build/numbers.csv (each registered figure with its calculation and source)."""
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
