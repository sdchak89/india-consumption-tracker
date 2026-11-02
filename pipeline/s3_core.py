"""Step 3. Core series: merchant UPI by year and month, the fixed category basket,
where last year's increase went, P2P vs P2M coverage, the consumption decomposition
and the cash/cards/currency bridge. Reads data/npci and data/macro; writes build/d1.json."""
import json
import numpy as np
import pandas as pd
from common import DATA, W, WL, r1, r2, ym, win, load_npci, write_json, Registry

v, c, names = load_npci()
O = {}
R = Registry()
reg = R.add

# Check: the category table's total row matches NPCI's P2P/P2M table
pm=pd.read_csv(DATA/'npci'/'p2p_p2m_monthly.csv').pivot_table(index='period',columns=['series','metric'],values='value')
chk=pd.DataFrame({'cat_total':v['total'].values},index=[ym(i) for i in v.index]).join(pm[('P2M','value')].rename('p2m')/1e7)
chk['diff%']=(chk.cat_total/chk.p2m-1)*100
print('P2M total in category table vs P2P/P2M table, max abs diff %:', round(chk['diff%'].abs().max(),3))
# 1. yearly direction
yr=[]
for k,(a,b) in W.items():
    val=v['total'].loc[a:b].sum(); cnt=c['total'].loc[a:b].sum(); yr.append(dict(y=WL[k],v=round(val/1e5,1),c=round(cnt/1e3,1),t=round(val*1e7/(cnt*1e6)),_v=val,_c=cnt))
for i in range(1,len(yr)):
    yr[i]['gv']=round((yr[i]['_v']/yr[i-1]['_v']-1)*100,1); yr[i]['gc']=round((yr[i]['_c']/yr[i-1]['_c']-1)*100,1)
for y in yr: y.pop('_v'); y.pop('_c')
O['dirY']=yr
for y in yr: reg('merchant_upi_'+y['y'],f"₹{y['v']} lakh cr; {y['c']} bn payments; avg ₹{y['t']}"+(f"; value growth {y['gv']}%, count growth {y['gc']}%" if 'gv' in y else ''),'sum of NPCI monthly merchant (P2M) totals over Oct–Sep','NPCI UPI merchant category table (total row), via archive')
# 2. monthly
ty=(v['total']/v['total'].shift(12)-1)*100; tc=(c['total']/c['total'].shift(12)-1)*100
g=v['5816'].fillna(0); vx=v['total']-g; tx=(vx/vx.shift(12)-1)*100
O['dirM']=[{'m':ym(i),'val':round(v['total'][i]/1e3,1),'v':r1(ty[i]),'c':r1(tc[i]),'x':r1(tx[i]) if i>=pd.Timestamp('2025-09-01') else None} for i in v.loc['2022-01':].index]
# 3. basket
ess=['5411','5451','5422','5462','5912','4814','4900','5311','5541']; dis=['5812','5814','5732','5813']
E=v[ess].sum(axis=1,min_count=len(ess)); Dd=v[dis].sum(axis=1,min_count=len(dis))
O['basketM']=[{'m':ym(i),'e':round(E[i]/1e3,1),'d':round(Dd[i]/1e3,1),'ge':r1((E[i]/E.shift(12)[i]-1)*100),'gd':r1((Dd[i]/Dd.shift(12)[i]-1)*100)} for i in v.loc['2023-10':'2026-09'].index]
by=[]
for k in ['Y23','Y24','Y25','Y26']:
    a,b=W[k]; by.append(dict(y=WL[k],e=round(E.loc[a:b].sum()/1e5,2),d=round(Dd.loc[a:b].sum()/1e5,2),_e=E.loc[a:b].sum(),_d=Dd.loc[a:b].sum()))
for i in range(1,len(by)): by[i]['ge']=round((by[i]['_e']/by[i-1]['_e']-1)*100,1); by[i]['gd']=round((by[i]['_d']/by[i-1]['_d']-1)*100,1)
for y in by: y.pop('_e'); y.pop('_d')
O['basketY']=by
for b_ in by: reg('basket_'+b_['y'],f"essentials ₹{b_['e']}L cr, discretionary ₹{b_['d']}L cr"+(f"; growth {b_['ge']}% / {b_['gd']}%" if 'ge' in b_ else ''),'sum of fixed 13-category basket over Oct–Sep','NPCI MCC table')
# 4. families
FAM={'Groceries & food at home':['5411','5451','5422','5462','5441','5499'],'Eating out':['5812','5814','5811'],'Fuel & transport':['5541','4121','4112','4784','5172'],
 'Shopping (retail, apparel, electronics)':['5732','5722','4812','7622','5691','5651','5611','5699','5137','5262','5311','5331','5399','5999','5815'],
 'Bills (telecom, utilities)':['4814','4900','4899'],'Health & personal care':['5912','7230','7298','7299'],'Alcohol & tobacco':['5921','5813','5993'],
 'Investments (brokers)':['6211','5412'],'Loan & card repayments':['7322','5413'],'Government services':['9399'],
 'Gaming & betting':['5816','7995'],'Other named (business, finance, misc.)':['6012','6540','7399','7372','8999','4214','4215','5111','5943','7011','5818','7994']}
GRP={'Groceries & food at home':'Consumption','Eating out':'Consumption','Fuel & transport':'Consumption','Shopping (retail, apparel, electronics)':'Consumption','Bills (telecom, utilities)':'Consumption','Health & personal care':'Consumption','Alcohol & tobacco':'Consumption',
 'Investments (brokers)':'Financial flows','Loan & card repayments':'Financial flows','Government services':'Government','Gaming & betting':'Other','Other named (business, finance, misc.)':'Other'}
allm=set(m for l in FAM.values() for m in l); missing=[m for m in v.columns if m not in allm and m not in('total','others')]
fam=[]; tot_inc=v['total'].loc[W['Y26'][0]:W['Y26'][1]].sum()-v['total'].loc[W['Y25'][0]:W['Y25'][1]].sum()
expl=0
for f,ms in FAM.items():
    d0=d1=0; n=0
    for m in ms:
        if m not in v: continue
        a=win(v[m],'Y25'); b=win(v[m],'Y26'); mk=a.notna()&b.notna()
        if mk.sum()<10: continue
        d0+=a[mk].sum(); d1+=b[mk].sum(); n+=1
    if n==0: continue
    fam.append(dict(f=f,grp=GRP[f],inc=round((d1-d0)/1e5,2),g=round((d1/d0-1)*100,1),base=round(d0/1e5,2),now=round(d1/1e5,2),_inc=d1-d0))
    expl+=d1-d0
res=tot_inc-expl
fam.append(dict(f="NPCI 'Others' + categories entering or leaving NPCI's list",grp='Not broken out',inc=round(res/1e5,2),g=None,_inc=res))
# share of the total increase, from unrounded rupee amounts (digital gold, 5412, has too few matched months and falls in the residual)
for x in fam: x['pct']=round(x.pop('_inc')/tot_inc*100,1)
O['fam']=sorted(fam,key=lambda x:-x['inc']); O['fam_total']=round(tot_inc/1e5,1)
for x in O['fam']: reg('increment_'+x['f'],f"+₹{x['inc']}L cr ({x['pct']}% of increase)"+(f", growth {x['g']}%" if x['g'] is not None else ''),'Oct25–Sep26 minus Oct24–Sep25, months published in both years per category; residual = total increase minus named','NPCI MCC table')
# 5. coverage L12
L=pm.loc['2025-10':'2026-09']
allv=L[('TOTAL','value')].sum()/1e12; p2p=L[('P2P','value')].sum()/1e12; p2m=L[('P2M','value')].sum()/1e12
allc=L[('TOTAL','volume')].sum()/1e9; p2pc=L[('P2P','volume')].sum()/1e9; p2mc=L[('P2M','volume')].sum()/1e9
cov={}
for f,ms in FAM.items():
    cov[GRP[f]]=cov.get(GRP[f],0)+sum(v[m].loc['2025-10':'2026-09'].sum() for m in ms if m in v)
cov['Not broken out']=v['others'].loc['2025-10':'2026-09'].sum()
cov={k:round(x/1e5,1) for k,x in cov.items()}
O['coverage']=dict(all=round(allv,1),p2p=round(p2p,1),p2m=round(p2m,1),allc=round(allc,1),p2pc=round(p2pc,1),p2mc=round(p2mc,1),parts=cov,
   p2m_val_share=round(p2m/allv*100,1),p2m_cnt_share=round(p2mc/allc*100,1),p2p_tkt=round(p2p*1e12/(p2pc*1e9)),p2m_tkt=round(p2m*1e12/(p2mc*1e9)))
reg('coverage_L12',json.dumps(O['coverage']),'Oct 2025–Sep 2026 sums; P2M split by MCC family','NPCI P2P/P2M table + MCC table')
# 6. decomposition + bridge
S=pd.read_csv(DATA/'macro'/'size_ratios_fy.csv').set_index('fy')
ga=pd.read_csv(DATA/'macro'/'gdp_pfce_annual.csv').pivot_table(index='period',columns='series',values='value')
dec=[]
for fy0,fy1 in [('2022-23','2023-24'),('2023-24','2024-25'),('2024-25','2025-26')]:
    gu=S.loc[fy1,'p2m_cr']/S.loc[fy0,'p2m_cr']; gp=ga.loc[fy1,'PFCE_current']/ga.loc[fy0,'PFCE_current']; gr=ga.loc[fy1,'PFCE_constant_2022-23']/ga.loc[fy0,'PFCE_constant_2022-23']
    dec.append(dict(fy='FY'+fy1[-2:],upi=round((gu-1)*100,1),pfce_nom=round((gp-1)*100,1),pfce_real=round((gr-1)*100,1),share_gain=round((gu/gp-1)*100,1),cons_part=round(np.log(gp)/np.log(gu)*100),
        d_upi=round((S.loc[fy1,'p2m_cr']-S.loc[fy0,'p2m_cr'])/1e5,1),d_pfce=round((ga.loc[fy1,'PFCE_current']-ga.loc[fy0,'PFCE_current'])/1e5,1)))
atm=pd.read_csv(DATA/'macro'/'atm_cash_withdrawals_monthly.csv'); atm=atm[(atm.series=='ATM_cash_withdrawal_total')&(atm.metric=='value')].copy()
def fy(p): y,m=map(int,p.split('-')); y0=y if m>=4 else y-1; return f"{y0}-{str(y0+1)[2:]}"
atm['fy']=atm.period.map(fy); A_=atm.groupby('fy').value.sum()/1e5
cs=pd.read_csv(DATA/'macro'/'card_spend_monthly.csv'); cs=cs[(cs.series=='Card_payments_total')&(cs.metric=='value')].copy(); cs['fy']=cs.period.map(fy); C_=cs.groupby('fy').value.sum()/1e5
cu=pd.read_csv(DATA/'macro'/'currency_annual_fy_end.csv'); cu=cu[cu.series=='Currency_with_public'].set_index('period').value/1e5
for d_ in dec:
    f1='20'+str(int(d_['fy'][2:])-1)+'-'+d_['fy'][2:]; f0='20'+str(int(d_['fy'][2:])-2)+'-'+str(int(d_['fy'][2:])-1)
    d_['d_atm']=round(A_[f1]-A_[f0],1); d_['d_cards']=round(C_[f1]-C_[f0],1); d_['d_cwp']=round(cu[f1]-cu[f0],1)
O['dec']=dec
for d_ in dec: reg('decomp_'+d_['fy'],json.dumps(d_),'merchant UPI growth = (1+nominal PFCE growth)×(1+share gain); consumption part = ln(1+PFCE g)/ln(1+UPI g); ₹ changes in lakh crore','size_ratios_fy.csv (NPCI/RBI PSI), MoSPI NAS 31 Aug 2026, RBI PSI ATM & cards, RBI Handbook currency')
O['cashflow']=[dict(fy='FY'+k[-2:],atm=round(A_[k],1),cards=round(C_[k],1),cwp=round(cu[k],1),p2m=round(S.loc[k,'p2m_cr']/1e5,1),pfce=round(ga.loc[k,'PFCE_current']/1e5,1)) for k in ['2022-23','2023-24','2024-25','2025-26']]
for x in O['cashflow']: reg('payments_'+x['fy'],json.dumps(x),'annual sums (ATM, cards), FY-end stock (currency with public), ₹ lakh crore','RBI PSI; RBI Handbook Table 36; MoSPI')
macro=dict(pfce_real={k:round((ga.loc[k,'PFCE_constant_2022-23']/ga.shift(1).loc[k,'PFCE_constant_2022-23']-1)*100,2) for k in ['2023-24','2024-25','2025-26']},
           pfce_nom={k:round((ga.loc[k,'PFCE_current']/ga.shift(1).loc[k,'PFCE_current']-1)*100,2) for k in ['2023-24','2024-25','2025-26']})
Q=pd.read_csv(DATA/'macro'/'gdp_pfce_quarterly.csv').pivot_table(index='period',columns='series',values='value'); qg=(Q/Q.shift(4)-1)*100
macro['q1fy27']=dict(pfce_real=round(qg.loc['2026-27 Q1','PFCE_constant_2022-23'],2),pfce_nom=round(qg.loc['2026-27 Q1','PFCE_current'],2),gdp_nom=round(qg.loc['2026-27 Q1','GDP_current'],2),gdp_real=round(qg.loc['2026-27 Q1','GDP_constant_2022-23'],2),pfce_real_q1fy26=round(qg.loc['2025-26 Q1','PFCE_constant_2022-23'],2))
P=pd.read_csv(DATA/'macro'/'state_population_projection.csv'); pt=P.groupby('year').population_persons.sum(); macro['pop_cagr_21_26']=round(((pt[2026]/pt[2021])**(1/5)-1)*100,2)
O['macro']=macro; reg('macro',json.dumps(macro),'growth from levels','MoSPI NAS 31 Aug 2026 vintage (base 2022-23); MoHFW population projections 2020')
write_json(O, "d1.json")
write_json(R.rows, "reg1.json")
print("step 3:", len(O), "blocks,", len(R.rows), "registered numbers")
