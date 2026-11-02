"""Run the whole pipeline: data/ -> build/report.json, build/ticket_monthly.json, build/numbers.csv.

    python pipeline/run.py            # rebuild
    python pipeline/run.py --publish  # rebuild and copy the outputs into report/data/
"""
import runpy
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["s1_categories", "s2_geography", "s3_core", "s4_tax_vehicles_credit", "s5_cash_geography", "s6_assemble"]

sys.path.insert(0, str(HERE))
for step in STEPS:
    runpy.run_path(str(HERE / f"{step}.py"), run_name="__main__")

if "--publish" in sys.argv:
    root = HERE.parent
    for f in ["report.json", "ticket_monthly.json", "numbers.csv"]:
        shutil.copy(root / "build" / f, root / "report" / "data" / f)
    print("copied outputs to report/data/")
