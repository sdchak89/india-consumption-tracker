// Deck charts. Depends on helpers.js (tok, pct, pct0, rs, mlab, vlab, refline, markers, ln, bar, monthX, base).
function deckCharts(D,TK){
  base();Chart.defaults.font.size=11;Chart.defaults.devicePixelRatio=2.5;
  const s1=tok('--s1'),s2=tok('--s2'),s3=tok('--s3'),bench=tok('--bench'),sky=tok('--sky'),navy=tok('--navy');
  const add=(id,cfg)=>{const el=document.getElementById(id);if(el)new Chart(el,cfg)};
  const vy=(cb,extra)=>Object.assign({grid:{color:tok('--grid')},ticks:{callback:cb}},extra||{});
  const yl2=s=>{const q=String(s).split('–');return q.length===2?[q[0]+'–',q[1]]:s};
  const noX={grid:{display:false},ticks:{maxRotation:0,autoSkip:false}};

  // 1 scope: three 100% bars
  const c=D.coverage,P=c.parts;
  const sc=[['P2P',bench,[70.435,36.986,null],['P2P ₹'+c.p2p+'L cr · '+Math.round(c.p2p/c.all*100)+'%','P2P '+c.p2pc+' bn · '+Math.round(c.p2pc/c.allc*100)+'%']],
    ['Merchant',s1,[29.565,63.014,null],['Merchant ₹'+c.p2m+'L cr · '+Math.round(c.p2m_val_share)+'%','Merchant '+c.p2mc+' bn · '+Math.round(c.p2m_cnt_share)+'%']],
    ['Consumption',navy,[null,null,37.302],[null,null,'Consumption ₹'+P['Consumption']+'L cr · '+Math.round(P['Consumption']/c.p2m*100)+'%']],
    ['Financial',s2,[null,null,16.382],[null,null,'Financial ₹'+P['Financial flows']+'L · '+Math.round(P['Financial flows']/c.p2m*100)+'%']],
    ['Government',s3,[null,null,1.239],[null,null,'']],
    ['Others',bench,[null,null,45.077],[null,null,"NPCI 'Others' ₹"+P['Not broken out']+'L cr · '+Math.round(P['Not broken out']/c.p2m*100)+'%']]];
  sc[0][1]=bench;
  add('xScope',{type:'bar',data:{labels:['All UPI value (₹343.2L cr)','All UPI payments (268 bn)','Merchant UPI value (₹101.5L cr)'],datasets:sc.map(r=>({label:r[0],data:r[2],backgroundColor:r[1],stack:'a',barPercentage:.62,borderRadius:2}))},
    options:{indexAxis:'y',scales:{x:{stacked:true,max:100,grid:{display:false},ticks:{callback:v=>v+'%'}},y:{stacked:true,grid:{display:false},ticks:{font:{size:11.5,weight:'600'},color:tok('--ink')}}},
    plugins:{vlab:{inside:true,size:11,minSize:70,bold:true,fmt:(v,d,i)=>sc[d][3][i]||null}}},plugins:[vlab]});

  // 2 annual merchant UPI
  add('xDirY',{type:'bar',data:{labels:D.dirY.map(r=>yl2(r.y)),datasets:[bar('Value',s1,D.dirY.map(r=>r.v),{maxBarThickness:54})]},options:{layout:{padding:{top:30}},scales:{x:noX,y:vy(v=>'₹'+v,{beginAtZero:true})},plugins:{vlab:{size:11,bold:true,fmt:(v,d,i)=>['₹'+v+'L cr',D.dirY[i].gv!=null?pct(D.dirY[i].gv):'']}}},plugins:[vlab]});
  // 3 monthly growth lines
  const M=D.dirM.filter(r=>r.m>='2022-01');
  add('xDirG',{type:'line',data:{labels:M.map(r=>r.m),datasets:[ln(s1,M.map(r=>r.v),{label:'Value'}),ln(s2,M.map(r=>r.c),{label:'Payments'}),ln(bench,M.map(r=>r.x),{label:'Value without games',borderDash:[5,4]})]},
    options:{layout:{padding:{right:94}},scales:{x:monthX(9),y:vy(v=>v+'%')},plugins:{markers:{spill:true,items:[['2025-04','Tax relief','','L'],['2025-09','GST cut']]},vlab:{lineEnd:true,colorize:true,size:10.5,fmt:(v,d)=>['Value','Payments','Ex-games'][d]+' '+pct0(v)}}},plugins:[markers,vlab]});
  // 4-5 basket
  add('xBasketY',{type:'bar',data:{labels:D.basketY.map(r=>yl2(r.y)),datasets:[bar('Essentials',s1,D.basketY.map(r=>r.e)),bar('Discretionary',s2,D.basketY.map(r=>r.d))]},options:{layout:{padding:{top:30}},scales:{x:noX,y:vy(v=>'₹'+v,{beginAtZero:true})},plugins:{vlab:{size:10.5,fmt:(v,d,i)=>{const r=D.basketY[i];const g=d===0?r.ge:r.gd;return['₹'+v.toFixed(1),g!=null?pct0(g):'']}}}},plugins:[vlab]});
  add('xBasketG',{type:'line',data:{labels:D.basketM.map(r=>r.m),datasets:[ln(s1,D.basketM.map(r=>r.ge),{label:'Essentials'}),ln(s2,D.basketM.map(r=>r.gd),{label:'Discretionary'})]},options:{layout:{padding:{right:146}},scales:{x:monthX(6),y:vy(v=>v+'%')},plugins:{vlab:{lineEnd:true,colorize:true,size:10.5,fmt:(v,d)=>['Essentials','Discretionary'][d]+' '+pct0(v)+' (Sep)'}}},plugins:[vlab]});
  // 6 decomposition
  add('xDec',{type:'bar',data:{labels:D.dec.map(r=>r.fy),datasets:[bar('Consumption part',s1,D.dec.map(r=>r.cons_pts),{stack:'a',maxBarThickness:70}),bar('Share gain part',bench,D.dec.map(r=>r.share_pts),{stack:'a',maxBarThickness:70})]},
    options:{layout:{padding:{top:22}},scales:{x:{stacked:true,grid:{display:false}},y:vy(v=>v+'%',{stacked:true,beginAtZero:true})},plugins:{vlab:{inside:true,bold:true,fmt:(v,d,i)=>d===0?D.dec[i].cons_part+'%':(100-D.dec[i].cons_part)+'%'}}},
    plugins:[vlab,{id:'tot',afterDatasetsDraw(ch){const{ctx}=ch;ctx.save();ctx.font='600 11.5px '+tok('--body');ctx.fillStyle=tok('--ink');ctx.textAlign='center';ch.getDatasetMeta(1).data.forEach((el,i)=>ctx.fillText('UPI '+pct(D.dec[i].upi),el.x,el.y-6));ctx.restore();}}]});
  // 7 bridge
  const dl=D.dec[D.dec.length-1];const BR=[['Merchant UPI',dl.d_upi],['Consumption (all channels)',dl.d_pfce],['Card payments',dl.d_cards],['ATM cash withdrawals',dl.d_atm],['Cash held by public (stock)',dl.d_cwp]];
  add('xBridge',{type:'bar',data:{labels:BR.map(r=>r[0]),datasets:[{data:BR.map(r=>r[1]),backgroundColor:BR.map((r,i)=>i===0?s1:i===1?s3:r[1]<0?s2:bench),borderRadius:3,barPercentage:.68}]},options:{indexAxis:'y',layout:{padding:{right:64}},scales:{x:vy(v=>'₹'+v),y:{grid:{display:false},ticks:{font:{size:11}}}},plugins:{vlab:{negRight:true,bold:true,fmt:v=>(v>0?'+':'−')+'₹'+Math.abs(v).toFixed(1)+'L cr'}}},plugins:[vlab]});
  // 8-9 ticket
  add('xTktY',{type:'bar',data:{labels:D.dirY.map(r=>yl2(r.y)),datasets:[bar('Average',D.dirY.map((r,i)=>i===D.dirY.length-1?s1:sky),D.dirY.map(r=>r.t),{maxBarThickness:54})]},options:{layout:{padding:{top:22}},scales:{x:noX,y:vy(v=>'₹'+v,{beginAtZero:true})},plugins:{vlab:{size:11.5,bold:true,fmt:v=>'₹'+v}}},plugins:[vlab]});
  add('xTktM',{type:'bar',data:{labels:TK.map(r=>r.m),datasets:[{data:TK.map(r=>r.y),backgroundColor:TK.map(r=>r.y<0?s2:s1),borderRadius:2,barPercentage:.8}]},options:{layout:{padding:{top:16,right:28}},scales:{x:monthX(7),y:vy(v=>v+'%')},plugins:{vlab:{size:10,fmt:(v,d,i)=>i===TK.length-1||i===TK.findIndex(r=>r.m==='2025-07')?pct(v):null}}},plugins:[vlab]});
  // 10 cash
  add('xCash',{type:'bar',data:{labels:D.cashQ.map(r=>r.q),datasets:[bar('Digital',s1,D.cashQ.map(r=>r.adig_mid_rs),{stack:'a',maxBarThickness:30}),bar('Cash',s2,D.cashQ.map(r=>r.acash_mid_rs),{stack:'a',maxBarThickness:30})]},
    options:{layout:{padding:{top:18}},scales:{x:{stacked:true,grid:{display:false},ticks:{maxRotation:0,autoSkip:true,maxTicksLimit:9}},y:vy(v=>'₹'+v,{stacked:true,beginAtZero:true})},plugins:{vlab:{size:10.5,bold:true,fmt:(v,d,i)=>d===1?Math.round((D.cashQ[i].adj_lo+D.cashQ[i].adj_hi)/2)+'%':null}}},plugins:[vlab]});
  // 11 channels
  const CF=D.cashflow;
  add('xPay',{type:'bar',data:{labels:CF.map(r=>r.fy),datasets:[bar('Merchant UPI',s1,CF.map(r=>r.p2m)),bar('ATM cash withdrawals',s2,CF.map(r=>r.atm)),bar('Card payments',bench,CF.map(r=>r.cards)),bar('Cash held by public',s3,CF.map(r=>r.cwp))]},options:{layout:{padding:{top:16}},scales:{x:{grid:{display:false}},y:vy(v=>'₹'+v,{beginAtZero:true})},plugins:{vlab:{size:10,fmt:v=>Math.round(v)}}},plugins:[vlab]});
  // 12 where new money went
  const F=D.fam;const fl={"NPCI 'Others' + categories entering or leaving NPCI's list":"NPCI 'Others' + list changes",'Shopping (retail, apparel, electronics)':'Shopping','Investments (brokers)':'Investments (brokers)','Bills (telecom, utilities)':'Bills','Loan & card repayments':'Loan repayments'};
  add('xFam',{type:'bar',data:{labels:F.map(r=>fl[r.f]||r.f),datasets:[{data:F.map(r=>r.inc),backgroundColor:F.map(r=>r.grp==='Consumption'?s1:r.grp==='Financial flows'?s2:bench),borderRadius:3,barPercentage:.72}]},options:{indexAxis:'y',layout:{padding:{right:130}},scales:{x:vy(v=>'₹'+v),y:{grid:{display:false},ticks:{autoSkip:false,font:{size:11.5}}}},plugins:{vlab:{negRight:true,size:11,fmt:(v,d,i)=>(v>0?'+':'−')+'₹'+Math.abs(v).toFixed(1)+'L cr'+(F[i].g!=null?' ('+pct0(F[i].g)+')':' ('+F[i].pct.toFixed(0)+'% of rise)')}}},plugins:[vlab]});
  // 13 size, 14 ticket by category
  add('xSize',{type:'bar',data:{labels:['FY23','FY24','FY25','FY26'],datasets:[bar('All UPI ÷ GDP',s1,[0.53,0.69,0.82,0.91]),bar('Merchant UPI ÷ consumption',s2,[0.21,0.31,0.40,0.46])]},options:{layout:{padding:{top:16}},scales:{x:{grid:{display:false}},y:vy(v=>v.toFixed(1)+'×',{beginAtZero:true})},plugins:{vlab:{size:10.5,fmt:v=>v.toFixed(2)+'×'}}},plugins:[vlab]});
  const tick=D.score.slice().sort((a,b)=>b.t1-a.t1);
  add('xTicket',{type:'bar',data:{labels:tick.map(r=>r.n.replace(' (loan repayments) †','')),datasets:[{data:tick.map(r=>r.t1),backgroundColor:tick.map(r=>r.t1>=2000?s2:s1),borderRadius:2,barPercentage:.78}]},options:{indexAxis:'y',layout:{padding:{right:44}},scales:{x:{type:'logarithmic',min:50,max:12000,ticks:{maxRotation:0,autoSkip:false,callback:v=>[100,1000,10000].includes(v)?rs(v):''}},y:{grid:{display:false},ticks:{autoSkip:false,font:{size:9.5}}}},plugins:{refline:{value:2000,label:'₹2,000 fee threshold',bottom:true},vlab:{size:9,fmt:v=>rs(v)}}},plugins:[refline,vlab]});
  // 16 mini category charts
  (window.CARDS||[]).forEach(cd=>{const s=D.cardser[cd.m];const first=s.findIndex(r=>r.v!=null);const rows=s.slice(first);
    add('m'+cd.m,{type:'bar',data:{labels:rows.map(r=>r.m),datasets:[bar('Value',s1,rows.map(r=>r.v),{maxBarThickness:6,borderRadius:1,barPercentage:.9,categoryPercentage:.95})]},options:{layout:{padding:{top:cd.ev&&cd.ev.length?22:12,right:4}},scales:{x:{grid:{display:false},ticks:{maxRotation:0,autoSkip:true,maxTicksLimit:4,font:{size:9},callback(v){return mlab(this.getLabelForValue(v))}}},y:{grid:{color:tok('--grid')},beginAtZero:true,ticks:{maxTicksLimit:4,font:{size:9},callback:v=>v>=1000?'₹'+(v/1000)+'k':'₹'+v}}},plugins:{markers:{items:cd.ev||[],above:true}}},plugins:[markers]});});
  // 17 food
  add('xFoodY',{type:'bar',data:{labels:D.foodY.map(r=>[r.y,'eating out '+Math.round(r.share)+'%']),datasets:[bar('Groceries',s1,D.foodY.map(r=>r.home)),bar('Restaurants + fast food',s2,D.foodY.map(r=>r.away))]},options:{layout:{padding:{top:16}},scales:{x:{grid:{display:false},ticks:{maxRotation:0,autoSkip:false,font:{size:10}}},y:vy(v=>'₹'+v,{beginAtZero:true})},plugins:{vlab:{size:10,fmt:v=>'₹'+v.toFixed(1)}}},plugins:[vlab]});
  add('xFood',{type:'line',data:{labels:D.food.map(r=>r.m),datasets:[ln(s1,D.food.map(r=>r.home),{label:'Food at home'}),ln(s2,D.food.map(r=>r.away),{label:'Eating out'}),ln(bench,D.food.map(r=>r.all),{label:'All merchant UPI',borderDash:[5,4]})]},options:{layout:{padding:{right:96}},scales:{x:monthX(7),y:vy(v=>v+'%')},plugins:{vlab:{lineEnd:true,colorize:true,size:10.5,fmt:(v,d)=>['At home','Eating out','All'][d]+' '+pct0(v)}}},plugins:[vlab]});
  // 18 tax
  add('xITax',{type:'bar',data:{labels:D.itax.map(r=>r.fy),datasets:[bar('Essentials',s1,D.itax.map(r=>r.ess)),bar('Discretionary',s2,D.itax.map(r=>r.dis))]},options:{layout:{padding:{top:30}},scales:{x:{grid:{display:false}},y:vy(v=>'₹'+v,{beginAtZero:true})},plugins:{vlab:{size:10,fmt:(v,d,i)=>{const r=D.itax[i];const g=d===0?r.g_ess:r.g_dis;return['₹'+v.toFixed(1),g!=null?pct0(g):'']}}}},plugins:[vlab]});
  add('xTerc',{type:'bar',data:{labels:D.terc.map(r=>[r.g.replace(' (top 7 states)','').replace(' (bottom 7)',''),r.filers+' per 1,000']),datasets:[bar('Before',bench,D.terc.map(r=>r.pre)),bar('After',s1,D.terc.map(r=>r.post))]},options:{layout:{padding:{top:16,bottom:2}},scales:{x:{grid:{display:false},ticks:{maxRotation:0,autoSkip:false,font:{size:9.5}}},y:vy(v=>v)},plugins:{vlab:{size:10,fmt:v=>(v>0?'+':'')+v.toFixed(1)}}},plugins:[vlab]});
  const VY=D.vehY;
  add('xVeh',{type:'bar',data:{labels:['Cars','Two-wheelers'],datasets:[bar('Oct 23–Sep 24',bench,[VY.cars.y24/1e6,VY.tw.y24/1e6].map(x=>+x.toFixed(2))),bar('Oct 24–Sep 25',sky,[VY.cars.y25/1e6,VY.tw.y25/1e6].map(x=>+x.toFixed(2))),bar('Oct 25–Sep 26',s1,[VY.cars.y26/1e6,VY.tw.y26/1e6].map(x=>+x.toFixed(2)))]},options:{layout:{padding:{top:30}},scales:{x:{grid:{display:false}},y:{type:'logarithmic',min:1,max:40,grid:{color:tok('--grid')},ticks:{callback:v=>[1,2,5,10,20].includes(v)?v+' mn':''}}},plugins:{vlab:{size:9.5,fmt:(v,d,i)=>{const k=i===0?VY.cars:VY.tw;return[v.toFixed(2),d===1?pct(k.g25):d===2?pct(k.g26):'']}}}},plugins:[vlab]});
  // 19 credit split
  const CS=D.credit_split.rows.map((r,i)=>[r.line,r.lakh_cr,i<4?s1:bench,r.share]);
  add('xCredSplit',{type:'bar',data:{labels:CS.map(r=>r[0]),datasets:[{data:CS.map(r=>r[1]),backgroundColor:CS.map(r=>r[2]),borderRadius:3,barPercentage:.7}]},options:{indexAxis:'y',layout:{padding:{right:96}},scales:{x:vy(v=>'₹'+v,{beginAtZero:true}),y:{grid:{display:false},ticks:{font:{size:11}}}},plugins:{vlab:{bold:true,size:11,fmt:(v,d,i)=>'₹'+v.toFixed(2)+'L cr · '+CS[i][3].toFixed(1)+'%'}}},plugins:[vlab]});
  const CR=D.credit;const crn=l=>l.replace('Bank+NBFC non-housing personal (indicative: Aug NBFC + Sep bank)','Banks + NBFCs: all non-housing*').replace('Bank+NBFC ex gold (indicative: Aug NBFC + Sep bank)','Banks + NBFCs: excl. gold*').replace('Bank ','Banks: ').replace('NBFC ','NBFCs: ').replace('non-housing personal','all non-housing').replace('non-housing ex gold','non-housing excl. gold').replace('retail ex housing','all non-housing');
  add('xCredit',{type:'bar',data:{labels:CR.map(r=>crn(r.line)),datasets:[bar('Year to Sep 2025',bench,CR.map(r=>r.yoy_to_2025),{barPercentage:.86}),bar('Year to Sep 2026',s1,CR.map(r=>r.yoy_to_2026),{barPercentage:.86})]},options:{indexAxis:'y',layout:{padding:{right:40}},scales:{x:vy(v=>v+'%'),y:{grid:{display:false},ticks:{autoSkip:false,font:{size:10}}}},plugins:{vlab:{size:9,fmt:v=>pct(v)}}},plugins:[vlab]});
  // 21 cities
  const C=D.cities.slice().sort((a,b)=>b.v_pr_month-a.v_pr_month);
  add('xCity',{type:'bar',data:{labels:C.map(r=>[r.city,r.state+' '+rs(r.state_v_pr_month)]),datasets:[{data:C.map(r=>r.v_pr_month),backgroundColor:C.map(r=>r.city==='Kolkata'?s2:s1),borderRadius:3,barPercentage:.7}]},options:{indexAxis:'y',layout:{padding:{right:120}},scales:{x:vy(v=>'₹'+(v/1000)+'k',{beginAtZero:true}),y:{grid:{display:false},ticks:{autoSkip:false,font:{size:10}}}},plugins:{refline:{value:D.india_geo.v_pr_month,label:'India'},vlab:{size:10.5,fmt:(v,d,i)=>rs(v)+' · '+(C[i].v_pr_month/C[i].state_v_pr_month).toFixed(1)+'× state'}}},plugins:[refline,vlab]});
}
