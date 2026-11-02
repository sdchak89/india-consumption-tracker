const $=s=>document.querySelector(s);
function tok(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim()}
const charts=[];const TABLES={};
const fmt1=x=>x==null?'':(+x).toLocaleString('en-IN',{maximumFractionDigits:1});
const fmt2=x=>x==null?'':(+x).toLocaleString('en-IN',{maximumFractionDigits:2});
const rs=x=>x==null?'':'₹'+Math.round(x).toLocaleString('en-IN');
const pct=(x,d=1)=>x==null?'n/a':(x>0?'+':'')+(+x).toFixed(d)+'%';
const pct0=x=>x==null?'n/a':(x>0?'+':'')+Math.round(x)+'%';
const mlab=m=>{const[y,mo]=m.split('-');return['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+mo-1]+' '+y.slice(2)};
let N=false;
const yl=s=>{const q=String(s).split('–');return q.length===2?[q[0]+'–',q[1]]:s};
const wrapL=(s,m)=>{if(!N||s.length<=m)return s;const out=[];let cur='';s.split(' ').forEach(x=>{if(cur&&(cur+' '+x).length>m){out.push(cur);cur=x}else cur=cur?cur+' '+x:x});if(cur)out.push(cur);return out};
// ---------- plugins ----------
const vlab={id:'vlab',afterDatasetsDraw(ch,a,o){if(!o||!o.fmt)return;const{ctx}=ch;const horiz=ch.options.indexAxis==='y';ctx.save();ctx.font=(o.bold?'600 ':'500 ')+(o.size||11)+'px '+tok('--body');const ends=[];
  ch.data.datasets.forEach((ds,di)=>{const meta=ch.getDatasetMeta(di);if(meta.hidden)return;const n=meta.data.length;
    meta.data.forEach((el,i)=>{const val=ds.data[i];if(val==null)return;let t=o.fmt(val,di,i,ch);if(t==null||t==='')return;const lines=[].concat(t);
      if(ch.config.type==='line'){if(o.lineEnd){let last=-1;ds.data.forEach((v,k)=>{if(v!=null)last=k});if(i!==last)return;ends.push({x:el.x,y:el.y+((o.offsets&&o.offsets[di])||0),lines,c:o.colorize?ds.borderColor:tok('--ink-2')});}return;}
      if(!horiz&&n>1){const sp=Math.abs(meta.data[1].x-meta.data[0].x);const tw=Math.max(...lines.map(l=>ctx.measureText(l).width));const k=Math.ceil((tw+6)/sp);if(k>1&&(n-1-i)%k!==0)return;}
      if(o.inside){ctx.fillStyle='#fff';ctx.textAlign='center';ctx.textBaseline='middle';const cx=horiz?(el.x+el.base)/2:el.x,cy=horiz?el.y:(el.y+el.base)/2;const h=horiz?Math.abs(el.x-el.base):Math.abs(el.base-el.y);if(h<(o.minSize||16))return;lines.forEach((ln,k)=>ctx.fillText(ln,cx,cy+(k-(lines.length-1)/2)*12));return;}
      ctx.fillStyle=tok('--ink');
      if(horiz){const neg=val<0&&!o.negRight;ctx.textAlign=neg?'right':'left';ctx.textBaseline='middle';const x=neg?Math.min(el.x,el.base)-4:Math.max(el.x,el.base)+4;lines.forEach((ln,k)=>ctx.fillText(ln,x,el.y+(k-(lines.length-1)/2)*12));}
      else{ctx.textAlign='center';ctx.textBaseline='bottom';const neg=val<0;const y=neg?el.y+14*lines.length:Math.min(el.y,el.base)-3;lines.slice().reverse().forEach((ln,k)=>ctx.fillText(ln,el.x,y-k*12));}
    });});
  if(ends.length){ends.sort((p,q)=>p.y-q.y);for(let k=1;k<ends.length;k++){const pv=ends[k-1],g=12*pv.lines.length+1;if(ends[k].y<pv.y+g)ends[k].y=pv.y+g;}const lb=ends[ends.length-1],ov=lb.y+12*(lb.lines.length-1)-(ch.chartArea.bottom-4);if(ov>0)ends.forEach(e=>e.y-=ov);ctx.textAlign='left';ctx.textBaseline='middle';ends.forEach(e=>{ctx.fillStyle=e.c;e.lines.forEach((ln,k)=>ctx.fillText(ln,e.x+6,e.y+k*12))});}
  ctx.restore();}};
const refline={id:'refline',afterDatasetsDraw(ch,a,o){if(!o||o.value==null)return;const{ctx,chartArea:ca}=ch;const ax=o.axis||'x';const sc=ch.scales[ax];const p=sc.getPixelForValue(o.value);ctx.save();ctx.strokeStyle=tok('--ink-3');ctx.setLineDash([4,3]);ctx.beginPath();if(ax==='x'){ctx.moveTo(p,ca.top);ctx.lineTo(p,ca.bottom)}else{ctx.moveTo(ca.left,p);ctx.lineTo(ca.right,p)}ctx.stroke();ctx.setLineDash([]);if(o.label){ctx.fillStyle=tok('--ink-2');ctx.font='11px '+tok('--body');ctx.textAlign='left';ctx.fillText(o.label,ax==='x'?p+4:ca.left+4,ax==='x'?(o.bottom?ca.bottom-6:ca.top+10):p-4)}ctx.restore();}};
const markers={id:'markers',afterDatasetsDraw(ch,a,o){const items=o&&o.items;if(!items||!items.length)return;const{ctx,chartArea:ca,scales:{x}}=ch;const labels=ch.data.labels;ctx.save();ctx.font=(N?10:11)+'px '+tok('--body');items.forEach((it,i)=>{const idx=labels.indexOf(it[0]);if(idx<0)return;const px=x.getPixelForValue(idx);ctx.strokeStyle=tok('--ink-3');ctx.setLineDash([3,3]);ctx.beginPath();ctx.moveTo(px,o.above?ca.top-4:ca.top+14);ctx.lineTo(px,ca.bottom);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle=tok('--ink-2');const txt=(N&&it[2])||it[1];const w=ctx.measureText(txt).width;let tx=px+4;if(tx+w>((o.spill||o.above)?ch.width-4:ca.right)||it[3]==='L')tx=px-4-w;if(tx<ca.left)tx=ca.left;ctx.fillText(txt,tx,o.above?ca.top-28+(i%2)*11:ca.top+10+(i%2)*12);});ctx.restore();}};
function base(){Chart.defaults.font.family=tok('--body');Chart.defaults.font.size=N?11:12;Chart.defaults.color=tok('--ink-2');Chart.defaults.plugins.legend.display=false;Chart.defaults.maintainAspectRatio=false;Chart.defaults.animation=false;
  const tt=Chart.defaults.plugins.tooltip;tt.backgroundColor=tok('--surface');tt.titleColor=tok('--ink');tt.bodyColor=tok('--ink-2');tt.borderColor=tok('--line');tt.borderWidth=1;tt.padding=10;
  Chart.defaults.scale.grid.color=tok('--grid');Chart.defaults.scale.border.display=false;}
const ln=(color,data,extra)=>Object.assign({data,borderColor:color,backgroundColor:color,borderWidth:2,pointRadius:0,pointHoverRadius:4,tension:.25,spanGaps:false},extra||{});
const bar=(label,color,data,extra)=>Object.assign({label,data,backgroundColor:color,borderRadius:3,maxBarThickness:46},extra||{});
const monthX=(max)=>({grid:{display:false},ticks:{maxRotation:0,autoSkip:true,maxTicksLimit:max||8,callback(v){return mlab(this.getLabelForValue(v))}}});
