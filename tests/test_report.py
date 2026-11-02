"""Rebuild the report's dataset from the raw files and check it against the published one.

    python -m pytest tests/      (or: python tests/test_report.py)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rebuild():
    subprocess.run([sys.executable, str(ROOT / "pipeline" / "run.py")], check=True, cwd=ROOT)


def load(path):
    return json.load(open(ROOT / path))


def test_pipeline_reproduces_published_dataset():
    rebuild()
    assert load("build/report.json") == load("report/data/report.json")
    assert load("build/ticket_monthly.json") == load("report/data/ticket_monthly.json")


def test_headline_numbers():
    D = load("report/data/report.json")
    last = D["dirY"][-1]
    assert last["y"] == "Oct 25–Sep 26"
    assert last["v"] == 101.5          # ₹ lakh crore, merchant UPI, Oct 2025–Sep 2026
    assert last["gv"] == 26.4          # % growth on the year before
    assert D["dirY"][0]["v"] == 23.0   # four years earlier
    dec = {d["fy"]: d for d in D["dec"]}
    assert dec["FY24"]["cons_part"] == 19 and dec["FY26"]["cons_part"] == 35   # % of growth matching consumption
    assert dec["FY24"]["share_gain"] == 49.7 and dec["FY26"]["share_gain"] == 16.6
    q = D["cashQ"][-1]
    assert q["q"] == "Apr–Jun 26" and (q["adj_lo"], q["adj_hi"]) == (39.1, 47.9)  # cash share range, strict version
    assert D["fam_total"] == 21.2      # ₹ lakh crore added in the latest year
    assert len(D["score"]) == 28


if __name__ == "__main__":
    test_pipeline_reproduces_published_dataset()
    test_headline_numbers()
    print("all checks pass")
