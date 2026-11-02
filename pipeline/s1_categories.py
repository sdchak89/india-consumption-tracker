"""Step 1. Category profiles from the NPCI merchant-category table.

For each category: value and payments in the latest year, growth on matched months,
four-year (or shorter) CAGR, average payment then and now, and share of merchant UPI.
Writes build/category_profiles.csv and build/categories.json."""
import numpy as np
import pandas as pd
from common import W, YEARS, BUILD, load_npci, win, r1, ym, write_json

v, c, names = load_npci()


def matched(m, k0, k1, df):
    """Sums over months published in both windows."""
    a, b = win(df[m], k0), win(df[m], k1)
    mk = a.notna() & b.notna()
    return a[mk].sum(), b[mk].sum(), int(mk.sum())


def total_matched(m, k0, k1):
    """All-merchant totals over the same months a category was published."""
    a, b = win(v[m], k0), win(v[m], k1)
    mk = a.notna() & b.notna()
    return win(v["total"], k0)[mk].sum(), win(v["total"], k1)[mk].sum()


# ---- profiles -------------------------------------------------------------
rows = []
for m in v.columns:
    if m == "total":
        continue
    r = {"mcc": m, "name": names[m]}
    y26n = int(win(v[m], "Y26").notna().sum())
    r["y26_months"] = y26n
    if y26n == 0:
        continue
    # CAGR base: the earliest year with at least 9 months matched to the latest year
    base = None
    for k in YEARS[:-1]:
        if matched(m, k, "Y26", v)[2] >= 9:
            base = k
            break
    if base:
        a, b, n = matched(m, base, "Y26", v)
        years = YEARS.index("Y26") - YEARS.index(base)
        ca, cb, _ = matched(m, base, "Y26", c)
        ta, tb = total_matched(m, base, "Y26")
        r.update(
            base=base, cagr_months=n, years=years,
            val_cagr=((b / a) ** (1 / years) - 1) * 100,
            cnt_cagr=((cb / ca) ** (1 / years) - 1) * 100,
            tot_cagr_same=((tb / ta) ** (1 / years) - 1) * 100,
            share_base=a / ta * 100, share_26=b / tb * 100,
            tkt_base=a * 1e7 / (ca * 1e6), tkt_26=b * 1e7 / (cb * 1e6),
        )
    # one-year growth, matched months (at least 6)
    a, b, n = matched(m, "Y25", "Y26", v)
    if n >= 6:
        ca, cb, _ = matched(m, "Y25", "Y26", c)
        ta, tb = total_matched(m, "Y25", "Y26")
        r.update(yoy_v=(b / a - 1) * 100, yoy_c=(cb / ca - 1) * 100, yoy_n=n, tot_yoy_same=(tb / ta - 1) * 100)
    vv, cc = win(v[m], "Y26").sum(), win(c[m], "Y26").sum()
    r.update(val_26_cr=vv, cnt_26_mn=cc, tkt_26_all=vv * 1e7 / (cc * 1e6) if cc else np.nan)
    rows.append(r)

P = pd.DataFrame(rows).set_index("mcc")
P.to_csv(BUILD / "category_profiles.csv", float_format="%.17g")

# ---- report blocks ----------------------------------------------------------
O = {}

# Categories shown as cards and in the scoreboard
CARDS = ["5411", "5812", "5814", "5451", "5462", "5422", "5541", "6211", "7322", "5732", "5921", "5993", "5813",
         "5262", "5691", "5651", "5331", "5311", "5912", "4814", "4900", "4121", "4112", "7230", "5441", "7622",
         "5137", "9399"]

O["ser"] = {
    m: [{"m": ym(i), "v": r1(rw.v), "c": r1(rw.c)} for i, rw in pd.DataFrame({"v": v[m], "c": c[m]}).loc["2021-01":].iterrows()]
    for m in CARDS
}

FIELDS = ["base", "years", "cagr_months", "val_cagr", "cnt_cagr", "tot_cagr_same", "share_base", "share_26", "tkt_base",
          "tkt_26", "yoy_v", "yoy_c", "tot_yoy_same", "val_26_cr", "cnt_26_mn", "tkt_26_all", "y26_months"]
prof = {}
for m in CARDS + ["others"]:
    if m not in P.index:
        continue
    row, d = P.loc[m], {"name": names[m]}
    for k in FIELDS:
        x = row.get(k)
        d[k] = None if x is None or (isinstance(x, float) and np.isnan(x)) else (x if isinstance(x, str) else r1(x))
    a, ac = win(v[m], "Y25"), win(c[m], "Y25")
    mk = a.notna()
    d["tkt_25"] = r1(a[mk].sum() * 1e7 / (ac[mk].sum() * 1e6)) if mk.sum() >= 6 else None
    a, b = win(v[m], "Y24"), win(v[m], "Y25")
    mk = a.notna() & b.notna()
    if mk.sum() >= 9:
        ac, bc = win(c[m], "Y24"), win(c[m], "Y25")
        d["yoy_v_prev"] = r1((b[mk].sum() / a[mk].sum() - 1) * 100)
        d["yoy_c_prev"] = r1((bc[mk].sum() / ac[mk].sum() - 1) * 100)
    prof[m] = d
O["prof"] = prof


def basket_yoy(ms, df):
    s = df[ms].sum(axis=1, min_count=len(ms))
    return (s / s.shift(12) - 1) * 100


# Eating out vs food at home
away = v[["5812", "5814"]].sum(axis=1)
home = v["5411"]
O["foodshare"] = {
    k: round(float(away.loc[a:b].sum() / (away.loc[a:b].sum() + home.loc[a:b].sum()) * 100), 1) for k, (a, b) in W.items()
}
total_yoy = (v["total"] / v["total"].shift(12) - 1) * 100
fav, fhv = basket_yoy(["5812", "5814"], v), basket_yoy(["5411", "5451", "5422", "5462"], v)
O["food"] = [{"m": ym(i), "home": r1(fhv[i]), "away": r1(fav[i]), "all": r1(total_yoy[i])} for i in v.loc["2023-10":"2026-09"].index]

# Liquor shops vs bars, matched months
lq = {}
for k in ["Y24", "Y25", "Y26"]:
    a, b = W[k]
    shop, bar = v["5921"].loc[a:b], v["5813"].loc[a:b]
    mk = shop.notna() & bar.notna()
    lq[k] = {"shop_share": round(float(shop[mk].sum() / (shop[mk].sum() + bar[mk].sum()) * 100), 1), "n": int(mk.sum())}
O["liquor"] = lq

O["brokers_monthly"] = [{"m": ym(i), "v": r1(v["6211"][i]), "c": r1(c["6211"][i])} for i in v.loc["2022-01":].index]

# Debt collection (MCC 7322): the September 2025 break
d7, c7 = v["7322"], c["7322"]
A, S = "2025-08-01", "2025-09-01"
O["dc"] = {
    "aug25_v": r1(d7[A]), "sep25_v": r1(d7[S]), "aug25_c": r1(c7[A]), "sep25_c": r1(c7[S]),
    "sep26_v": r1(d7["2026-09-01"]), "sep26_c": r1(c7["2026-09-01"]),
    "lfl_v": r1((d7["2026-09-01"] / d7[S] - 1) * 100), "lfl_c": r1((c7["2026-09-01"] / c7[S] - 1) * 100),
    # average payment of the value that left the category in September 2025
    "left_tkt": r1((d7[A] - d7[S]) * 1e7 / ((c7[A] - c7[S]) * 1e6)),
    "cc_nov25_v": r1(v["5413"]["2025-11-01"]), "cc_nov25_c": r1(c["5413"]["2025-11-01"]),
    "cc_tkt": r1(v["5413"]["2025-11-01"] * 1e7 / (c["5413"]["2025-11-01"] * 1e6)),
    "tkt_aug25": r1(d7[A] * 1e7 / (c7[A] * 1e6)), "tkt_sep25": r1(d7[S] * 1e7 / (c7[S] * 1e6)),
    "others_aug25": r1(v["others"][A]), "others_sep25": r1(v["others"][S]),
    "prebreak_yoy": r1((d7.loc["2024-09":"2025-08"].sum() / d7.loc["2023-09":"2024-08"].sum() - 1) * 100),
}

write_json(O, "categories.json")
print("step 1: profiles for", len(P), "categories")
