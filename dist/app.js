'use strict';
let snapshot=null, analysis=null, filter='all';
const $=id=>document.getElementById(id);
const labels={ready:'可用',stale:'資料過期',missing:'待串接',error:'擷取失敗',license_required:'待授權'};
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeURL=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?u.href:'#';}catch{return '#';}};
const fmt=(v,unit)=>v==null?'—':new Intl.NumberFormat('zh-TW',{maximumFractionDigits:unit==='口'||unit==='點'?0:unit==='億股'?3:unit==='TWD'||unit==='HKD'?4:unit==='USD'?4:2}).format(v);
function toast(text){$('toast').textContent=text;$('toast').style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').style.display='none',5500);}
function currentStatus(m){if(m.value===null)return m.status;const age=(Date.now()-Date.parse(m.observed_at+'T23:59:59+08:00'))/86400000;return age>(m.max_age_days??4)?'stale':m.status;}
function card(m){const status=currentStatus(m),delta=m.delta,sign=delta>0?'＋':delta<0?'−':'',change=delta==null?'尚無可比較的前值':`${sign}${fmt(Math.abs(delta),'')} ${m.change_kind==='bp'?'bp':m.change_kind==='absolute'?(m.unit==='%'?'百分點':m.unit):'%'}${m.id==='night'?' · 期交所公布漲跌':' · 較前筆'}`;return `<button class="metric" data-metric="${esc(m.id)}" aria-label="${esc(m.label)}，查看來源與細節"><div class="metric-top"><div><div class="metric-label">${esc(m.label)}</div><div class="metric-code">${esc(m.id.toUpperCase().replaceAll('_',' / '))}</div></div><span class="badge ${esc(status)}">${esc(labels[status]||status)}</span></div><div class="metric-value">${fmt(m.value,m.unit)}<em>${esc(m.unit)}</em></div><div class="metric-change ${delta>0?'up':delta<0?'down':'neutral'}">${esc(change)}</div><div class="mini-note">${m.quality==='proxy'?'參考／替代口徑':m.id==='night'?esc(m.details?.contract||''):m.value===null?'等待資料通道':'已保留來源證據'}</div><div class="metric-date">${esc(m.observed_at||'日期待更新')} ${m.observed_at&&m.observed_at<new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Taipei'})?'· 較早交易日':''} ↗</div></button>`;}
function sparkline(m){const points=(m.history||[]).filter(p=>Number.isFinite(p.value)).slice(-20);if(points.length<2)return '';const values=points.map(p=>p.value),lo=Math.min(...values),range=Math.max(...values)-lo;const line=values.map((v,i)=>`${(i/(values.length-1)*96+2).toFixed(1)},${(range?36-(v-lo)/range*32:20).toFixed(1)}`).join(' ');return `<svg class="sparkline" viewBox="0 0 100 40" aria-hidden="true"><polyline points="${line}" fill="none" stroke="${values.at(-1)>=values[0]?'#f29791':'#6dceb6'}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;}
const plainCard=card;
card=function(m){return plainCard(m).replace('class="metric"',`class="metric ${m.value==null?'metric-muted':''}"`).replace('</button>',sparkline(m)+'</button>');};
function render(){if(!snapshot)return;for(const group of ['global','taiwan']){const rows=snapshot.metrics.filter(m=>m.group===group&&(filter==='all'||(filter==='usable'?currentStatus(m)==='ready':currentStatus(m)!=='ready')));const ids=group==='global'?['us30','us10','us5','gold','brent','copper','dxy','vix']:['foreign_net','night','spot','usdtwd','pcr','lending_balance'];const core=ids.map(id=>rows.find(m=>m.id===id)).filter(Boolean),extra=rows.filter(m=>!ids.includes(m.id));let html=core.length?`<div class="core-grid ${group==='taiwan'?'taiwan-core':''}">${core.map(card).join('')}</div>`:'';if(extra.length)html+=group==='global'?`<div class="supplement-grid">${extra.map(card).join('')}</div>`:`<details class="metric-detail-group" ${filter==='attention'?'open':''}><summary>完整籌碼與流動性 · ${extra.length} 項</summary><div class="core-grid">${extra.map(card).join('')}</div></details>`;$(group+'-metrics').innerHTML=html||'<div class="empty">此篩選條件下沒有指標。</div>';}
 const ready=snapshot.metrics.filter(m=>currentStatus(m)==='ready').length, stale=snapshot.metrics.filter(m=>currentStatus(m)==='stale').length;
 $('available-count').textContent=ready;$('stale-count').textContent=stale;$('missing-count').textContent=snapshot.metrics.length-ready-stale;
 $('report-date').textContent=new Date(snapshot.generated_at).toLocaleDateString('zh-TW',{timeZone:'Asia/Taipei',year:'numeric',month:'2-digit',day:'2-digit'});
 $('updated').textContent='擷取 '+new Date(snapshot.generated_at).toLocaleTimeString('zh-TW',{timeZone:'Asia/Taipei',hour:'2-digit',minute:'2-digit',hour12:false})+' · 台灣時間';
 $('source-table').innerHTML=snapshot.sources.map(s=>`<tr><td><a href="${esc(safeURL(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.name)} ↗</a></td><td>${esc(s.coverage)}</td><td>${esc(s.channel)}</td><td><span class="badge ${esc(s.status)}">${esc(labels[s.status]||s.status)}</span></td></tr>`).join('');
 document.querySelectorAll('[data-metric]').forEach(el=>el.addEventListener('click',()=>detail(snapshot.metrics.find(m=>m.id===el.dataset.metric))));
}
function detail(m){const history=(m.history||[]).slice(-7);$('metric-detail').innerHTML=`<div class="eyebrow">SOURCE & OBSERVATIONS</div><h2>${esc(m.label)}</h2><div class="metric-value">${fmt(m.value,m.unit)}<em>${esc(m.unit)}</em></div><p>${esc(m.note)}</p><dl><dt>資料日期</dt><dd>${esc(m.observed_at||'尚未更新')}</dd><dt>市場時段</dt><dd>${esc(m.session||'待確認')}</dd><dt>擷取時間</dt><dd>${esc(m.fetched_at)}</dd><dt>品質狀態</dt><dd>${esc(labels[currentStatus(m)])} ${m.quality==='proxy'?'· 參考／替代口徑':''}</dd><dt>資料來源</dt><dd><a href="${esc(safeURL(m.source_url))}" target="_blank" rel="noopener noreferrer">開啟原始通道 ↗</a></dd></dl>${history.length?'<h3>最近觀测值</h3><table><thead><tr><th>交易日</th><th>數值</th></tr></thead><tbody>'+history.map(p=>`<tr><td>${esc(p.date)}</td><td>${fmt(p.value,m.unit)}</td></tr>`).join('')+'</tbody></table>':''}${Object.keys(m.details||{}).length?'<h3>口徑與附加資料</h3><pre>'+esc(JSON.stringify(m.details,null,2))+'</pre>':''}`;$('metric-dialog').showModal();}
function download(content,name,type){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function markdown(){return '# Pioter 每日研究包\n\n擷取：'+snapshot.generated_at+'\n\n'+snapshot.metrics.map(m=>`## ${m.label}\n- 數值：${m.value??'尚未更新'} ${m.unit}\n- 日期：${m.observed_at??'—'}\n- 時段：${m.session??'—'}\n- 狀態：${currentStatus(m)} / ${m.quality}\n- 來源：${m.source_url}\n- 備註：${m.note}\n`).join('\n')+'\n## 資料限制\n'+snapshot.limitations.map(x=>'- '+x).join('\n')+'\n\n## 模型分析\n'+(analysis?JSON.stringify(analysis,null,2):'尚未分析。禁止把缺值當中性、把未知風險當低風險。');}
function showAnalysis(a){if(!a||typeof a!=='object'||!a.summary||!a.short_term||!a.medium_term)throw Error('分析格式不符：需要 summary、short_term、medium_term');if(a.snapshot_id!==snapshot.snapshot_id)throw Error('分析結果與目前資料快照不一致，請使用同一份研究包重新分析。');analysis=a;const names={Bullish:'偏多',Neutral:'中性',Bearish:'偏空',Unknown:'資料不足',Low:'低',Medium:'中',High:'高'};for(const [id,key] of [['global-signal','international_capital'],['taiwan-signal','taiwan_capital'],['risk-signal','systemic_risk']])$(id).textContent=names[a.summary[key]]||'未評估';$('brief-title').textContent=a.summary.one_line||'模型研究觀點';$('brief-text').textContent='模型：'+(a.model||'匯入分析')+' · '+(a.generated_at||'')+' · 請參照下方資料限制';$('short-title').textContent=a.short_term.direction||'條件式情境';$('short-text').textContent=a.short_term.base_scenario||'資料不足';$('medium-title').textContent=a.medium_term.direction||'條件式情境';$('medium-text').textContent=a.medium_term.base_scenario||'資料不足';$('model-state').textContent='已完成 · 模型觀點';$('analysis-result').hidden=false;$('analysis-result').textContent=JSON.stringify(a,null,2);}
async function load(){try{const r=await fetch('data/latest.json',{cache:'no-store'});if(!r.ok)throw Error('無法讀取資料');const d=await r.json();if(!Array.isArray(d.metrics)||!Array.isArray(d.sources))throw Error('資料格式不正確');snapshot=d;analysis=null;render();try{const a=await fetch('data/analysis.json',{cache:'no-store'});if(a.ok)showAnalysis(await a.json());}catch{ $('model-state').textContent='需重新分析';} }catch(e){$('updated').textContent='載入失敗，可重試';toast(e.message);}}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.view;document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('selected',x===b));render();}));
document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>{document.querySelectorAll('nav a').forEach(x=>x.classList.toggle('active',x===a));}));
$('zoom').addEventListener('change',e=>{document.documentElement.style.setProperty('--font-scale',e.target.value);});
$('refresh').addEventListener('click',async()=>{await load();toast('已重新讀取快照；每日擷取由本機排程執行。');});
$('export-json').addEventListener('click',()=>{if(!snapshot)return toast('資料尚未載入');download(JSON.stringify(snapshot,null,2),'pioter-'+snapshot.snapshot_id+'.json','application/json');});
$('export-md').addEventListener('click',()=>{if(!snapshot)return toast('資料尚未載入');download(markdown(),'pioter-'+snapshot.snapshot_id+'.md','text/markdown;charset=utf-8');});
$('close-dialog').addEventListener('click',()=>$('metric-dialog').close());
$('analysis-file').addEventListener('change',async e=>{try{const f=e.target.files[0];if(!f)return;if(f.size>2e6)throw Error('分析檔案請小於 2 MB');showAnalysis(JSON.parse(await f.text()));toast('已載入與快照一致的模型分析');}catch(err){toast(err.message);}finally{e.target.value='';}});
$('analyze').addEventListener('click',async()=>{if(!['localhost','127.0.0.1'].includes(location.hostname)){toast('請在本機版執行分析，或匯入本地模型產生的 analysis.json。');return;}const b=$('analyze');b.disabled=true;$('model-state').textContent='正在分析';try{const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({snapshot_id:snapshot.snapshot_id}),signal:AbortSignal.timeout(240000)});const a=await r.json();if(!r.ok)throw Error(a.error||'分析失敗');showAnalysis(a);toast('本地模型分析完成');}catch(e){$('model-state').textContent='分析未完成';toast(e.message);}finally{b.disabled=false;}});
$('analysis-result').outerHTML='<div id="evidence-list"></div><details id="analysis-json" hidden><summary>檢視完整模型 JSON</summary><pre id="analysis-result"></pre></details>';
const originalShowAnalysis=showAnalysis;
showAnalysis=function(a){
 originalShowAnalysis(a);
 $('analysis-json').hidden=false;
 if(a.review_status==='needs_review'){
  // Retain the model direction with a prominent draft marker; never imply approval.
  $('brief-title').textContent='模型已完成分析，有待覆核的敘述';
  $('brief-text').textContent=(a.review_flags||[]).join(' ');
  $('model-state').textContent='已完成 · 待覆核';
 }
 const directionNames={Bullish:'▲ 看多',Bearish:'▼ 看空',Neutral:'— 中性',Unknown:'資料不足',Low:'低風險',Medium:'中風險',High:'高風險'};
 for(const [id,key] of [['global-signal','international_capital'],['taiwan-signal','taiwan_capital'],['risk-signal','systemic_risk']]){
  const value=a.summary[key],el=$(id),draft=a.review_status==='needs_review';
  el.textContent=directionNames[value]||'未評估';
  const panel=el.closest('.summary');panel.querySelector('.direction-animal')?.remove();
  if((id==='global-signal'||id==='taiwan-signal')&&['Bullish','Bearish'].includes(value)){
   const animal=document.createElement('img');animal.className='direction-animal';animal.src=value==='Bullish'?'assets/bull.png':'assets/bear.png';animal.alt=value==='Bullish'?'牛：看多':'熊：看空';animal.width=96;animal.height=96;panel.append(animal);
  }

  el.closest('.summary').dataset.direction=draft?'review':value;
  if(draft){const flag=document.createElement('small');flag.className='review-marker';flag.textContent='模型初判 · 待覆核';el.append(flag);}
 }
 const translate={Bullish:'偏多情境',Bearish:'偏空情境',Neutral:'中性情境',Unknown:'資料不足'};
 for(const [key,prefix] of [['short_term','short'],['medium_term','medium']]){
  $(prefix+'-title').textContent=translate[a[key].direction]||a[key].direction;
  $(prefix+'-text').innerHTML=esc(a[key].base_scenario)+'<span class="scenario-label">翻多條件</span>'+esc(a[key].bullish_trigger)+'<span class="scenario-label danger">風險升級條件</span>'+esc(a[key].bearish_trigger)+'<span class="scenario-label">風險情境</span>'+esc(a[key].risk_scenario);
 }
 $('evidence-list').innerHTML='<h4>判讀依據</h4>'+(a.evidence||[]).map(e=>{const m=snapshot.metrics.find(m=>m.id===e.metric_id);return '<div class="evidence-item"><strong>'+esc(m?.label||e.metric_id)+' <span>'+fmt(e.value,m?.unit)+' '+esc(m?.unit||'')+'</span></strong><small>'+esc(e.observed_at)+'</small><p>'+esc(e.interpretation)+'</p></div>';}).join('')+'<h4>分歧與資料限制</h4><ul>'+[...(a.divergences||[]),...(a.missing_data||[])].map(x=>'<li>'+esc(x)+'</li>').join('')+'<p class="help">模型觀點；已核對引用數值與日期，推論與門檻仍需研究者覆核。</p>';
};
const originalLoad=load;
load=async function(){
 for(const id of ['global-signal','taiwan-signal'])$(id).textContent='待分析';
 $('risk-signal').textContent='未評估';$('brief-title').textContent='先確認資料，再形成觀點';$('brief-text').textContent='等待與本次快照一致的模型分析。';
 $('evidence-list').innerHTML='';$('analysis-json').hidden=true;$('analysis-result').textContent='';$('model-state').textContent='尚未執行';
 for(const prefix of ['short','medium']){$(prefix+'-title').textContent='等待分析';$(prefix+'-text').textContent='缺少有效分析時不保留上一版結論。';}
 document.querySelectorAll('.summary').forEach(el=>{delete el.dataset.direction;el.querySelector('.direction-animal')?.remove();});
 await originalLoad();
};
load();
