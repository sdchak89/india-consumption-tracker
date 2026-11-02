"""Step 4. Income-tax test (fixed basket by financial year, state terciles by taxpayer density),
vehicle registrations and consumer credit. Reads build/d1.json; writes build/d2.json."""
import json
import numpy as np
import pandas as pd
from common import DATA, r1, load_npci, read_json, write_json, Registry

v, c, names = load_npci()
O = read_json("d1.json")
R = Registry(read_json("reg1.json"))
reg = R.add

# --- income tax: FY windows on fixed basket; financial flows separately
FY={'FY24':('2023-04','2024-03'),'FY25':('2024-04','2025-03'),'FY26':('2025-04','2026-03')}
ess=['5411','5451','5422','5462','5912','4814','4900','5311','5541']; dis=['5812','5814','5732','5813']; fin=['6211','7322']
def tot(ms,a,b): return v[ms].loc[a:b].sum().sum()
it=[]
for k,(a,b) in FY.items():
    it.append(dict(fy=k,cons=tot(ess+dis,a,b)/1e5,ess=tot(ess,a,b)/1e5,dis=tot(dis,a,b)/1e5,fin=tot(fin,a,b)/1e5,allp2m=v['total'].loc[a:b].sum()/1e5))
for i in range(1,3):
    for f in ['cons','ess','dis','fin','allp2m']: it[i]['g_'+f]=round((it[i][f]/it[i-1][f]-1)*100,1)
for x in it:
    for f in ['cons','ess','dis','fin','allp2m']: x[f]=round(x[f],2)
O['itax']=it
# income tax: restaurant / eating out / electronics FY growth
cat_fy={}
for m in ['5812','5814','5732','5411','5541','5912']:
    g=[]
    for k,(a,b) in FY.items(): g.append(v[m].loc[a:b].sum())
    cat_fy[m]=dict(name=names[m],g25=round((g[1]/g[0]-1)*100,1),g26=round((g[2]/g[1]-1)*100,1))
O['itax_cat']=cat_fy
# state terciles
# States ranked by positive-tax filers per 1,000 people (FY24). Share change = 100 x ln(share / share a year
# earlier), using each state's share of classified UPI value by financial year, at full precision.
st=pd.read_csv(DATA/'tax'/'state_income_tax.csv').sort_values('filers_per_1000',ascending=False)
sm=pd.read_csv(DATA/'npci'/'state_monthly.csv.gz'); sm=sm[(sm.metric=='value')&(sm.geography!='Unclassified (no state reported)')].copy()
sm['fy']=[int(p[:4])+(1 if int(p[5:7])>=4 else 0) for p in sm.period]
sh=sm[sm.fy.isin([2024,2025,2026])].groupby(['fy','geography']).value.sum().unstack(0); sh=sh/sh.sum()
pp=pd.read_csv(DATA/'macro'/'state_population_projection.csv'); pp=pp[pp.year==2026].set_index('state').population_persons
PN={'Jammu and Kashmir':'Jammu & Kashmir (UT)','Uttarakhand':'Uttaranchal','Delhi':'NCT of Delhi'}
st['pop']=[pp[PN.get(x,x)] for x in st.state]
st['pre']=[100*np.log(sh.loc[x,2025]/sh.loc[x,2024]) for x in st.state]
st['post']=[100*np.log(sh.loc[x,2026]/sh.loc[x,2025]) for x in st.state]
hi=st.head(7); lo=st.tail(7); mid=st.iloc[7:14]
def avg(d,col): return round(float(np.average(d[col],weights=d['pop'])),1)
terc=[dict(g='Most taxpayers (top 7 states)',states=', '.join(hi.state),filers=round(hi.filers_per_1000.mean(),1),pre=avg(hi,'pre'),post=avg(hi,'post')),
      dict(g='Middle 7',states=', '.join(mid.state),filers=round(mid.filers_per_1000.mean(),1),pre=avg(mid,'pre'),post=avg(mid,'post')),
      dict(g='Fewest taxpayers (bottom 7)',states=', '.join(lo.state),filers=round(lo.filers_per_1000.mean(),1),pre=avg(lo,'pre'),post=avg(lo,'post'))]
O['terc']=terc
reg('income_tax_terciles',json.dumps(terc),'population-weighted mean of log change (×100) in state share of classified UPI value; pre = FY25 vs FY24, post = FY26 vs FY25; states ranked by positive-tax filers per 1,000 (FY24)','NPCI state table; CBDT filers via Lok Sabha Q946')
reg('income_tax_fy_basket',json.dumps(it),'FY sums of fixed 13-category basket; financial = brokers + debt collection','NPCI MCC table')
# --- vehicles monthly
vh=pd.read_csv(DATA/'vahan'/'vahan_state_monthly.csv.gz',usecols=['vehicle_class','year','month','registrations'])
VC={'cars':['MOTOR CAR'],'tw':['M-CYCLE/SCOOTER','MOPED','MOTORISED CYCLE (CC > 25CC)']}
vh['m']=vh.year.astype(str)+'-'+vh.month.astype(int).map('{:02d}'.format)
vm={}
for k,cl in VC.items(): vm[k]=vh[vh.vehicle_class.isin(cl)].groupby('m').registrations.sum()
VM=pd.DataFrame(vm); VM=VM[VM.index<='2026-09']
VM['g_c']=(VM.cars/VM.cars.shift(12)-1)*100; VM['g_t']=(VM.tw/VM.tw.shift(12)-1)*100
O['vehM']=[dict(m=i,cars=int(r.cars),tw=int(r.tw),gc=r1(r.g_c),gt=r1(r.g_t)) for i,r in VM.loc['2024-01':].iterrows()]
def s12(s,a,b): return s.loc[a:b].sum()
vy={}
for k in ['cars','tw']:
    p0=s12(VM[k],'2023-10','2024-09'); p1=s12(VM[k],'2024-10','2025-09'); p2=s12(VM[k],'2025-10','2026-09')
    vy[k]=dict(y24=int(p0),y25=int(p1),y26=int(p2),g25=round((p1/p0-1)*100,1),g26=round((p2/p1-1)*100,1))
O['vehY']=vy
reg('vehicles',json.dumps(vy),'Vahan registrations, sums Oct–Sep; cars = MOTOR CAR; two-wheelers = M-CYCLE/SCOOTER + MOPED + MOTORISED CYCLE','Vahan4 dashboard')
# --- credit (verified against RBI xlsx)
cr=pd.read_csv(DATA/'rbi'/'credit_growth_prepost.csv')
O['credit']=cr.to_dict('records')
O['credit_all_bank']=dict(prev=11.4,now=19.4,note='All bank credit, year to 3 Oct 2025 vs 30 Sep 2026')
O['credit_fd']=dict(prev=14.3,now=53.3)
reg('credit_lines',cr.to_csv(index=False),'YoY growth of outstanding credit; banks 19 Sep 2025/20 Sep 2024 and 30 Sep 2026/19 Sep 2025; NBFC Aug','RBI SIBC 30 Oct 2026 (SIBC30102026E.xlsx); RBI NBFC sectoral 6 Oct 2026')
reg('credit_context','All bank credit +11.4% (Oct 2025 YoY) → +19.4% (Sep 2026 YoY); advances against FDs +14.3% → +53.3%','Statement 1 rows I and 4.3','RBI SIBC30102026E.xlsx')
write_json(O, "d2.json")
write_json(R.rows, "reg2.json")
print("step 4:", len(O), "blocks,", len(R.rows), "registered numbers")
