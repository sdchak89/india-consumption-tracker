"""Build the PDF briefing's HTML (20 pages, 1280 x 720) from the published dataset.

Usage: python report/deck/build_deck.py   ->  build/deck.html
Then:  node report/deck/render_pdf.js build/deck.html docs/<name>.pdf"""
import json, re, math, html as H
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "report" / "web"
DECK = ROOT / "report" / "deck"
NODE = ROOT / "node_modules"
jr = lambda x: int(math.floor(x + 0.5))  # round half up, as displayed on the page

D = json.load(open(ROOT / "report" / "data" / "report.json"))
TK = json.load(open(ROOT / "report" / "data" / "ticket_monthly.json"))
CARDS = open(WEB / "cards.js").read()
T = open(WEB / "template.html").read()
helpers = open(DECK / "helpers.js").read()
charts = open(DECK / "charts.js").read()

def rows(tid):
    i=T.index('id="%s"'%tid); j=T.index('</table>',i)
    body=T[T.index('<tbody>',i):j]
    out=[]
    for tr in re.findall(r'<tr>(.*?)</tr>',body,re.S):
        out.append(re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S))
    return out
HYP=rows('tHyp'); OUT=rows('tOutside'); CRS=rows('tCreditSpend'); PAIRS=rows('tPairs')
def strip(s): return re.sub(r'<[^>]+>','',s)

FONTS=(NODE/'@fontsource').as_uri()+'/'
css_links=''.join(f'<link rel="stylesheet" href="{FONTS}{f}">' for f in ['ibm-plex-sans/400.css','ibm-plex-sans/500.css','ibm-plex-sans/600.css','ibm-plex-sans/700.css','ibm-plex-sans/400-italic.css','source-serif-4/600.css','source-serif-4/700.css'])

CSS='''
@page{size:1280px 720px;margin:0}
/* Layout: consulting exhibit pages, 1280x720. Tracker, action title, then insight column + numbered exhibits; source line and page number at foot. */
:root{--navy:#0B2545;--ink:#141A22;--ink-2:#434C58;--ink-3:#747D88;--line:#D5DBE3;--grid:#E8ECF1;--s1:#1F5FD6;--s2:#E0662E;--s3:#12A086;--bench:#A7B0BB;--sky:#A9C4F5;--tint:#EEF3FC;
--good:#0B7A3B;--good-bg:#E2F2E8;--mixed:#8A5A00;--mixed-bg:#FBF0D9;--bad:#B42F2F;--bad-bg:#FBE7E6;--na:#5D646C;--na-bg:#ECEEF1;--surface:#fff;
--body:"IBM Plex Sans",Inter,Arial,sans-serif;--serif:"Source Serif 4",Georgia,serif;color-scheme:light}
*{box-sizing:border-box}
html,body{margin:0;background:#fff;color:var(--ink);font:13px/1.45 var(--body);-webkit-font-smoothing:antialiased}
.pg{width:1280px;height:720px;padding:28px 48px 0;display:flex;flex-direction:column;position:relative;overflow:hidden;break-after:page;page-break-after:always}
.trk{display:flex;justify-content:space-between;font:600 10.5px var(--body);letter-spacing:.08em;text-transform:uppercase;color:var(--s1);padding-bottom:7px;border-bottom:1px solid var(--line)}
.trk span:last-child{color:var(--ink-3);font-weight:500}
h2.act{font:700 26px/1.16 var(--serif);color:var(--navy);margin:14px 0 0;max-width:1120px;text-wrap:balance;letter-spacing:-.005em}
.sub{font-size:13.5px;color:var(--ink-2);margin-top:6px;max-width:1080px}
.body{flex:1;min-height:0;display:grid;gap:26px;margin-top:16px;padding-bottom:12px}
.g-pe{grid-template-columns:330px 1fr}
.g-pee{grid-template-columns:300px 1fr 1fr}
.g-ee{grid-template-columns:1fr 1fr}
.g-peee{grid-template-columns:270px 1fr 1fr 1fr}
.pts{display:flex;flex-direction:column;gap:14px;font-size:13.5px;line-height:1.5;color:var(--ink-2);border-top:2px solid var(--navy);padding-top:9px;min-width:0}
.pts h4,.box h4{font:600 10.5px var(--body);letter-spacing:.08em;text-transform:uppercase;color:var(--navy);margin:0}
.pts p{margin:0}.pts b{color:var(--ink);font-weight:600}
.big{font:700 34px/1 var(--serif);color:var(--s1);display:block;margin-bottom:3px}
.ex{display:flex;flex-direction:column;min-height:0;min-width:0;border-top:2px solid var(--navy);padding-top:8px}
.exs{flex:none;font-size:8.4px;line-height:1.3;color:var(--ink-3);margin-top:3px}
.exn{font:600 10px var(--body);letter-spacing:.08em;text-transform:uppercase;color:var(--s1)}
.ext{font:600 13.5px/1.3 var(--body);color:var(--ink);margin-top:3px}
.exu{font-size:11px;color:var(--ink-3);margin-top:1px}
.lg{display:flex;flex-wrap:wrap;gap:3px 14px;font-size:10.5px;color:var(--ink-2);margin-top:6px}
.lg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.lg i.l{height:3px;vertical-align:2px}.lg i.d{height:3px;vertical-align:2px;background:repeating-linear-gradient(90deg,var(--bench) 0 4px,transparent 4px 7px)!important}
.cv{flex:1;position:relative;min-height:0;margin-top:6px}
.ft{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;border-top:1px solid var(--line);padding:7px 0 13px;font-size:9.5px;color:var(--ink-3);line-height:1.38}
.ft .pn{font:600 10px var(--body);color:var(--ink-2);white-space:nowrap}
.ft b{color:var(--ink-2);font-weight:600}
.tag{display:inline-block;font:600 9.5px var(--body);letter-spacing:.04em;text-transform:uppercase;color:var(--mixed);background:var(--mixed-bg);border-radius:3px;padding:1px 5px;margin-right:4px;vertical-align:1px}
.box{background:var(--tint);border-left:3px solid var(--s1);padding:10px 14px;font-size:12.5px;color:var(--ink-2)}
.box b{color:var(--ink)}
table.tb{width:100%;border-collapse:collapse;font-size:11px;line-height:1.35}
.tb th{font:600 10px var(--body);letter-spacing:.03em;color:var(--ink-3);text-align:left;border-bottom:1.5px solid var(--navy);padding:4px 7px;vertical-align:bottom}
.tb td{padding:4px 7px;border-bottom:1px solid var(--grid);vertical-align:top;color:var(--ink-2);font-variant-numeric:tabular-nums}
.tb td:first-child{color:var(--ink);font-weight:600}
.tb .n{text-align:right;white-space:nowrap}
.pill{display:inline-block;font:600 10px/1.3 var(--body);border-radius:999px;padding:2px 8px;white-space:nowrap}
.pill.good{color:var(--good);background:var(--good-bg)}.pill.mixed{color:var(--mixed);background:var(--mixed-bg)}.pill.bad{color:var(--bad);background:var(--bad-bg)}.pill.na{color:var(--na);background:var(--na-bg)}
.cap{font-size:10px;color:var(--ink-3)}
.up{color:var(--good)}.down{color:var(--bad)}
/* cover */
.cover{background:var(--navy);color:#fff;padding:0;display:grid;grid-template-rows:auto 1fr auto}
.cover .top{display:flex;justify-content:space-between;padding:34px 56px 0;font:600 11px var(--body);letter-spacing:.1em;text-transform:uppercase;color:#9FB7E0}
.cover .mid{padding:70px 56px 0}
.cover h1{font:700 64px/1.04 var(--serif);margin:0;max-width:900px;letter-spacing:-.01em}
.cover .lede{font-size:19px;line-height:1.45;color:#D3DDEE;max-width:760px;margin-top:22px}
.cover .rule{width:120px;height:4px;background:#4F86F0;margin-top:30px}
.credit{margin-top:22px;display:grid;grid-template-columns:auto auto;justify-content:start;gap:4px 14px;font-size:13px;color:#B9C8E2}
.credit b{font-weight:600;color:#fff}
.credit a{color:#fff;text-decoration:none;border-bottom:1px solid #9FB7E0}
.ft a{color:var(--ink-2);text-decoration:none}
.credit span:nth-child(odd){font:600 10.5px var(--body);letter-spacing:.1em;text-transform:uppercase;color:#9FB7E0;padding-top:2px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:1px solid #2C4570;margin:0 56px;padding:22px 0 34px}
.kpi{padding-right:28px;border-right:1px solid #2C4570;margin-right:28px}.kpi:last-child{border:none;margin:0}
.kpi b{display:block;font:700 34px/1 var(--serif);color:#fff}
.kpi span{display:block;font-size:12px;line-height:1.4;color:#B9C8E2;margin-top:8px}
/* exec summary */
.es{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(3,1fr);gap:14px 40px}
.es .f{border-top:2px solid var(--navy);padding-top:10px;display:grid;align-content:start;grid-template-columns:150px 1fr;gap:4px 18px;font-size:12.8px;line-height:1.45;color:var(--ink-2)}
.es .f .num{grid-row:1/3;font:700 30px/1.05 var(--serif);color:var(--s1)}.es .f .num small{display:block;font:500 11px/1.35 var(--body);color:var(--ink-3);margin-top:5px}
.es .f h3{font:700 15px/1.25 var(--serif);color:var(--navy);margin:0;display:flex;gap:9px}
.es .f h3 i{font:600 11px/20px var(--body);font-style:normal;color:#fff;background:var(--s1);border-radius:50%;width:20px;height:20px;text-align:center;flex:none;margin-top:1px}
/* small multiples */
.sm{display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:repeat(3,1fr);gap:12px 20px;min-height:0}
.mc{display:flex;flex-direction:column;min-height:0;min-width:0;border-top:1.5px solid var(--navy);padding-top:6px}
.mc .h{display:flex;justify-content:space-between;gap:8px;font:600 11.5px var(--body);color:var(--ink)}
.mc .h span{color:var(--s1);white-space:nowrap}
.mc .k{font-size:10px;color:var(--ink-3);margin-top:1px}
.mc .t{font-size:10.5px;line-height:1.35;color:var(--ink-2);margin-top:3px}
.mc .cv{margin-top:2px}
.cols3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:26px;font-size:11.5px;line-height:1.45;color:var(--ink-2)}
.cols3 p{margin:0 0 7px}.cols3 b{color:var(--ink)}
.cols3 code{font-size:10.5px;background:var(--tint);padding:0 3px;border-radius:3px;color:var(--ink)}
.src li{margin-bottom:4px}
.infer{font:600 9.5px var(--body);text-transform:uppercase;letter-spacing:.04em;color:var(--mixed);background:var(--mixed-bg);border-radius:3px;padding:1px 5px}
.tb.t-score td{padding:1.1px 6px;font-size:9.8px;line-height:1.25}.tb.t-score th{padding:2px 6px}.tb.t-pairs td{font-size:11px;padding:5px 8px}.tb.t-crs td{font-size:12.6px;padding:8.5px 10px;line-height:1.45}.tb.t-crs th{font-size:10.5px;padding:5px 10px}.tb.t-hyp td{font-size:11.3px;padding:6.5px 8px;line-height:1.4}.tb.t-hyp .pill{white-space:normal}.tb.t-out td{font-size:12px;padding:5.2px 8px}.tb.t-st td{font-size:9.8px;padding:1.2px 6px;line-height:1.25}.tb.t-st td:first-child{white-space:nowrap}.tb.t-st th{padding:2px 6px}
'''

def page(n,trk,title,body,src,sub=None,cls='',grid=''):
    return f'''<section class="pg {cls}"><div class="trk"><span>{trk}</span><span>Where is Indian consumption going? · Soumyadeep Chakraborty · November 2026</span></div>
<h2 class="act">{title}</h2>{f'<p class="sub">{sub}</p>' if sub else ''}
<div class="body {grid}">{body}</div>
<div class="ft"><div>{src}</div><div class="pn">{n}</div></div></section>'''

EXN=[0]
NPm='NPCI merchant category table · data/npci/merchant_categories_monthly.csv'
SRCX={
 'xScope':'NPCI P2P/P2M and merchant category tables · data/npci/p2p_p2m_monthly.csv, merchant_categories_monthly.csv',
 'xDirY':NPm,'xDirG':NPm,'xBasketY':NPm,'xBasketG':NPm,'xTktY':NPm,'xTktM':NPm,'xFam':NPm,'xTicket':NPm,'xFoodY':NPm,'xFood':NPm,'xITax':NPm,
 'xDec':'NPCI P2P/P2M table; MoSPI PFCE, current prices (31 Aug 2026) · data/macro/size_ratios_fy.csv, gdp_pfce_annual.csv',
 'xBridge':'NPCI; MoSPI; RBI payment system indicators; RBI Handbook Table 36 · data/macro/',
 'xCash':'RBI payment system indicators; NPCI; MoSPI quarterly PFCE · data/rbi/cash_share_quarterly.csv',
 'xPay':'RBI payment system indicators; RBI Handbook Table 36; NPCI · data/macro/',
 'xSize':'NPCI; MoSPI national accounts · data/macro/size_ratios_fy.csv',
 'xTerc':'NPCI state table; MoF Lok Sabha Q946; MoHFW · data/npci/state_monthly.csv.gz, data/tax/state_income_tax.csv',
 'xVeh':'Vahan4 dashboard · data/vahan/vahan_state_monthly.csv.gz',
 'xCredSplit':'RBI sectoral credit (30 Oct 2026), NBFC sectoral credit (6 Oct 2026) · data/rbi/credit_growth_prepost.csv',
 'xCredit':'RBI sectoral credit (30 Oct 2026), NBFC sectoral credit (6 Oct 2026) · data/rbi/credit_growth_prepost.csv',
 'xCity':'NPCI district table; MoHFW; Census 2001 and 2011 · data/npci/district_monthly.csv.gz, data/macro/census_district_growth.csv',
}
SRCT={
 'Scoreboard: 28 selected categories':NPm+'; report/data/numbers.csv',
 'Three pairs, three different stories':NPm,
 'Credit next to spending':'RBI sectoral credit; Vahan; NPCI; company results (page 20) · data/rbi/, data/vahan/',
 'Eight hypotheses, tested':'NPCI; MoSPI; RBI; Vahan; company results (page 20) · report/data/report.json',
 'The outside view: public markets and official surveys':'Company results; RBI surveys; MoSPI; Mint (links on page 20)',
 'States: UPI money moved per resident, and growth':'NPCI state table; MoHFW projections · data/npci/state_monthly.csv.gz',
}
def xs(t): return f'<div class="exs">Source: {t}</div>' if t else ''
def ex(title,unit,cid,legend='',extra=''):
    EXN[0]+=1
    return f'''<figure class="ex" style="margin:0"><span class="exn">Exhibit {EXN[0]}</span><div class="ext">{title}</div><div class="exu">{unit}</div>{f'<div class="lg">{legend}</div>' if legend else ''}<div class="cv"><canvas id="{cid}"></canvas></div>{extra}{xs(SRCX.get(cid))}</figure>'''
def exhtml(title,unit,inner):
    EXN[0]+=1
    return f'''<figure class="ex" style="margin:0"><span class="exn">Exhibit {EXN[0]}</span><div class="ext">{title}</div><div class="exu">{unit}</div><div style="flex:1;min-height:0;margin-top:6px;overflow:hidden">{inner}</div>{xs(SRCT.get(title))}</figure>'''
def exhtml_wide(title,unit,inner):
    EXN[0]+=1
    return f'''<figure class="ex" style="margin:0;grid-column:1/-1"><span class="exn">Exhibit {EXN[0]}</span><div class="ext">{title}</div><div class="exu">{unit}</div><div style="margin-top:4px">{inner}</div>{xs(SRCT.get(title))}</figure>'''
def lg(items):
    return ''.join(f'<span><i class="{c}" style="background:{col}"></i>{t}</span>' for t,col,c in items)
def pts(*ps,head='What the data show'):
    return '<div class="pts"><h4>'+head+'</h4>'+''.join(f'<p>{p}</p>' for p in ps)+'</div>'

NPCI='<b>Source:</b> NPCI UPI ecosystem statistics (merchant category tables, Jan 2021–Sep 2026); analysis'
P=[]
# 1 cover
P.append('''<section class="pg cover"><div class="top"><span>India consumption briefing</span><span>November 2026 · data to September 2026</span></div>
<div class="mid"><h1>Where is Indian consumption going?</h1><p class="lede">What 69 months of UPI payments data say about how India spends, cross-checked against cash, bank credit, national accounts, vehicle registrations and company results.</p><div class="rule"></div><div class="credit"><span>Author</span><span><b>Soumyadeep Chakraborty</b></span><span>Data and code</span><span><a href="https://github.com/sdchak89/india-consumption-tracker">github.com/sdchak89/india-consumption-tracker</a></span></div></div>
<div class="kpis"><div class="kpi"><b>₹101.5L cr</b><span>Merchant UPI, Oct 2025–Sep 2026, up 26.4% on the year before</span></div>
<div class="kpi"><b>35%</b><span>Share of FY26 merchant-UPI growth that matches consumption growth (19% in FY24); the rest is UPI growing relative to consumption</span></div>
<div class="kpi"><b>39–48%</b><span>Cash's estimated share of consumer spending, Apr–Jun 2026 (70–78% in Apr–Jun 2022)</span></div>
<div class="kpi"><b>₹11.2L cr</b><span>Added to non-housing consumer credit in a year; 76.5% in gold, personal and other loans whose end-use is unobserved</span></div></div></section>''')

# 2 exec summary
F=[("Merchant UPI is still growing about 25% a year, and the slowdown has levelled off","₹101.5 lakh crore in Oct 2025–Sep 2026, up 26.4%, from ₹23.0 lakh crore four years earlier. Monthly growth has stayed between 22% and 31% since early 2025."),
("Merchant UPI's lead over consumption growth is narrowing","Merchant UPI grew 26.5% in FY26 against 8.5% for consumption in rupees. The gap (UPI growing relative to consumption) shrank from 50% (FY24) to 29% to 17%, and the average merchant payment has stopped shrinking (₹595 → ₹601, latest two Oct–Sep years). Slower UPI growth ahead need not mean weaker demand."),
("Cash's spending share fell, while cash balances kept rising","Cash's model-estimated share of consumer spending fell from 70–78% (Apr–Jun 2022) to 39–48% (Apr–Jun 2026). ATM withdrawals fell ₹1.9 lakh crore in FY26, yet cash held by the public rose 12%."),
("Food is the engine; liquor and paan shops are among the fastest growers","Groceries are the largest named category (₹9.5 lakh crore). Fast food grew 108% a year for four years. Liquor-shop UPI is up 70% with an unchanged average payment."),
("Vehicle buying and loan balances rebounded together","Car and two-wheeler registrations grew 21–22% in the year after the September 2025 GST cut (5–6% the year before). NBFC consumer-durable loans grew 56%; bank vehicle loans 6.1% → 15.5%. Credit data add financing context; UPI cannot identify how a payment was funded."),
("Real consumption is growing; prices and confidence are the watch-points","Real consumption grew 7.2% in FY26. Recent company sales reflect price and mix as well as volume (HUL: sales +15%, volume +7%); RBI urban confidence fell from 96.9 to 87.9, inflation is 5.5% and the RBI raised rates in October.")]
NUM=[('+26.4%','merchant UPI, last 12 months'),('49.7% → 16.6%','growth in the merchant-UPI ÷ consumption ratio, FY24 → FY26'),('39–48%','cash share of consumer spending (model)'),('₹9.5L cr','groceries, the largest named category'),('+21–22%','car and two-wheeler registrations'),('7.2%','real consumption growth, FY26')]
es='<div class="es">'+''.join(f'<div class="f"><div class="num">{NUM[k][0]}<small>{NUM[k][1]}</small></div><h3><i>{k+1}</i><span>{h}</span></h3><div>{t}</div></div>' for k,(h,t) in enumerate(F))+'</div>'
watch='''<div class="box" style="margin-top:2px"><b>What to watch.</b> <span class="tag">Scenario</span>If nominal consumption keeps growing 8.5% a year and the share-gain part halves from here, merchant UPI growth would be about 17.5% next year and 13% the year after. <span class="tag">Our inference</span>The October rate hike and 5.5% inflation make the next two quarters the test: if company volumes hold and discretionary UPI stops slowing, the "cautious consumer" reading is wrong.</div>'''
P.append(f'''<section class="pg"><div class="trk"><span>Executive summary</span><span>Where is Indian consumption going? · Soumyadeep Chakraborty · November 2026</span></div>
<h2 class="act">UPI growth remains near 26%; its lead over consumption is narrowing while confidence weakens and price pressures rise</h2>
<div class="body" style="grid-template-rows:1fr auto;gap:14px">{es}{watch}</div>
<div class="ft"><div><b>Source:</b> NPCI; RBI; MoSPI; Vahan; company results for Jul–Sep 2026; analysis. UPI figures are nominal. ₹1 lakh crore (L cr) = ₹1 trillion. FY = April–March. <b>Next update:</b> clothing, electronics, online marketplaces and department stores will be revisited after the festive season, once October–November data are out (December 2026).</div><div class="pn">2</div></div></section>''')

pn=3
def add(trk,title,body,src,grid,sub=None):
    global pn; P.append(page(pn,trk,title,body,src,sub=sub,grid=grid)); pn+=1
c=D['coverage']
add('0 · Scope','Merchant payments are only 30% of UPI value, but 63% of payments, and they are where consumption shows up',
 pts(f"<span class='big'>11%</span>of all UPI value sits in named consumer categories (₹37.8 lakh crore). NPCI puts another 45% of merchant value into an unnamed \"Others\" bucket.",
     "<b>Why P2P is left out.</b> Person-to-person payments average ₹2,438 against ₹601 for merchants; most of it is money moving between people, not spending.",
     "Some consumption does hide in P2P (a vegetable seller paid on a personal UPI ID), but NPCI does not split it out, so merchant UPI understates UPI's role in consumption.",
     "<b>Financial flows</b> (brokers, loan repayments, digital gold) are ₹16.6 lakh crore of merchant UPI and are kept out of the consumption reads.")+
 ex('What UPI paid for in the last 12 months','Share of value or payments, Oct 2025–Sep 2026','xScope',lg([('Person to person (P2P)','var(--bench)',''),('Merchant (P2M)','var(--s1)',''),('Consumption categories','var(--navy)',''),('Financial flows','var(--s2)',''),('Government (1%)','var(--s3)',''),("NPCI 'Others'",'var(--bench)','')])),
 '<b>Source:</b> NPCI UPI P2P/P2M totals and merchant category tables (via the measure.thisindianlife.today archive); analysis. P2P = person to person; P2M = person to merchant. "Consumption" = named household-spending categories, including some mixed ones (uniforms, marketplaces, department stores).','g-pe')

add('1 · Direction','Merchant UPI is still growing about a quarter a year; since early 2025 monthly growth has held between 22% and 31%',
 pts("<span class='big'>+26.4%</span>Merchant UPI reached ₹101.5 lakh crore in Oct 2025–Sep 2026, from ₹23.0 lakh crore four years earlier.",
     "<b>The steep slowdown of 2022–24 is consistent with UPI's adoption surge fading</b> (adoption is not measured directly). Growth has been stable since; September 2026 was ₹8.87 lakh crore across 15.2 billion payments (+23.3% and +23.1%).",
     "<b>Online games</b> (1.0–1.7% of value in 2025) stopped being published separately after August 2025. The dashed line removes them from both years, so it is an upper bound.")+
 ex('Merchant UPI per year','₹ lakh crore and growth on the year before, Oct–Sep years','xDirY')+
 ex('Growth on the same month a year earlier','%, monthly, Jan 2022–Sep 2026','xDirG',lg([('Value (₹)','var(--s1)','l'),('Number of payments','var(--s2)','l'),('Value without online games','var(--bench)','d')])),
 NPCI+'. Oct–Sep years so the latest year ends with the latest NPCI month. Online games = MCC 5816 "Digital Goods: Games", which included real-money gaming; not publishing a category does not mean the spending fell to zero.','g-pee')

add('1 · Direction','Since May 2025, discretionary categories have grown slower than essentials on UPI in every month, by about 4 points on average',
 pts("<span class='big'>+26.4% vs +22.9%</span>Essentials rose to ₹24.0 lakh crore and discretionary to ₹6.5 lakh crore over the last 12 months.",
     "<b>Same 13 categories every month:</b> the consumption categories NPCI published continuously over these 48 months, so list changes cannot create spikes.",
     "<b>Essentials:</b> groceries, dairy, meat, bakeries, pharmacies, fuel, telecom, utilities, department stores. <b>Discretionary:</b> restaurants, fast food, electronics, bars.",
     "September 2026: essentials ₹2.10 lakh crore (+22.0%), discretionary ₹0.53 lakh crore (+17.7%).")+
 ex('Essentials vs discretionary per year','₹ lakh crore and growth, fixed 13-category basket','xBasketY',lg([('Essentials','var(--s1)',''),('Discretionary','var(--s2)','')]))+
 ex('Monthly growth, same basket','Value growth on the same month a year earlier, Oct 2023–Sep 2026','xBasketG',lg([('Essentials','var(--s1)','l'),('Discretionary','var(--s2)','l')])),
 NPCI+'.','g-pee')

add('2 · Consumption signal','About 35% of merchant-UPI growth now matches consumption growth, up from 19% two years ago; the rest is UPI growing relative to consumption',
 pts("<b>FY26:</b> merchant UPI grew 26.5% while consumption (PFCE, current prices) grew 8.5%. The split is an accounting split, not a causal estimate; it does not say where each rupee came from.",
     "<b>Cash held is not shrinking:</b> currency with the public rose from ₹36.3 to ₹40.7 lakh crore (+12.0%), faster than consumption. <b>Cash withdrawn is:</b> ATM withdrawals fell from ₹30.6 to ₹28.7 lakh crore.",
     "<span class='tag'>Scenario</span>The share-gain part fell from 50% to 29% to 17%, down about 42% a year. If nominal consumption keeps growing 8.5% and the share-gain part halves from here, merchant UPI growth would be about 17.5% next year and 13% the year after.")+
 ex('Merchant UPI growth split into consumption growth and share gain','% growth; labels = share of UPI growth','xDec',lg([('Part matching consumption growth','var(--s1)',''),('Part from UPI growing relative to consumption','var(--bench)','')]))+
 ex('What changed in FY26','Change from FY25, ₹ lakh crore','xBridge'),
 '<b>Source:</b> NPCI; MoSPI national accounts (base 2022-23); RBI payment system indicators and Handbook Table 36; analysis. FY = April–March. Bars split in proportion to the logs of the two growth factors; formula and notes on page 20.','g-pee')

add('2 · Consumption signal','The average merchant payment has stopped shrinking, consistent with maturing adoption',
 pts("<span class='big'>₹595 → ₹601</span>Average merchant payment, latest two Oct–Sep years, after ₹813, ₹664 and ₹643 in the three years before.",
     "<b>Flat or slightly up every month since January 2026</b>, after falling 6–10% year on year in Jan–Aug 2025 and about 1.5–4.1% in Sep–Dec.",
     "<b>The fixed 13-category basket shows the same:</b> ₹272.50 → ₹272.66.",
     "The sub-1% rise is nominal and mix-sensitive; it does not establish larger real purchases.")+
 ex('Average merchant UPI payment per year','₹ per payment, Oct–Sep years','xTktY')+
 ex('Change in the average payment','% on the same month a year earlier, Jan 2024–Sep 2026','xTktM',lg([('Smaller than a year earlier','var(--s2)',''),('Larger than a year earlier','var(--s1)','')])),
 NPCI+'. Average payment = value ÷ number of payments, all merchant categories.','g-pee')

add('3 · Cash vs digital','On a model estimate, cash fell from about three-quarters of consumer spending to under half in four years',
 pts("<span class='big'>39–48%</span>Cash's estimated share of consumer spending in Apr–Jun 2026, down from 70–78% in Apr–Jun 2022.",
     "<b>In rupees,</b> digital consumer payments tripled from ₹8.9 to ₹27.7 lakh crore a quarter, while cash spending fell from ₹25.2 to ₹21.3 lakh crore.",
     "<b>Strict version:</b> UPI paid to brokers, lenders, credit-card bills and digital gold is removed. On the RBI article's method without that removal, cash is 31–40% (Apr–Jun 2026).",
     "These are model estimates of cash use, not observed cash payments.")+
 ex('Consumer spending per quarter, paid digitally vs in cash','₹ lakh crore; labels = cash share (midpoint of range)','xCash',lg([('Digital (midpoint)','var(--s1)',''),('Cash (midpoint)','var(--s2)','')]))+
 ex('How Indians pay','₹ lakh crore per year (cash held = stock at 31 March)','xPay',lg([('Merchant UPI','var(--s1)',''),('ATM withdrawals','var(--s2)',''),('Card payments','var(--bench)',''),('Cash held by public','var(--s3)','')])),
 '<b>Source:</b> Extension of Bhuyan, RBI Bulletin (Oct 2024; not RBI\'s views); RBI payment system indicators; MoSPI PFCE (base 2022-23); NPCI; analysis. Range: low estimate counts card and wallet payments outside shops as consumption, high estimate does not.','g-pee')

add('3 · Cash vs digital','NPCI\'s unnamed "Others" took 58% of last year\'s increase in merchant UPI; among named categories, food at home added the most',
 pts("<span class='big'>₹21.2L cr</span>Increase in merchant UPI, Oct 2025–Sep 2026 vs the year before.",
     "<b>₹12.3 lakh crore (58%) went to NPCI's \"Others\".</b> With categories moving on and off NPCI's top-29 list, ₹14.0 lakh crore (65.9%) falls outside this report's category attribution (named categories need at least 10 matched months), so no category view can explain most of UPI's growth.",
     "<b>Of what can be seen,</b> food at home added the most (+₹2.9 lakh crore, +33%), then fuel and transport (+₹1.3 lakh crore).",
     "<b>Loan repayments show a fall,</b> most likely because of a possible classification break in September 2025 (page 11).")+
 ex('Where the extra merchant UPI went','Increase, ₹ lakh crore (growth); blue = consumption, orange = financial flows, grey = not broken out','xFam'),
 NPCI+'. A category counts by name only with at least 10 matched calendar months (published in both years); digital gold (9 months) and family clothing (4) therefore sit in the grey bar.','g-pe')

add('4 · UPI and merchants','UPI moved 0.91 times GDP in FY26; the announced merchant fee targets selected payments above ₹2,000, with its start deferred',
 pts("<b>All UPI moved ₹314 lakh crore in FY26</b> (0.53× GDP in FY23). Merchant UPI reached ₹90.9 lakh crore, equal to 46% of consumer spending (21% in FY23). Gross payment flows, so the same rupee can move several times.",
     "<b>The fee:</b> 0.4% (capped at ₹300) on payments above ₹2,000 at merchants receiving over ₹1 lakh a month for three consecutive months; a flat ₹5 for fuel, telecom, rail, insurance and utilities; 0.02% for capital markets. Smaller payments, small merchants, P2P and AutoPay stay free. Deferred to after Diwali; new date to be notified.",
     "<span class='tag'>Our inference</span>At 0.4% UPI stays far cheaper than cards. Watch for bills split into ₹2,000 pieces and cash discounts on big purchases.")+
 ex('UPI as a multiple of the economy','Ratio of gross payment flows to GDP and to consumption','xSize',lg([('All UPI ÷ GDP','var(--s1)',''),('Merchant UPI ÷ consumption','var(--s2)','')]))+
 ex('Average payment by category','₹ per payment, Oct 2025–Sep 2026 (log scale); orange = above ₹2,000','xTicket'),
 '<b>Source:</b> NPCI; RBI payment system indicators (all-UPI totals); MoSPI (31 Aug 2026 vintage); Department of Financial Services FAQ (fee terms); ThePrint and Indian Express (deferral, Oct 2026); analysis. An average below ₹2,000 still includes many payments above it.','g-pee')

# scoreboard table
sc=D['score'];mx=max(max(r.get('cagr') or 0,r.get('mk') or 0) for r in sc)
def rsf(x): return '' if x is None else '₹{:,}'.format(jr(x))
trs=''
for r in sc:
    if r.get('cagr') is None: cg='<span class="cap">too few comparable months</span>'
    else:
        w=lambda v:max(0,v)/mx*100
        col='var(--s1)' if r['cagr']>r['mk'] else 'var(--bench)'
        cg=f'<div style="display:flex;align-items:center;gap:8px"><div style="position:relative;height:10px;width:150px"><span style="position:absolute;left:0;top:2px;height:7px;border-radius:2px;width:{w(r["cagr"]):.1f}%;background:{col}"></span><span style="position:absolute;top:0;width:2px;height:11px;background:var(--ink-3);left:{w(r["mk"]):.1f}%"></span></div><span>{jr(r["cagr"])}% vs {jr(r["mk"])}% <span class="cap">({r["yrs"]}y)</span></span></div>'
    p0=lambda x:'n/a' if x is None else ('+' if x>0 else '')+str(jr(x))+'%'
    trs+=f'<tr><td>{r["n"]}</td><td class="n">{r["val"]:.2f}</td><td class="n">{p0(r.get("yv"))}</td><td class="n">{p0(r.get("yc"))}</td><td class="n">{(rsf(r.get("t0"))+" → ") if r.get("t0") else ""}{rsf(r.get("t1"))}</td><td>{cg}</td></tr>'
tbl=f'<table class="tb t-score"><thead><tr><th>Category</th><th class="n">₹ lakh cr,<br>last 12 months</th><th class="n">Value<br>growth</th><th class="n">Payments<br>growth</th><th class="n">Average payment,<br>then → now</th><th>CAGR (bar) vs all merchant UPI (tick)</th></tr></thead><tbody>{trs}</tbody></table>'
add('5 · Category by category','Food and fuel lead; many category tickets remain below their earlier levels',
 pts("<b>Groceries</b> are the largest named category at ₹9.5 lakh crore, growing 32%, with the average payment down from ₹476 to ₹220 over four years.",
     "<b>Blue bars beat the market:</b> the category's compound growth exceeded all merchant UPI over the same years, so it gained share.",
     "<b>Brokers and lenders behave differently:</b> they follow market rules and reclassifications, not spending.",
     "<b>† Debt collection:</b> a block of large payments appears to have left this code in September 2025 (value −37% in one month, payments −12%), a possible classification break NPCI has not announced. Reported growth −18.6%; a sensitivity calculation gives +25.5% in value and +55% in payments.",
     head='How to read the table')+
 exhtml('Scoreboard: 28 selected categories','Last 12 months = Oct 2025–Sep 2026; growth on matched months; CAGR from the earliest Oct–Sep year with ≥9 matched months',tbl),
 NPCI+'. Average payment "then" is the CAGR base year; "now" is all published months of the last 12. Broker growth uses 10 matched months.','g-pe')

# small multiples
cards=json.loads(re.sub(r'(\w+):',lambda m:'"'+m.group(1)+'":' if m.group(1) in ('m','t','k','p','ev') else m.group(0),'[]')) if False else None
import subprocess
cj=subprocess.run(['node','-e','const C='+CARDS+';process.stdout.write(JSON.stringify(C))'],capture_output=True,text=True).stdout
CD=json.loads(cj)
cells=''
SHORT={'6211':'Securities brokers','7322':'Loan repayments (debt collection)','5541':'Fuel stations','5691':"Men's and women's clothing",'4814':'Telecom recharges and bills','5411':'Groceries and supermarkets'}
for cd in CD:
    cd['t']=SHORT.get(cd['m'],cd['t'].split(' (')[0]);k=cd['k'];head=re.search(r'<strong>(.*?)</strong>',cd['p']).group(1).rstrip('.')
    kl=('Reported: value −18.6%, payments +38.3% · sensitivity: +25.5%, +55.2% · avg '+k[3][0]+' (1 yr)') if cd['m']=='7322' else f"Value {k[1][0]} · payments {k[2][0]} · avg {k[3][0]} ({', '.join(k[3][1].split(', ')[1:])})"
    cells+=f'<div class="mc"><div class="h"><span style="color:var(--ink)">{cd["t"]}</span><span>{k[0][0]}</span></div><div class="k">{kl}</div><div class="cv"><canvas id="m{cd["m"]}"></canvas></div><div class="t"><b style="color:var(--ink)">{head}.</b></div></div>'
P.append(f'''<section class="pg"><div class="trk"><span>5 · Category by category</span><span>Where is Indian consumption going? · Soumyadeep Chakraborty · November 2026</span></div>
<h2 class="act">Twelve categories up close: fast food leads four-year growth among large categories; brokers and repayments follow markets and reclassifications</h2>
<div class="body" style="grid-template-rows:1fr auto;gap:0;margin-top:12px"><div class="sm">{cells}</div><div class="exs">Source for all panels: NPCI merchant category table · data/npci/merchant_categories_monthly.csv; fuel volumes: PPAC · data/ppac/petroleum_consumption_monthly.csv</div></div>
<div class="ft"><div>{NPCI}; PPAC product-wise petroleum consumption, Oct 2025–Sep 2026 vs the preceding 12 months (fuel volumes). Monthly value, ₹ crore; gaps are months NPCI did not publish the category. Growth = last 12 months vs the year before; avg = average payment then → now.</div><div class="pn">{pn}</div></div></section>''');pn+=1

pairs_html='<table class="tb t-pairs" style="margin-top:8px"><thead><tr><th>Pair</th><th>What the data show</th><th>Verdict</th></tr></thead><tbody>'+''.join(f'<tr><td style="width:170px">{r[0]}</td><td>{r[1]}</td><td style="width:330px">{r[2]}</td></tr>' for r in PAIRS)+'</tbody></table>'
add('6 · Substitution','Food at home and eating out move together: there is no evidence of substitution in the UPI shares',
 ex('Groceries vs eating out','₹ lakh crore per year; label = eating out\'s share of the two','xFoodY',lg([('Groceries','var(--s1)',''),('Restaurants + fast food','var(--s2)','')]))+
 ex('Monthly growth','% on the same month a year earlier','xFood',lg([('Food at home','var(--s1)','l'),('Eating out','var(--s2)','l'),('All merchant UPI','var(--bench)','d')]))+
 exhtml_wide('Three pairs, three different stories','Verdicts on UPI shares only; channel migration is not measured',pairs_html),
 NPCI+'; Jubilant FoodWorks, Swiggy and Eternal results for Jul–Sep 2026. Exhibit 16 uses groceries (5411) only; in Exhibit 17, food at home also includes dairy, meat and bakeries. The 2022→2023 jump in eating out likely reflects restaurants adopting UPI; habits are not measured.','g-ee" style="grid-template-columns:1fr 1fr;grid-template-rows:1fr auto;row-gap:16px')

add('7 · Tax cuts','Vehicle buying jumped after the GST and rate cuts; the income-tax relief is consistent with the UPI data but not proven by it',
 pts("<b>Income tax (April 2025):</b> consumer UPI growth slowed from 44.3% to 29.6% as adoption matured, and discretionary slowed more (45.5% → 26.2%) than essentials (43.9% → 30.6%).",
     "<b>Across states,</b> the most-taxed group went from losing UPI share (−8.2) to holding it (+0.4); the least-taxed went from +6.9 to −2.6. Real consumption growth rose from 6.4% to 7.2%.",
     "<span class='pill mixed'>◐ Consistent with a tax effect, not proof</span> Maharashtra drives most of the top group's earlier fall, and unclassified UPI jumped from 26% to 42% in Apr–Jun 2025.",
     "<b>GST cut (22 Sep 2025):</b> cars +22.5%, two-wheelers +21.1% (6.1% and 4.8% the year before). Rate cuts came at the same time, so the two can't be separated.")+
 ex('Consumer UPI by financial year','₹ lakh crore and growth, 13-category basket','xITax',lg([('Essentials','var(--s1)',''),('Discretionary','var(--s2)','')]))+
 ex('Change in UPI share by taxpayer density','Log points; 21 states in three groups of 7, by positive-tax filers per 1,000 people','xTerc',lg([('FY25 vs FY24 (before)','var(--bench)',''),('FY26 vs FY25 (after)','var(--s1)','')]))+
 ex('Vehicle registrations','Million per Oct–Sep year (log scale) and growth','xVeh',lg([('2023–24','var(--bench)',''),('2024–25','var(--sky)',''),('2025–26','var(--s1)','')])),
 '<b>Source:</b> NPCI state and merchant tables; Ministry of Finance, Lok Sabha Q946 (10 Feb 2025), annexures A/B via TaxGuru (positive-tax filers, all assessee types, FY2023–24); MoHFW population projections; GST Council/CBIC notifications (22 Sep 2025 rates); Vahan4; FADA; MoSPI; analysis. Small cars and two-wheelers up to 350cc went from 28% GST to 18%; larger ones to 40%.','g-peee')

add('8 · Credit','₹11.2 lakh crore was added to non-housing consumer credit in a year; 76.5% sits in loans whose end-use is unobserved',
 pts("<b>Vehicle, durable, education and card categories</b> are 23.5% of the net increase. Vehicle, durable and education loans are normally taken to buy a specific item, though top-ups and refinancing exist.",
     "<b>Gold, personal and other loans make up the other 76.5%.</b> They may fund spending, but lenders don't report what the money is spent on.",
     "<b>A broad upswing:</b> all bank credit grew 19.4% (3 Oct 2025 → 30 Sep 2026), up from 11.4%. Gold loans: banks +83%, NBFCs +69%. Pricier gold lets households borrow more per gram; one bank has also moved some farm loans into gold loans since May 2024.",
     "These are shares of the net increase in outstanding balances, not new loans disbursed.")+
 ex('Where the extra ₹11.2 lakh crore went','Net increase in outstanding, ₹ lakh crore and share; blue = vehicle, durable, education and card categories','xCredSplit')+
 ex('Consumer credit growth by lender and loan type','% growth, year to Sep 2025 vs year to Sep 2026 (NBFCs: August)','xCredit',lg([('Year to Sep 2025','var(--bench)',''),('Year to Sep 2026','var(--s1)','')])),
 '<b>Source:</b> RBI sectoral deployment of bank credit (30 Oct 2026; banks 19 Sep 2025 → 30 Sep 2026, covering ~95% of non-food credit); RBI NBFC sectoral credit (6 Oct 2026; upper and middle layers, ~87% of NBFC credit); analysis. Housing excluded. * Indicative: NBFC August added to bank September.','g-pee')

crs='<table class="tb t-crs"><thead><tr><th>Credit line</th><th>Credit signal</th><th>Matching spending signal</th><th>Read</th></tr></thead><tbody>'+''.join(f'<tr><td style="width:120px">{r[0]}</td><td style="width:190px">{r[1]}</td><td style="width:270px">{r[2]}</td><td>{r[3]}</td></tr>' for r in CRS)+'</tbody></table>'
add('8 · Credit','Vehicle loans and purchases rebounded together; for gold and personal loans, the link to spending is unmeasured',
 exhtml('Credit next to spending','Credit growth: year to Sep 2025 → year to Sep 2026; spending signals from UPI, Vahan and company results',crs),
 '<b>Source:</b> RBI sectoral credit; Vahan4; NPCI; Counterpoint; Titan Q2 FY27 results; gold prices (ETV Bharat, 5paisa); RBI (Feb 2025 risk weights on bank lending to NBFCs and microfinance); analysis. Down-payments and EMIs can be paid by UPI, so neither dataset splits spending by how it was funded.','" style="grid-template-columns:1fr')

hyp='<table class="tb t-hyp"><thead><tr><th>Hypothesis</th><th>Verdict</th><th>Evidence</th></tr></thead><tbody>'+''.join(f'<tr><td style="width:190px">{r[0]}</td><td style="width:200px">{r[1]}</td><td>{r[2]}</td></tr>' for r in HYP)+'</tbody></table>'
add('9 · The consumer','Real consumption grew 7.2% in FY26; in late 2026 prices rose and confidence weakened',
 exhtml('Eight hypotheses, tested','Verdicts combine UPI, national accounts, credit, registrations and company results',hyp),
 '<b>Source:</b> MoSPI; RBI; NPCI; Vahan4; FADA; Counterpoint; HUL, Havells and Titan results; analysis. UPI overstates the pace of consumption because it is still taking share.','" style="grid-template-columns:1fr')

ot='<table class="tb t-out"><thead><tr><th>Signal</th><th class="n">A year earlier</th><th class="n">Latest</th><th>Read</th></tr></thead><tbody>'+''.join(f'<tr><td>{r[0]}</td><td class="n">{r[1]}</td><td class="n">{r[2]}</td><td>{r[3]}</td></tr>' for r in OUT)+'</tbody></table>'
add('9 · The consumer','Outside UPI, HUL volumes and DMart revenue are up, but confidence, inflation and staples stocks point to caution',
 exhtml('The outside view: public markets and official surveys','Company figures are Jul–Sep 2026 against Jul–Sep 2025 unless stated',ot)+
 '<div class="pts"><h4>Our read</h4><p><span class="big">7.2%</span>Real private consumption growth in FY26 (7.1% in Apr–Jun 2026): healthy and steady.</p><p><b>Company sales reflect price and mix as well as volume.</b> HUL sales +15% on 7% volume; Havells raised prices 10–25%; Titan buyers up only mid-single digits.</p><p><b>Confidence is weaker:</b> RBI urban current-situation index 96.9 → 87.9; households expect 10% inflation.</p><p><span class="tag">Our inference</span>The October rate hike and 5.5% inflation make the next two quarters the test. If company volumes hold and discretionary UPI stops slowing, the "cautious consumer" reading is wrong.</p></div>',
 '<b>Source:</b> MoSPI; RBI Consumer Confidence Survey and Household Inflation Expectations Survey (Sep 2026); PIB CPI; company results; Mint (Nifty indices). Revenue, order value and same-store growth are different measures, not volume.','" style="grid-template-columns:1fr 330px')

st=sorted(D['states']+[dict(state='India (classified)',v_pr_month=D['india_geo']['v_pr_month'],g_value=D['india_geo']['g_value'],g_count=D['india_geo']['g_count'],c_pr_month=D['india_geo']['c_pr_month'],india=1)],key=lambda r:-r['v_pr_month'])
mv=max(r['v_pr_month'] for r in st);mg=max(r['g_value'] for r in st)
srows=''
for r in st:
    col='var(--ink-3)' if r.get('india') else ('var(--s2)' if r['state']=='West Bengal' else 'var(--s1)')
    srows+=f'<tr><td{" style=\"font-weight:700\"" if r.get("india") else ""}>{r["state"]}</td><td><div style="display:flex;align-items:center;gap:6px"><span style="display:inline-block;height:8px;border-radius:2px;width:{r["v_pr_month"]/mv*90:.0f}px;background:{col}"></span>₹{r["v_pr_month"]:,}</div></td><td class="n">+{r["g_value"]:.1f}%</td><td class="n">+{r["g_count"]:.1f}%</td><td class="n">{r["c_pr_month"]}</td></tr>'
stbl=f'<table class="tb t-st"><thead><tr><th>State</th><th>₹ moved per resident a month</th><th class="n">Value growth</th><th class="n">Payment growth</th><th class="n">Payments a month</th></tr></thead><tbody>{srows}</tbody></table>'
add('10 · Geography','The south and west lead on UPI money moved per person; most metro cores run 2–3.5 times their state average',
 pts("<b>Kerala, Tamil Nadu and Jammu and Kashmir grew fastest;</b> West Bengal grew slowest in value (+11.7%) though its payment count rose 18.5%.",
     "<b>Kolkata is 3.2× West Bengal's average,</b> in line with other metros; its level is the lowest of the eight, and West Bengal's state average is also among the lowest. Hyderabad is 1.5×; Telangana's average is the highest.",
     "<b>Money moved, not income:</b> gross flows, including transfers between people. All UPI per person (₹2.5 lakh a year) is close to GDP per person (₹2.4 lakh). About 39% of UPI value has no state.",
     "<b>City populations</b> use 2011 Census shares, which understate fast-growing districts: on its 2001–11 growth trend, Bengaluru is about ₹61,500, not ₹88,300.")+
 ex('Metro core: UPI money moved per resident per month','₹, Jul–Sep 2026; label = multiple of the state average','xCity')+
 exhtml('States: UPI money moved per resident, and growth','Jul–Sep 2026; growth vs Jul–Sep 2025',stbl),
 '<b>Source:</b> NPCI state and district UPI tables; MoHFW Technical Group population projections 2011–2036; Census 2011; analysis. 22 states with 5 million+ people; includes person-to-person transfers. District data start in March 2026, so city growth rates are not yet available.','g-pee" style="grid-template-columns:255px .85fr 1.35fr')

# limits, method, sources
srcs=re.sub(r'\s+',' ',T[T.index('Sources outside NPCI'):T.index('</ul>',T.index('Sources outside NPCI'))])
srcs=re.sub(r'<a ([^>]*)>(.*?)</a>',r'<a \1 style="color:var(--s1);text-decoration:none">\2</a>',srcs); lis=re.findall(r'<li>(.*?)</li>',srcs)
lim='''<p><b>Spending per person.</b> UPI adds users and merchants every month, so UPI per resident mixes adoption with spending.</p><p><b>Category by place.</b> NPCI doesn't publish categories by state or district.</p><p><b>Most of the growth.</b> NPCI's "Others" is 45% of merchant value and took 57.8% of last year's increase; 65.9% falls outside this report's category attribution.</p><p><b>Cause and effect.</b> Tax changes, rate moves and festival timing overlap, with no untouched comparison group. The verdicts are associations backed by several sources, not causal estimates.</p><p><b>Prices.</b> UPI figures are nominal. In a Jan–Aug 2026 test using approximate category CPI proxies (inflation 0.4–10.9%), growth fell by 0.5–14.1 points and none of the 26 tested series changed sign.</p><p><b>Debt collection.</b> NPCI did not announce a reclassification; our reading rests on the size and timing of the September 2025 drop and the matching average payment of the credit-card bill category. Confirming it needs an NPCI mapping notice.</p><p><b>Revisit after the festive season.</b> This edition runs to September 2026. Diwali fell on 20 October in 2025 but falls on 8 November in 2026, and Navratri and the big online sales moved from late September to October, so October on its own will mislead. We will revisit clothing, electronics, online marketplaces and department stores once October–November 2026 data are out (expected December 2026), comparing September–November with the same months a year earlier.</p>'''
meth='''<p><b>Growth</b> <code>value ÷ value a year earlier − 1</code>, on months published in both periods.</p><p><b>CAGR</b> <code>(last year ÷ base year)^(1 ÷ years) − 1</code>, matched months.</p><p><b>Consumption part of UPI growth</b> <code>ln(1 + PFCE growth) ÷ ln(1 + UPI growth)</code>. Logs, because (1 + UPI growth) = (1 + consumption growth) × (1 + share gain) compounds; only logs split it exactly. FY26: 0.082 ÷ 0.235 = 35% (8.5 ÷ 26.5 = 32% leaves 1.4 points unassigned). Consumption = MoSPI PFCE, current prices; merchant UPI includes ~₹15 lakh crore a year of investment and repayment flows.</p><p><b>Cash share</b> <code>1 − digital consumer payments ÷ PFCE</code>; digital = UPI merchant + Aadhaar Pay + FASTag + card and wallet payments at shops, minus UPI to brokers, lenders, card bills and digital gold. Extends Bhuyan, RBI Bulletin (Oct 2024); reproduces its FY23–FY24 digital totals.</p><p><b>Break-adjusted growth</b> (sensitivity): pre-break months scaled by Sep ÷ Aug 2025.</p><p><b>Per resident</b> <code>classified UPI ÷ population ÷ months</code>; <b>state share change</b> <code>100 × ln(share ÷ share last FY)</code>.</p><p><b>Checks.</b> All plotted values and text numbers were checked against raw files or primary sources; changed values and all 218 scoreboard fields were recomputed from raw data.</p>'''
P.append(f'''<section class="pg"><div class="trk"><span>11–12 · Limits, method and sources</span><span>Where is Indian consumption going? · Soumyadeep Chakraborty · November 2026</span></div>
<h2 class="act">What this data can't tell us, and how every number was built</h2>
<div class="body" style="grid-template-columns:1fr;margin-top:14px"><div class="cols3"><div class="pts" style="font-size:11.5px"><h4>Limits</h4>{lim}</div><div class="pts" style="font-size:11.5px"><h4>Method</h4>{meth}</div><div class="pts" style="font-size:10.8px"><h4>Sources</h4><p><b>NPCI</b> UPI ecosystem statistics via the measure.thisindianlife.today archive (npci.org.in was unreachable on 1 Nov 2026), spot-checked against NPCI's August 2025 table; P2M totals match NPCI's P2P/P2M table every month.</p><ul class="src" style="margin:0;padding-left:14px">{''.join(f'<li>{x}</li>' for x in lis)}</ul></div></div></div>
<div class="ft"><div><b>Author:</b> Soumyadeep Chakraborty. © 2026, CC BY 4.0: share and adapt with credit. UPI figures are nominal rupees. ₹1 lakh crore = ₹1 trillion. FY = April–March. Data, code and the interactive version: <a href="https://github.com/sdchak89/india-consumption-tracker">github.com/sdchak89/india-consumption-tracker</a>.</div><div class="pn">{pn}</div></div></section>''')

doc=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Where is Indian consumption going?</title>{css_links}<style>{CSS}</style>
<script src="{(NODE/"chart.js"/"dist"/"chart.umd.js").as_uri()}"></script></head><body>
{''.join(P)}
<script>const D={json.dumps(D)};const TK={json.dumps(TK)};window.CARDS={cj};
{helpers}
{charts}
document.fonts.ready.then(()=>{{deckCharts(D,TK);window.__done=1}});
</script></body></html>'''
(ROOT/'build').mkdir(exist_ok=True)
open(ROOT/'build'/'deck.html','w').write(doc)
print('pages',len(P),'exhibits',EXN[0],len(doc))
