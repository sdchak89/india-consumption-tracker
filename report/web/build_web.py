"""Build the interactive web report: report/web/template.html + script.js + cards.js + the dataset
-> docs/index.html (served by GitHub Pages). Chart.js 4.4.1 loads from cdnjs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "report" / "web"
D = open(ROOT / "report" / "data" / "report.json").read()
s = open(WEB / "template.html").read()
js = open(WEB / "script.js").read().replace("__CARDS__", open(WEB / "cards.js").read())
s = s.replace("__DATA__", D).replace("__SCRIPT__", js)
s = s.replace("__CHARTJS__", "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js")
(ROOT / "docs").mkdir(exist_ok=True)
open(ROOT / "docs" / "index.html", "w").write(s)
print("wrote docs/index.html,", len(s), "bytes")
