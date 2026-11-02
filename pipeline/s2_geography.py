"""Step 2. States, cities and metro clusters from NPCI's state and district UPI tables.

Basis: Jul–Sep 2026 vs Jul–Sep 2025, all UPI (P2P + P2M) by payer address.
Per-resident figures use 2026 population projections (MoHFW) for states and World Population Review's 2026
estimates for cities, with a Census-trend estimate for the core districts kept for comparison; clusters use fixed 2011 shares. Writes build/states.csv, cities.csv, clusters.csv."""
import pandas as pd
from common import DATA, BUILD, write_json

s = pd.read_csv(DATA / "npci" / "state_monthly.csv.gz")
s = s[s.metric.isin(["value", "volume"])].pivot_table(index=["geography", "period"], columns="metric", values="value").reset_index()
U = "Unclassified (no state reported)"

P = pd.read_csv(DATA / "macro" / "state_population_projection.csv")
P = P[P.year == 2026].set_index("state")["population_persons"]
# NPCI state names -> projection table names
NAME = {"Jammu and Kashmir": "Jammu & Kashmir (UT)", "Uttarakhand": "Uttaranchal", "Delhi": "NCT of Delhi",
        "Andaman and Nicobar Islands": "Andaman & Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu": None}


def pop(g):
    if g == "Dadra and Nagar Haveli and Daman and Diu":
        return P["Dadra & Nagar Haveli"] + P["Daman Diu"]
    return P.get(NAME.get(g, g))


Q26, Q25 = ["2026-07", "2026-08", "2026-09"], ["2025-07", "2025-08", "2025-09"]


def agg(g, ms, k):
    return s[(s.geography == g) & (s.period.isin(ms))][k].sum()


def classified(ms, k):
    return s[(s.geography != U) & (s.period.isin(ms))][k].sum()


popall = sum(pop(g) for g in s.geography.unique() if g != U and pop(g))
rows = []
for g in s.geography.unique():
    if g == U:
        continue
    p = pop(g)
    v26, v25, c26, c25 = agg(g, Q26, "value"), agg(g, Q25, "value"), agg(g, Q26, "volume"), agg(g, Q25, "volume")
    rows.append(dict(state=g, pop_mn=round(p / 1e6, 1), v_pr_month=round(v26 / p / 3), c_pr_month=round(c26 / p / 3, 1),
                     g_value=round((v26 / v25 - 1) * 100, 1), g_count=round((c26 / c25 - 1) * 100, 1),
                     share_val=round(v26 / classified(Q26, "value") * 100, 2), share_pop=round(p / popall * 100, 2),
                     tkt=round(v26 / c26)))
S = pd.DataFrame(rows).sort_values("v_pr_month", ascending=False)
S.to_csv(BUILD / "states.csv", index=False)

# India totals for the geography section
c26, c25 = classified(Q26, "value"), classified(Q25, "value")
u26, u25 = agg(U, Q26, "value"), agg(U, Q25, "value")
geo = dict(v_pr_month=round(c26 / popall / 3), c_pr_month=round(classified(Q26, "volume") / popall / 3, 1),
           g_value=round((c26 / c25 - 1) * 100, 1), g_count=round((classified(Q26, "volume") / classified(Q25, "volume") - 1) * 100, 1),
           unc_q25=round(u25 / (c25 + u25) * 100, 1), unc_q26=round(u26 / (c26 + u26) * 100, 1))
write_json(geo, "india_geo.json")

# ---- cities (core districts) ------------------------------------------------
d = pd.read_csv(DATA / "npci" / "district_monthly.csv.gz")
d = d[d.metric.isin(["value", "volume"])].pivot_table(index=["state", "district", "period"], columns="metric", values="value").reset_index()
sn = pd.read_csv(DATA / "npci" / "district_snapshot.csv")


def dsum(state_like, names, ms):
    x = d[(d.state.str.contains(state_like, case=False)) & (d.district.isin(names)) & (d.period.isin(ms))]
    return x.value.sum(), x.volume.sum(), sorted(x.district.unique())


def census_pop(codes):
    return sn[sn.census_code.isin(codes)].pop_2026_est.sum()


def code(name):
    r = sn[sn.district_2011 == name]
    assert len(r) == 1, name
    return r.census_code.iloc[0]


# city: (state, NPCI district names, 2011 census district names)
CORE = {
    "Mumbai": ("Maharashtra", ["Mumbai", "Mumbai Suburban"], ["Mumbai", "Mumbai Suburban"]),
    "Delhi": ("Delhi", None, None),
    "Bengaluru": ("Karnataka", ["Bengaluru (Urban)"], ["Bangalore"]),
    "Hyderabad": ("Telangana", ["Hyderabad"], ["Hyderabad"]),
    "Chennai": ("Tamil Nadu", ["Chennai"], ["Chennai"]),
    "Pune": ("Maharashtra", ["Pune"], ["Pune"]),
    "Kolkata": ("West Bengal", ["Kolkata"], ["Kolkata"]),
    "Ahmedabad": ("Gujarat", ["Ahmadabad"], ["Ahmadabad"]),
}
# 2026 population of each core district. No count exists after Census 2011, so:
#   pop 2026 = 2011 population on today's district boundary
#              x (1 + r x state growth 2011->2026, MoHFW projection),
#   r = the district's 2001-11 growth / its state's 2001-11 growth (Census Table A-2).
# A district that grows twice as fast as its state keeps doing so; one that shrank keeps shrinking slowly.
# Chennai was enlarged in 2018 and has no comparable 2001 figure, so it grows at its state's pace (r = 1).
CEN = pd.read_csv(DATA / "macro" / "census_district_growth.csv").set_index("area")
P11 = pd.read_csv(DATA / "macro" / "state_population_projection.csv")
P11 = P11[P11.year == 2011].set_index("state")["population_persons"]
CEN_AREA = {"Bangalore": "Bangalore (Bengaluru Urban district)"}


def core_pop(census_names, st):
    g01 = lambda a: CEN.loc[a, "census_2011"] / CEN.loc[a, "census_2001"] - 1
    d01 = sum(CEN.loc[CEN_AREA.get(n, n), "census_2001"] for n in census_names)
    d11 = sum(CEN.loc[CEN_AREA.get(n, n), "census_2011"] for n in census_names)
    base = sum(CEN.loc[CEN_AREA.get(n, n), "census_2011_current_boundary"] if pd.notna(CEN.loc[CEN_AREA.get(n, n), "census_2011_current_boundary"])
               else CEN.loc[CEN_AREA.get(n, n), "census_2011"] for n in census_names)
    enlarged = base > d11
    r = 1.0 if enlarged else (d11 / d01 - 1) / g01(st)
    return base * (1 + r * (pop(st) / P11[NAME.get(st, st)] - 1)), r, base


# City populations used in the report: World Population Review's 2026 estimates (boundaries undefined;
# mostly metro areas). The Census-trend estimate for the core district(s) is kept alongside for comparison.
WPR = pd.read_csv(DATA / "macro" / "city_population_wpr_2026.csv").set_index("city")["population_2026"]

out = []
for city, (st, npci_names, census_names) in CORE.items():
    if city == "Delhi":
        x = d[(d.state == "Delhi") & (d.period.isin(Q26))]
        v, c, dn = x.value.sum(), x.volume.sum(), sorted(x.district.unique())
        pct = pop("Delhi")  # whole state: the MoHFW projection itself
    else:
        v, c, dn = dsum(st, npci_names, Q26)
        pct, r, base = core_pop(census_names, st)
    p = WPR[city]
    stp, sv = pop(st), agg(st, Q26, "value")
    out.append(dict(city=city, districts=" + ".join(dn), pop_mn=round(p / 1e6, 2), v_pr_month=round(v / p / 3),
                    c_pr_month=round(c / p / 3, 1), tkt=round(v / c), state=st, state_v_pr_month=round(sv / stp / 3),
                    city_vs_state=round(v / p / (sv / stp), 2), city_share_of_state_val=round(v / sv * 100, 1),
                    pop_census_trend_mn=round(pct / 1e6, 2), v_pr_month_census_trend=round(v / pct / 3),
                    city_vs_state_census_trend=round(v / pct / (sv / stp), 2)))
pd.DataFrame(out).sort_values("v_pr_month", ascending=False).to_csv(BUILD / "cities.csv", index=False)

# ---- wider metro clusters ---------------------------------------------------
wide = []
for name, grp in sn[sn.metro_cluster.fillna("") != ""].groupby("metro_cluster"):
    names = [n.strip() for x in grp.npci_districts for n in x.split("|")]
    x = d[(d.district.isin(names)) & (d.period.isin(Q26))]
    p = grp.pop_2026_est.sum()
    wide.append(dict(cluster=name, pop_mn=round(p / 1e6, 1), v_pr_month=round(x.value.sum() / p / 3), n_districts=len(names)))
pd.DataFrame(wide).sort_values("v_pr_month", ascending=False).to_csv(BUILD / "clusters.csv", index=False)
print("step 2:", len(S), "states,", len(out), "cities,", len(wide), "clusters")
