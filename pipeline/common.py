"""Shared paths, time windows, rounding and loaders for the pipeline."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)

# Twelve-month windows, October to September. Y26 = Oct 2025 to Sep 2026.
W = {
    "Y22": ("2021-10", "2022-09"),
    "Y23": ("2022-10", "2023-09"),
    "Y24": ("2023-10", "2024-09"),
    "Y25": ("2024-10", "2025-09"),
    "Y26": ("2025-10", "2026-09"),
}
WL = {
    "Y22": "Oct 21–Sep 22",
    "Y23": "Oct 22–Sep 23",
    "Y24": "Oct 23–Sep 24",
    "Y25": "Oct 24–Sep 25",
    "Y26": "Oct 25–Sep 26",
}
YEARS = list(W)


def isnan(x):
    return x is None or (isinstance(x, float) and np.isnan(x))


def r1(x):
    return None if isnan(x) else round(float(x), 1)


def r2(x):
    return None if isnan(x) else round(float(x), 2)


def jr(x, nd=0):
    """Round half away from zero (the way JavaScript's Math.round treats positive numbers).

    Python's round() rounds halves to even; the report rounds displayed figures once,
    from full precision, with this function."""
    f = 10 ** nd
    return float(np.floor(x * f + 0.5) / f) if nd else int(np.floor(x + 0.5))


def ym(ts):
    return ts.strftime("%Y-%m")


def load_npci():
    """NPCI UPI merchant-category table as three objects.

    v: payment value, ₹ crore (month x MCC); c: payments, million; names: MCC -> category name.
    'total' is all merchant (P2M) payments; 'others' is NPCI's residual line.
    Months where NPCI did not list a category are NaN."""
    m = pd.read_csv(DATA / "npci" / "merchant_categories_monthly.csv", dtype={"mcc": str})
    m["month"] = pd.to_datetime(m["month"])
    v = m.pivot_table(index="month", columns="mcc", values="payment_value_inr_crore", aggfunc="first")
    c = m.pivot_table(index="month", columns="mcc", values="transactions_million", aggfunc="first")
    cols = sorted(v.columns)
    v, c = v[cols], c.reindex(columns=cols)
    names = m.drop_duplicates("mcc").set_index("mcc")["category"].reindex(cols)
    return v, c, names


def win(s, k):
    """Values of a monthly series in window k, indexed by calendar month (for matching)."""
    a, b = W[k]
    x = s.loc[a:b].copy()
    x.index = x.index.month
    return x


def read_json(name):
    return json.load(open(BUILD / name))


def write_json(obj, name):
    json.dump(obj, open(BUILD / name, "w"), ensure_ascii=False)


class Registry:
    """Every published number with how it was calculated and where it comes from."""

    def __init__(self, start=None):
        self.rows = list(start or [])

    def add(self, key, value, calculation, source):
        self.rows.append(dict(id=key, value=value, calculation=calculation, source=source))
