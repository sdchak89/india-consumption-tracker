"""Score the government datasets this tracker relies on, and rank them with a 90% range.

    python evaluation/evaluate.py            # data/ + evaluation/*.csv -> build/scorecard.*
    python evaluation/evaluate.py --publish  # rebuild and copy the outputs into evaluation/

Inputs
  evaluation/sources.csv   one row per dataset: publisher, access, release dates, what it is used for
  evaluation/rubric.csv    seven dimensions, each with five levels (0-4)
  evaluation/scores.csv    documented and judged scores, each with its evidence
  data/                    the measured scores (timeliness, completeness) are computed here, not typed in
  report/data/numbers.csv  how many of the report's published numbers rely on each dataset

Outputs
  scorecard.csv        one row per dataset: score, 90% range, rank, rank range, tier, numbers using it
  scorecard_cells.csv  every dataset x dimension score, with its basis and evidence
  scorecard.svg        the chart
  scorecard.md         the table

Method and limits: evaluation/README.md.
"""
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EV = ROOT / "evaluation"
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)

RETRIEVED = pd.Timestamp("2026-11-01")   # data/ was retrieved on this date
DRAWS = 20_000                            # random weightings
SEED = 2026
ALPHA = 2.0                               # Dirichlet concentration per dimension: weights vary roughly 0x-3x of equal
NUDGE = 0.25                              # chance a judged score moves up one level, and again down one, in a draw
BASES = ("measured", "documented", "judged")
TIERS = ["Clear leader", "Strong", "Middle", "Weak", "Clear laggard"]

sources = pd.read_csv(EV / "sources.csv", dtype=str, keep_default_na=False)
rubric = pd.read_csv(EV / "rubric.csv", dtype=str)
assessed = pd.read_csv(EV / "scores.csv")
DIMS = list(rubric.dimension)
IDS = list(sources.id)


# ---------- measured scores ----------

def month_end(p):
    return pd.Period(str(p)[:7], "M").end_time.normalize()


def lag_level(days):
    return 4 if days <= 7 else 3 if days <= 35 else 2 if days <= 95 else 1 if days <= 400 else 0


def share_level(pct):
    return 4 if pct >= 95 else 3 if pct >= 85 else 2 if pct >= 70 else 1 if pct >= 50 else 0


def fmt_date(t):
    return f"{t.day} {t:%b %Y}"


mcc = pd.read_csv(DATA / "npci" / "merchant_categories_monthly.csv", dtype={"mcc": str})
p2p = pd.read_csv(DATA / "npci" / "p2p_p2m_monthly.csv")
state = pd.read_csv(DATA / "npci" / "state_monthly.csv.gz")
psi = pd.read_csv(DATA / "rbi" / "cash_residual_components.csv")
credit = pd.read_csv(DATA / "rbi" / "consumer_credit_levels.csv")
vahan = pd.read_csv(DATA / "vahan" / "vahan_state_monthly.csv.gz",
                    usecols=["state", "year", "month", "registrations"])

# Latest period in each data file, to keep sources.csv honest.
_fy_q = re.compile(r"(\d{4})-\d{2} Q(\d)")


def _quarter_end(label):
    y, q = _fy_q.match(label).groups()           # FY quarter: Q1 = Apr-Jun of the FY's first year
    start = pd.Timestamp(int(y), 4, 1) + pd.DateOffset(months=3 * (int(q) - 1))
    return (start + pd.DateOffset(months=3) - pd.Timedelta(days=1)).normalize()


LATEST = {
    "npci_mcc": lambda: month_end(mcc.month.max()),
    "npci_p2p_p2m": lambda: month_end(p2p.period.max()),
    "npci_geo": lambda: month_end(state.period.max()),
    "mospi_nas": lambda: _quarter_end(pd.read_csv(DATA / "macro" / "gdp_pfce_quarterly.csv").period.iloc[-1]),
    "rbi_psi": lambda: month_end(psi.period.max()),
    "rbi_sibc": lambda: pd.Timestamp(credit[credit.lender == "bank"].date.max()),
    "rbi_nbfc": lambda: pd.Timestamp(credit[credit.lender == "nbfc"].date.max()),
    "rbi_currency": lambda: pd.Timestamp(int(pd.read_csv(DATA / "macro" / "currency_annual_fy_end.csv").period.max()[:4]) + 1, 3, 31),
    "vahan": lambda: month_end(f"{vahan.year.max()}-{vahan[vahan.year == vahan.year.max()].month.max():02d}"),
    "ppac": lambda: month_end(pd.read_csv(DATA / "ppac" / "petroleum_consumption_monthly.csv").period.max()),
}


def measured():
    rows = []
    src = sources.set_index("id")
    for sid, f in LATEST.items():
        got, said = f(), pd.Timestamp(src.loc[sid, "latest_period_end"])
        if got != said:
            sys.exit(f"sources.csv says {sid} ends {said.date()}, but data/ ends {got.date()}: update sources.csv")

    # Timeliness: release date minus the end of the latest period.
    for sid, s in src.iterrows():
        if not (s.latest_period_end and s.release_date):
            continue
        end, rel = pd.Timestamp(s.latest_period_end), pd.Timestamp(s.release_date)
        days = (rel - end).days
        start = "the census date the projections rest on" if sid == "mohfw_projection" else "the end of the latest period"
        ev = (f"{days:,} day{'s' if days != 1 else ''} from {start}, {fmt_date(end)}, to release, {fmt_date(rel)} "
              f"({s.release_date_basis}).")
        rows.append((sid, "timeliness", lag_level(days), "measured", ev))

    # Completeness, NPCI merchant categories: share of merchant value in named categories.
    m = mcc.copy()
    tot = m[m.mcc == "total"].set_index("month").payment_value_inr_crore
    oth = m[m.mcc == "others"].set_index("month").payment_value_inr_crore
    named = 100 * (1 - oth.iloc[-12:].sum() / tot.iloc[-12:].sum())
    first = 100 * oth.iloc[:12].sum() / tot.iloc[:12].sum()
    cats = m[~m.mcc.isin(["total", "others"])]
    unpub = 100 * (cats.status != "Published").mean()
    rows.append(("npci_mcc", "completeness", share_level(named), "measured",
                 f"Named categories carry {named:.0f}% of merchant value in the latest 12 months; 'Others' rose from "
                 f"{first:.0f}% (first 12 months, 2021) to {100 - named:.0f}%. {unpub:.0f}% of category-months are "
                 f"'Not separately published'."))

    # NPCI P2P/P2M: months present since the table starts.
    tv = p2p[(p2p.series == "TOTAL") & (p2p.metric == "value")]
    want = pd.period_range(tv.period.min(), tv.period.max(), freq="M")
    have = 100 * tv.period.nunique() / len(want)
    rows.append(("npci_p2p_p2m", "completeness", share_level(have), "measured",
                 f"{tv.period.nunique()} of {len(want)} months present ({tv.period.min()} to {tv.period.max()}); "
                 f"totals, so nothing is left unclassified."))

    # NPCI geography: share of UPI value with a state.
    un = state[(state.geography == "Unclassified (no state reported)") &
               (state.metric == "share_of_all_upi_value")].set_index("period").value
    with_state = 100 - un.iloc[-1]
    rows.append(("npci_geo", "completeness", share_level(with_state), "measured",
                 f"{with_state:.0f}% of UPI value has a state in {un.index[-1]} ({100 - un.iloc[0]:.0f}% in "
                 f"{un.index[0]}); the rest is 'Unclassified (no state reported)'."))

    # RBI PSI: months with every component of the digital-payments total.
    comp = ["upi_p2m_inr_cr", "bhim_aadhaar_pay_inr_cr", "netc_inr_cr", "credit_card_pos_inr_cr",
            "debit_card_pos_inr_cr", "ppi_wallet_inr_cr", "ppi_card_pos_inr_cr"]
    full = int(psi[comp].notna().all(axis=1).sum())
    rows.append(("rbi_psi", "completeness", share_level(100 * full / len(psi)), "measured",
                 f"All seven merchant-payment components present in {full} of {len(psi)} months "
                 f"({psi.period.min()} to {psi.period.max()})."))

    # Vahan: state-months with registrations.
    sm = vahan.groupby(["state", "year", "month"]).registrations.sum()
    months = vahan[["year", "month"]].drop_duplicates()
    cells = vahan.state.nunique() * len(months)
    ok = int((sm > 0).sum())
    rows.append(("vahan", "completeness", share_level(100 * ok / cells), "measured",
                 f"{ok:,} of {cells:,} state-months have registrations ({vahan.state.nunique()} states and UTs, "
                 f"{len(months)} months)."))
    return pd.DataFrame(rows, columns=["source", "dimension", "score", "basis", "evidence"])


# ---------- assemble and check the score table ----------

cells = pd.concat([measured(), assessed], ignore_index=True)
dup = cells[cells.duplicated(["source", "dimension"], keep=False)]
if len(dup):
    sys.exit(f"scored twice (measured and in scores.csv?):\n{dup[['source', 'dimension']]}")
grid = cells.pivot(index="source", columns="dimension", values="score").reindex(index=IDS, columns=DIMS)
if grid.isna().any().any():
    missing = grid.isna().stack()
    sys.exit(f"missing scores: {list(missing[missing].index)}")
bad = cells[~cells.basis.isin(BASES) | ~cells.score.between(0, 4) | cells.evidence.fillna("").str.len().eq(0)]
if len(bad):
    sys.exit(f"invalid rows:\n{bad}")
cells["o_s"] = cells.source.map({k: i for i, k in enumerate(IDS)})
cells["o_d"] = cells.dimension.map({k: i for i, k in enumerate(DIMS)})
cells = cells.sort_values(["o_s", "o_d"]).drop(columns=["o_s", "o_d"]).reset_index(drop=True)
cells["score"] = cells.score.astype(int)

S = grid.to_numpy(float)                                     # sources x dimensions, levels 0-4
J = (cells.pivot(index="source", columns="dimension", values="basis")
     .reindex(index=IDS, columns=DIMS).to_numpy() == "judged")
n, d = S.shape

# ---------- score, rank and their 90% ranges ----------

base = 25 * S.mean(axis=1)                                   # equal weights, scores as recorded; 0-100
rs = np.random.RandomState(SEED)                             # legacy generator: same stream on every numpy version
W = rs.dirichlet([ALPHA] * d, size=DRAWS)                    # draws x dimensions
u = rs.random_sample((DRAWS, n, d))
X = np.clip(S + J * ((u < NUDGE) * 1.0 - (u > 1 - NUDGE) * 1.0), 0, 4)
draw = 25 * np.einsum("kd,ksd->ks", W, X)                    # draws x sources
rank = 1 + (draw[:, None, :] > draw[:, :, None]).sum(axis=2)  # 1 = best; ties share the better rank
k = round(n / 3)
p_top = (rank <= k).mean(axis=0)
p_bot = (rank >= n - k + 1).mean(axis=0)


def tier(pt, pb):
    if pt >= 0.9:
        return "Clear leader"
    if pb >= 0.9:
        return "Clear laggard"
    if pt >= 0.5:
        return "Strong"
    if pb >= 0.5:
        return "Weak"
    return "Middle"


numbers = pd.read_csv(ROOT / "report" / "data" / "numbers.csv")
uses = [int(numbers.source.str.contains(p, regex=True).sum()) for p in sources.numbers_pattern]
base_rank = [1 + int((base > b).sum()) for b in base]

card = pd.DataFrame({
    "rank": base_rank,
    "id": IDS,
    "dataset": sources.short_name,
    "publisher": sources.publisher,
    "score": np.round(base, 1),
    "score_lo": np.round(np.quantile(draw, 0.05, axis=0), 1),
    "score_hi": np.round(np.quantile(draw, 0.95, axis=0), 1),
    "rank_lo": np.quantile(rank, 0.05, axis=0, method="inverted_cdf").astype(int),
    "rank_hi": np.quantile(rank, 0.95, axis=0, method="inverted_cdf").astype(int),
    "p_top_third": np.round(p_top, 3),
    "p_bottom_third": np.round(p_bot, 3),
    "tier": [tier(a, b) for a, b in zip(p_top, p_bot)],
    **{dim: grid[dim].astype(int).to_numpy() for dim in DIMS},
    "judged_scores": J.sum(axis=1),
    "report_numbers": uses,
    "upgrade": sources.upgrade,
})
card = card.sort_values(["rank", "score_hi", "dataset"], ascending=[True, False, True]).reset_index(drop=True)


# ---------- chart ----------

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(c):
    W_, X0, X1, ROW, Y0 = 860, 300, 600, 26, 150
    H = Y0 + ROW * len(c) + 92
    x = lambda v: X0 + (X1 - X0) * v / 100
    hue = {"Clear leader": "u", "Strong": "u", "Middle": "m", "Weak": "d", "Clear laggard": "d"}
    hollow = {"Strong", "Middle", "Weak"}
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_}" height="{H}" viewBox="0 0 {W_} {H}" '
         f'role="img" aria-labelledby="t d" font-family="system-ui, -apple-system, \'Segoe UI\', sans-serif">',
         "<style>",
         ".bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.t3{fill:#898781}.g{stroke:#e1e0d9}.ax{stroke:#c3c2b7}"
         ".fu{fill:#2a78d6}.su{stroke:#2a78d6}.fm{fill:#898781}.sm{stroke:#898781}.fd{fill:#e34948}.sd{stroke:#e34948}"
         ".fs{fill:#fcfcfb}.ss{stroke:#fcfcfb}.hit{fill:transparent}.row:hover .hit{fill:rgba(11,11,11,0.04)}"
         "@media (prefers-color-scheme: dark){.bg,.fs{fill:#1a1a19}.ss{stroke:#1a1a19}.t1{fill:#f0efec}.t2{fill:#c3c2b7}"
         ".g{stroke:#2c2c2a}.ax{stroke:#383835}.fu{fill:#3987e5}.su{stroke:#3987e5}.fm{fill:#b5b4ad}.sm{stroke:#b5b4ad}"
         ".fd{fill:#e66767}.sd{stroke:#e66767}.row:hover .hit{fill:rgba(255,255,255,0.05)}}",
         "</style>",
         f'<rect class="bg" width="{W_}" height="{H}" rx="8"/>',
         '<text id="t" class="t1" x="24" y="34" font-size="17" font-weight="600">'
         "Government data behind the consumption tracker, scored</text>",
         '<text id="d" class="t2" x="24" y="56" font-size="12.5">Dot: score out of 100, equal weights on seven '
         "dimensions. Right is better.</text>",
         f'<text class="t2" x="24" y="74" font-size="12.5">Line: 90% range over {DRAWS:,} random weightings, '
         "with each judged score moved one level at random.</text>"]
    # legend
    lx = 24
    for t in TIERS:
        h = hue[t]
        if t in hollow:
            o.append(f'<circle cx="{lx + 5}" cy="99" r="4.5" class="fs s{h}" stroke-width="2"/>')
        else:
            o.append(f'<circle cx="{lx + 5}" cy="99" r="5" class="f{h}"/>')
        o.append(f'<text class="t2" x="{lx + 15}" y="103" font-size="12">{t}</text>')
        lx += 15 + 7.2 * len(t) + 22
    o.append(f'<text class="t3" x="{lx}" y="103" font-size="12">filled: top or bottom third in 90% of draws</text>')
    # column heads
    hy = Y0 - 14
    o += [f'<text class="t3" x="24" y="{hy}" font-size="11.5">Dataset</text>',
          f'<text class="t3" x="{X0}" y="{hy}" font-size="11.5">Score</text>',
          f'<text class="t3" x="622" y="{hy}" font-size="11.5">Tier</text>',
          f'<text class="t3" x="770" y="{hy}" font-size="11.5" text-anchor="end">Rank (90%)</text>',
          f'<text class="t3" x="836" y="{hy}" font-size="11.5" text-anchor="end">Numbers</text>']
    yb = Y0 + ROW * len(c) - 6
    for v in (0, 25, 50, 75, 100):
        o.append(f'<line class="g" x1="{x(v)}" x2="{x(v)}" y1="{Y0 - 6}" y2="{yb}" stroke-width="1"/>')
        o.append(f'<text class="t3" x="{x(v)}" y="{yb + 18}" font-size="11.5" text-anchor="middle">{v}</text>')
    o.append(f'<line class="ax" x1="{X0}" x2="{X1}" y1="{yb}" y2="{yb}" stroke-width="1"/>')
    for i, r in c.iterrows():
        cy = Y0 + ROW * i + ROW / 2 - 4
        h = hue[r.tier]
        rk = f"{r.rank_lo}" if r.rank_lo == r.rank_hi else f"{r.rank_lo}–{r.rank_hi}"
        tip = (f"{r.dataset} ({r.publisher}): score {r.score:.0f}, 90% range {r.score_lo:.0f}–{r.score_hi:.0f}; "
               f"rank {r['rank']}, 90% range {rk}; {r.tier}; used in {r.report_numbers} of the report's numbers")
        o.append(f'<g class="row"><title>{esc(tip)}</title>')
        o.append(f'<rect class="hit" x="16" y="{cy - ROW / 2}" width="{W_ - 32}" height="{ROW}" rx="4"/>')
        o.append(f'<text class="t1" x="24" y="{cy + 4.5}" font-size="13">{esc(r.dataset)}</text>')
        o.append(f'<line class="s{h}" x1="{x(r.score_lo):.1f}" x2="{x(r.score_hi):.1f}" y1="{cy}" y2="{cy}" '
                 f'stroke-width="3" stroke-linecap="round" opacity="0.45"/>')
        if r.tier in hollow:
            o.append(f'<circle cx="{x(r.score):.1f}" cy="{cy}" r="4.5" class="fs s{h}" stroke-width="2"/>')
        else:
            o.append(f'<circle cx="{x(r.score):.1f}" cy="{cy}" r="5" class="f{h} ss" stroke-width="2" '
                     f'paint-order="stroke"/>')
        o.append(f'<text class="t2" x="622" y="{cy + 4.5}" font-size="12.5">{r.tier}</text>')
        o.append(f'<text class="t2" x="770" y="{cy + 4.5}" font-size="12.5" text-anchor="end" '
                 f'font-variant-numeric="tabular-nums">{rk}</text>')
        o.append(f'<text class="t2" x="836" y="{cy + 4.5}" font-size="12.5" text-anchor="end" '
                 f'font-variant-numeric="tabular-nums">{r.report_numbers}</text>')
        o.append("</g>")
    fy = yb + 44
    o += [f'<text class="t3" x="24" y="{fy}" font-size="11.5">Numbers = how many of the report\'s '
          f"{len(numbers)} published numbers (report/data/numbers.csv) rely on the dataset. Fit for tracking "
          "consumption month to month;</text>",
          f'<text class="t3" x="24" y="{fy + 16}" font-size="11.5">not a verdict on the agencies. Data retrieved '
          "1 Nov 2026. Method: evaluation/README.md.</text>",
          "</svg>"]
    return "\n".join(o) + "\n"


# ---------- table ----------

def md(c):
    label = dict(zip(rubric.dimension, rubric.label))
    short = dict(timeliness="Time", frequency="Freq", detail="Detail", completeness="Compl", consistency="Consist",
                 access="Access", documentation="Docs")
    head = ["Rank", "Dataset", "Score (90% range)", "Rank range", "Tier"] + [short[x] for x in DIMS] + \
           ["Numbers", "What would lift it"]
    lines = ["<!-- generated by evaluation/evaluate.py; do not edit by hand -->", "",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for _, r in c.iterrows():
        rk = f"{r.rank_lo}" if r.rank_lo == r.rank_hi else f"{r.rank_lo}–{r.rank_hi}"
        lines.append("| " + " | ".join([str(r["rank"]), f"**{r.dataset}** · {r.publisher}",
                                         f"{r.score:.0f} ({r.score_lo:.0f}–{r.score_hi:.0f})", rk, r.tier]
                                        + [str(r[x]) for x in DIMS] + [str(r.report_numbers), r.upgrade]) + " |")
    lines += ["", "Dimension scores are levels 0–4 (rubric.csv): " +
              ", ".join(f"{short[x]} = {label[x]}" for x in DIMS) + ".", ""]
    risk = c.assign(at_risk=c.report_numbers * (100 - c.score) / 100).sort_values("at_risk", ascending=False)
    lines += ["## Where to act first", "",
              "Report numbers that rely on a dataset, times the share of a perfect score it misses:", ""]
    for _, r in risk.head(3).iterrows():
        lines.append(f"- **{r.dataset}**: {r.report_numbers} numbers × {100 - r.score:.0f}% short = "
                     f"{r.at_risk:.1f}. {r.upgrade}.")
    return "\n".join(lines) + "\n"


OUT = {"scorecard.csv": card.to_csv(index=False, lineterminator="\n"),
       "scorecard_cells.csv": cells.to_csv(index=False, lineterminator="\n"),
       "scorecard.svg": svg(card),
       "scorecard.md": md(card)}
for name, text in OUT.items():
    (BUILD / name).write_text(text, encoding="utf-8")
print(f"evaluation: {n} datasets x {d} dimensions ({int((cells.basis == 'measured').sum())} measured, "
      f"{int(J.sum())} judged); {DRAWS:,} draws -> build/scorecard.*")
if "--publish" in sys.argv:
    for name in OUT:
        shutil.copy(BUILD / name, EV / name)
    print("copied outputs to evaluation/")
