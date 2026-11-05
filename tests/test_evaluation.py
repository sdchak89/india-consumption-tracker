"""Rebuild the government data scorecard, check its score table, and check the facts its evidence cites.

    python -m pytest tests/test_evaluation.py      (or: python tests/test_evaluation.py)
"""
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evaluation"
DATA = ROOT / "data"
OUTPUTS = ["scorecard.csv", "scorecard_cells.csv", "scorecard.svg", "scorecard.md"]


def test_scorecard_rebuilds_exactly():
    subprocess.run([sys.executable, str(EV / "evaluate.py")], check=True, cwd=ROOT)
    for f in OUTPUTS:
        assert (ROOT / "build" / f).read_text(encoding="utf-8") == (EV / f).read_text(encoding="utf-8"), f


def test_every_cell_scored_once_with_evidence():
    s = pd.read_csv(EV / "sources.csv")
    r = pd.read_csv(EV / "rubric.csv")
    c = pd.read_csv(EV / "scorecard_cells.csv")
    assert len(c) == len(s) * len(r)
    assert not c.duplicated(["source", "dimension"]).any()
    assert set(c.source) == set(s.id) and set(c.dimension) == set(r.dimension)
    assert c.score.between(0, 4).all()
    assert c.basis.isin(["measured", "documented", "judged"]).all()
    assert c.evidence.str.strip().str.len().gt(5).all()
    # Measured scores come from evaluate.py, never from scores.csv.
    assert not (pd.read_csv(EV / "scores.csv").basis == "measured").any()


def test_scorecard_headlines():
    c = pd.read_csv(EV / "scorecard.csv").set_index("id")
    assert len(c) == 16
    assert c.loc["npci_mcc", "report_numbers"] == 55 and c.loc["npci_mcc", "tier"] == "Weak"
    assert set(c[c.tier == "Clear laggard"].index) == {"ls_cbdt", "rs_rupay"}
    assert (c.score_lo <= c.score).all() and (c.score <= c.score_hi).all()
    assert (c.rank_lo <= c.rank_hi).all()


def test_numbers_patterns_match_the_report():
    s = pd.read_csv(EV / "sources.csv")
    n = pd.read_csv(ROOT / "report" / "data" / "numbers.csv")
    for sid, pat in zip(s.id, s.numbers_pattern):
        re.compile(pat)
        hits = n.source.str.contains(pat, regex=True).sum()
        assert hits > 0 or sid == "ppac", f"{sid}: pattern matches no published number"


def test_evidence_claims_hold():
    """Facts quoted in scores.csv, checked against data/ so the evidence cannot silently go stale."""
    p2p = pd.read_csv(DATA / "npci" / "p2p_p2m_monthly.csv")
    tot = p2p[(p2p.series == "TOTAL") & (p2p.metric == "value")].set_index("period").value / 1e7
    p2m = p2p[(p2p.series == "P2M") & (p2p.metric == "value")].set_index("period").value / 1e7
    psi = pd.read_csv(DATA / "rbi" / "cash_residual_components.csv").set_index("period")

    # NPCI's UPI total matches RBI PSI within 1% in all 76 shared months.
    ratio = (psi.upi_total_inr_cr / tot).dropna()
    assert len(ratio) == 76 and (ratio.sub(1).abs() < 0.01).all()

    # The MCC table's merchant total equals NPCI's P2M total in all 69 months.
    m = pd.read_csv(DATA / "npci" / "merchant_categories_monthly.csv", dtype={"mcc": str})
    t = m[m.mcc == "total"].assign(period=lambda x: x.month.str[:7]).set_index("period").payment_value_inr_crore
    match = (t / p2m).dropna()
    assert len(match) == 69 and (match.sub(1).abs() < 1e-4).all()   # equal to rounding

    # 31 rows a month: the top 29 categories, the total and 'Others'.
    assert (m[m.status == "Published"].groupby("month").size() == 31).all()

    # Debt collection (MCC 7322) fell 37% in value from Aug to Sep 2025.
    d = m[m.mcc == "7322"].set_index("month").payment_value_inr_crore
    assert round(100 * (d["2025-09-01"] / d["2025-08-01"] - 1)) == -37

    # UPI value with no state: 14% (Apr 2023), peak 42% (Jun 2025), 39% (Sep 2026).
    st = pd.read_csv(DATA / "npci" / "state_monthly.csv.gz")
    un = st[(st.geography == "Unclassified (no state reported)") &
            (st.metric == "share_of_all_upi_value")].set_index("period").value
    assert (round(un["2023-04"]), un.idxmax(), round(un.max()), round(un["2026-09"])) == (14, "2025-06", 42, 39)

    # 776 districts in the latest month.
    dist = pd.read_csv(DATA / "npci" / "district_monthly.csv.gz", usecols=["period", "district"])
    assert dist[dist.period == dist.period.max()].district.nunique() == 776


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
    print("all checks pass")
