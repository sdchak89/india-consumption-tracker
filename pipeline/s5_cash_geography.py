"""Step 5. Cash share of consumption by quarter (with and without financial flows), the
debt-collection break adjustment, geography tables and category registry entries.
Reads build/d2.json, build/categories.json and step 2 outputs; writes build/d3.json."""
import json
import numpy as np
import pandas as pd
from common import DATA, BUILD, load_npci, read_json, write_json, Registry

v, c, names = load_npci()
O = read_json("d2.json")
R = Registry(read_json("reg2.json"))
reg = R.add
cat = read_json("categories.json")
for k in ["prof", "ser", "food", "foodshare", "liquor", "dc", "brokers_monthly"]:
    O[k] = cat[k]
geo = read_json("india_geo.json")

# cash quarterly with rupees
cq=pd.read_csv(DATA/'rbi'/'cash_share_quarterly.csv').dropna(subset=['pfce_current_inr_cr'])
lab=lambda q: {'Q1':'Apr–Jun','Q2':'Jul–Sep','Q3':'Oct–Dec','Q4':'Jan–Mar'}[q.split()[1]]+" "+(q[2:4] if q.split()[1]!='Q4' else q[5:7])
O['cashQ']=[dict(q=lab(r.q),pfce=round(r.pfce_current_inr_cr/1e5,1),dig_lo=round(r.pfce_digital_L_inr_cr/1e5,1),dig_hi=round(r.pfce_digital_U_inr_cr/1e5,1),cash_lo=round(r.cash_share_pct_lower,1),cash_hi=round(r.cash_share_pct_upper,1)) for r in cq.itertuples()]
def qmonths(q):
    fy,qq=q.split(); y=int(fy[:4]); n=int(qq[1]); st={1:(y,4),2:(y,7),3:(y,10),4:(y+1,1)}[n]; return pd.date_range(f'{st[0]}-{st[1]:02d}-01',periods=3,freq='MS')
for x,r in zip(O['cashQ'],cq.itertuples()):
    f_=v.loc[qmonths(r.q),['6211','7322','5412','5413']].sum().sum(); pf=r.pfce_current_inr_cr
    dl=r.pfce_digital_L_inr_cr-f_; du=r.pfce_digital_U_inr_cr-f_
    x['fin']=round(f_/1e5,2); x['adj_lo']=round((1-du/pf)*100,1); x['adj_hi']=round((1-dl/pf)*100,1)
    x['adig_mid_rs']=round(((dl+du)/2)/1e5,1); x['acash_mid_rs']=round((pf-(dl+du)/2)/1e5,1)
    x['dig_mid']=round(((r.pfce_digital_L_inr_cr+r.pfce_digital_U_inr_cr)/2)/1e5,1); x['cash_mid_rs']=round((pf-(r.pfce_digital_L_inr_cr+r.pfce_digital_U_inr_cr)/2)/1e5,1)
d7=v['7322']; c7=c['7322']; f=d7['2025-09-01']/d7['2025-08-01']; fc=c7['2025-09-01']/c7['2025-08-01']
O['dc']['adj_v']=round((d7.loc['2025-10':'2026-09'].sum()/(d7.loc['2024-10':'2025-08'].sum()*f+d7['2025-09-01'])-1)*100,1)
O['dc']['adj_c']=round((c7.loc['2025-10':'2026-09'].sum()/(c7.loc['2024-10':'2025-08'].sum()*fc+c7['2025-09-01'])-1)*100,1)
O['dc']['factor_v']=round(f,3)
reg('cash_share_quarterly',json.dumps([O['cashQ'][0],O['cashQ'][7],O['cashQ'][-1]]),'adjusted (adj_*) removes merchant UPI to brokers 6211, debt collection 7322, digital gold 5412, credit-card bills 5413 from digital; '+'cash share = 1 − digital consumption payments ÷ PFCE; digital L = UPI P2M + Aadhaar Pay + NETC + card PoS + PPI wallet + PPI card PoS; U = L + card/PPI "others"; cash lower = 1−U/PFCE, upper = 1−L/PFCE','RBI PSI, NPCI, MoSPI; method of Bhuyan, RBI Bulletin Oct 2024')
# geography
S=pd.read_csv(BUILD/'states.csv'); C=pd.read_csv(BUILD/'cities.csv'); Wc=pd.read_csv(BUILD/'clusters.csv')
O['states']=S[S.pop_mn>=5].to_dict('records'); O['cities']=C.to_dict('records'); O['clusters']=Wc.to_dict('records')
O['india_geo']=geo
reg('states_JulSep2026',S[S.pop_mn>=5][['state','v_pr_month','g_value','g_count','c_pr_month']].to_csv(index=False),'classified UPI value (P2P+P2M) Jul–Sep 2026 ÷ 2026 population ÷ 3; growth vs Jul–Sep 2025 (unclassified share 38.9% → 39.0%, stable)','NPCI state table via archive; MoHFW 2026 population projection')
reg('cities_JulSep2026',C[['city','districts','pop_mn','v_pr_month','state_v_pr_month','city_vs_state','pop_2011_mn','growth_vs_state','pop_fixed_share_mn','v_pr_month_fixed_share']].to_csv(index=False),'core city district(s) classified UPI value Jul–Sep 2026 ÷ 2026 est population ÷ 3; population = Census 2011 on today\'s boundary × (1 + r × state growth 2011–26), r = district ÷ state growth 2001–11 (r = 1 for enlarged Chennai); fixed-share columns use 2011 district share of the state for comparison','NPCI district table via archive; Census 2001 and 2011 (Table A-2); MoHFW projection')
reg('india_geo','₹12,733 per resident per month classified UPI, Jul–Sep 2026; +19.0% value, +20.0% count vs Jul–Sep 2025','sum classified states','NPCI state table')
# category numbers
P=O['prof']
for m,d in P.items():
    reg('category_'+m,json.dumps({k:d.get(k) for k in ['name','val_26_cr','yoy_v','yoy_c','base','years','val_cagr','cnt_cagr','tot_cagr_same','tkt_base','tkt_25','tkt_26','share_base','share_26','yoy_v_prev','yoy_c_prev']}),'Oct25–Sep26 vs Oct24–Sep25 on months published in both; CAGR from earliest Oct–Sep year with ≥9 published months; ticket = value ÷ count','NPCI MCC table')
reg('debt_collection_break',json.dumps(O['dc']),'monthly values; left ticket = (Aug25 value − Sep25 value) ÷ (Aug25 count − Sep25 count)','NPCI MCC table (7322, 5413)')
reg('food_share',json.dumps(O['foodshare']),'(restaurants + fast food) ÷ (restaurants + fast food + groceries), Oct–Sep years','NPCI MCC table')
reg('liquor_share',json.dumps(O['liquor']),'liquor shops ÷ (liquor shops + bars), matched months','NPCI MCC table')
write_json(O, "d3.json")
write_json(R.rows, "reg3.json")
print("step 5:", len(O), "blocks,", len(R.rows), "registered numbers")
