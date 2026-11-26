"""Standalone live leader-analysis page, using the existing read-only prep APIs."""
LEADERS_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>dragon-quant · 龙头分析</title>
<style>
:root{--bg:#f3f5f9;--card:#fff;--ink:#18263a;--muted:#718096;--line:#e4eaf1;--blue:#4e7de6;--green:#16815f;--amber:#a96c16;--red:#c44f58;--nav:#101a2b;--shadow:0 7px 22px rgba(23,43,72,.05)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 Inter,"Microsoft YaHei",system-ui,sans-serif}
header{height:62px;background:white;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 max(20px,calc((100vw - 1420px)/2))}
.brand{font-size:15px;font-weight:800}.brand span{color:#557fdd}.right{display:flex;align-items:center;gap:12px}.link{font-size:11px;color:#5676b6;text-decoration:none}.cloud{font-size:10px;border-radius:99px;padding:5px 9px;background:#edf4ff;color:#456ab8;font-weight:750}
main{max-width:1420px;margin:auto;padding:25px 24px 50px}.title{display:flex;align-items:end;justify-content:space-between;gap:14px;margin-bottom:20px}h1{font-size:24px;margin:0 0 3px}.muted{color:var(--muted);font-size:11px}
.actions{display:flex;gap:8px;flex-wrap:wrap}.btn{border:1px solid #dce4ee;background:white;border-radius:8px;color:#344761;padding:8px 12px;font-size:11px;font-weight:700;cursor:pointer}.btn.primary{background:#376bd8;border-color:#376bd8;color:white}.btn:disabled{opacity:.5;cursor:not-allowed}
.row{display:grid;gap:12px}.metrics{grid-template-columns:repeat(5,minmax(0,1fr));margin-bottom:14px}.leader-cards{grid-template-columns:repeat(3,minmax(0,1fr))}.twocol{grid-template-columns:1.1fr .9fr}
.card{background:var(--card);border:1px solid var(--line);border-radius:11px;box-shadow:var(--shadow);padding:15px}
.kicker{font-size:10px;color:var(--muted);font-weight:700}.big{font-size:25px;font-weight:820;margin:6px 0 2px;letter-spacing:-.6px}.sub{font-size:10px;color:var(--muted)}
.pill{display:inline-block;padding:4px 7px;border-radius:99px;font-size:9px;font-weight:800}.ok{background:#e9f7f0;color:var(--green)}.warn{background:#fff4e0;color:var(--amber)}.neutral{background:#edf1f6;color:#617189}
.section{margin-top:19px}.heading{display:flex;align-items:center;justify-content:space-between;margin:0 0 10px}.heading h2{font-size:14px;margin:0}.date-select{border:1px solid var(--line);border-radius:7px;padding:7px 9px;background:white;color:#485a74;font-size:11px}
.ladder{display:grid;gap:10px;margin-top:13px}.lrow{display:grid;grid-template-columns:55px 1fr 35px;gap:10px;align-items:center;font-size:11px}.track{height:8px;background:#edf1f6;border-radius:99px;overflow:hidden}.bar{height:100%;background:linear-gradient(90deg,#92b1fb,#4b78db);border-radius:99px}.codes{grid-column:2/4;font-size:9px;color:#8592a3;margin-top:-8px}
.list{display:grid}.item{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:11px 0;border-bottom:1px solid #eef1f5}.item:last-child{border:0}.item b{font-size:11px}.item small{display:block;color:var(--muted);font-size:9px}.item-right{text-align:right;color:#596b84;font-size:10px}
.tablewrap{overflow:auto}table{width:100%;min-width:650px;border-collapse:collapse}th{text-align:left;background:#f9fafc;color:#8290a1;font-size:9px;padding:10px 12px;border-bottom:1px solid var(--line)}td{padding:11px 12px;border-bottom:1px solid #edf0f5;font-size:10px;color:#586981}tr:last-child td{border:0}.code{font-weight:800;color:#243650}.empty{padding:24px;text-align:center;color:var(--muted);font-size:12px}
.notice{padding:11px 13px;border-radius:8px;background:#fff7e8;border:1px solid #f1dfb8;color:#805619;font-size:11px;margin:12px 0}
.state{font-size:10px;color:var(--muted);padding:8px 0;min-height:27px}.footer{text-align:center;font-size:9px;color:#8995a4;margin-top:22px}
@media(max-width:900px){.metrics{grid-template-columns:repeat(3,1fr)}.leader-cards{grid-template-columns:1fr}.twocol{grid-template-columns:1fr}}
@media(max-width:640px){main{padding:18px 13px 35px}.title{align-items:start;flex-direction:column}h1{font-size:21px}.metrics{grid-template-columns:repeat(2,1fr)}header{padding:0 14px}.brand{font-size:13px}}
</style>
</head>
<body>
<header><div class="brand"><span>🐉</span> dragon-quant <span style="font-weight:500;color:#8793a4">/ 龙头分析</span></div><div class="right"><span class="cloud">云端真实数据 · 只读面板</span><a class="link" href="/">完整看板 →</a></div></header>
<main>
<div class="title">
 <div><h1>全市场龙头分析</h1><div class="muted">空间板 · 连板梯队 · 主线龙头 · 情绪周期</div></div>
 <div class="actions"><select id="date" class="date-select"><option>正在读取日期…</option></select><button id="refresh" class="btn">刷新</button></div>
</div>
<div id="notice"></div>
<div class="section"><div class="heading"><h2>市场情绪</h2><span class="muted" id="dateLabel">—</span></div><div class="row metrics" id="metrics"></div></div>
<div class="section"><div class="heading"><h2>空间板与总龙头</h2><span class="muted">leader_analysis_v1</span></div><div class="row leader-cards" id="leaderCards"></div></div>
<div class="section"><div class="row twocol">
 <div class="card"><div class="heading"><h2>全市场连板梯队</h2><span class="muted">按高度降序</span></div><div class="ladder" id="ladder"></div></div>
 <div class="card"><div class="heading"><h2>主线龙头</h2><span class="muted">既有五角色责任链</span></div><div class="list" id="mainlineLeaders"></div></div>
</div></div>
<div class="section"><div class="heading"><h2>复盘候选池</h2><span class="muted" id="coverage">—</span></div><div class="card tablewrap"><table><thead><tr><th>代码 / 名称</th><th>主线</th><th>角色</th><th>连板</th><th>复盘评分</th><th>资格状态</th><th>数据覆盖</th></tr></thead><tbody id="candidates"></tbody></table><div id="emptyCandidates" class="empty" hidden>当前没有复盘候选记录。</div></div></div>
<div class="section"><div class="heading"><h2>数据任务</h2><span class="muted">按系统交易时段与前置条件执行</span></div><div class="card">
 <div class="actions"><button class="btn primary" id="scan">执行龙头扫描</button><button class="btn primary" id="prep">执行盘后复盘</button></div>
 <div id="eligibility" class="state">正在检查今日任务窗口…</div>
 <div id="jobStatus" class="state"></div>
</div></div>
<div class="footer">数据来自云端 TDX / THS 采集与 SQLite 快照 · 首次部署数据库为空，扫描和复盘后才会出现记录</div>
</main>
<script>
const $=id=>document.getElementById(id);
const escapeHtml=value=>String(value??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt=value=>value==null?"—":Number(value).toLocaleString("zh-CN",{maximumFractionDigits:1});
const pct=value=>value==null?"—":(Number(value)*100).toFixed(1)+"%";
let calendar=null, selectedDate=null, activeJob=null, pollHandle=null;

async function api(path,options={}){
 const response=await fetch(path,{credentials:"same-origin",headers:{"Accept":"application/json","Content-Type":"application/json",...(options.headers||{})},...options});
 if(response.status===401) throw new Error("登录已失效，请刷新页面并重新认证");
 let body={}; try{body=await response.json()}catch{}
 if(!response.ok) throw new Error(body.detail||body.error||("请求失败："+response.status));
 return body;
}
function metricCard(label,value,sub){
 return '<div class="card" style="padding:13px 14px"><div class="kicker">'+escapeHtml(label)+'</div><div class="big">'+escapeHtml(value)+'</div><div class="sub">'+escapeHtml(sub)+'</div></div>';
}
function showNotice(message,isError=false){
 $("notice").innerHTML=message?'<div class="notice" style="'+(isError?'background:#fff0f0;border-color:#efcaca;color:#983d45':'')+'">'+escapeHtml(message)+'</div>':"";
}
async function loadCalendar(){
 calendar=await api("/api/prep/calendar?days=365");
 const days=(calendar.days||[]).filter(x=>x.has_snapshot);
 const select=$("date");
 select.innerHTML="";
 for(const item of days){
  const option=document.createElement("option"); option.value=item.trade_date; option.textContent=item.trade_date; select.appendChild(option);
 }
 if(!days.length){
  select.innerHTML='<option value="">暂无复盘日期</option>'; selectedDate=null; return;
 }
 if(!selectedDate||!days.some(x=>x.trade_date===selectedDate)) selectedDate=days[days.length-1].trade_date;
 select.value=selectedDate;
}
function statusPill(status){
 const labels={identified:"已识别",contested:"高标并列",provisional:"暂定候选",unconfirmed:"待交叉验证",unavailable:"不可判"};
 const cls=status==="identified"?"ok":(status==="contested"||status==="provisional"?"warn":"neutral");
 return '<span class="pill '+cls+'">'+escapeHtml(labels[status]||"待确认")+'</span>';
}
function render(snapshot){
 const review=snapshot.review||{}, market=review.market||{}, inputs=market.inputs||{}, leaders=review.leaders||{}, cycle=review.emotion_cycle||{};
 $("dateLabel").textContent=snapshot.trade_date+" · 快照 v"+(snapshot.version||"—");
 $("metrics").innerHTML=[
  metricCard("情绪温度",fmt(market.score),market.state||"未知"),
  metricCard("涨停家数",fmt(inputs.limit_up_cnt),"THS 全市场涨停池"),
  metricCard("跌停家数",fmt(inputs.limit_down_cnt),"全 A 市场宽度"),
  metricCard("炸板率",pct(inputs.broken_rate),"触板后未封住比例"),
  metricCard("市场最高板",inputs.max_board_height==null?"—":inputs.max_board_height+" 板","全市场空间板")
 ].join("");
 const coverage=leaders.coverage||{}, space=leaders.space_board||{}, total=leaders.market_total_leader||{}, candidate=total.candidate||{};
 $("leaderCards").innerHTML=[
  '<div class="card" style="padding:16px"><div class="kicker">情绪周期</div><div class="big">'+escapeHtml(cycle.phase_label||"待观察")+'</div><div class="sub">'+escapeHtml(cycle.reason||"缺少环比证据")+'</div><div class="sub" style="margin-top:8px">解释性标签，不直接驱动买卖或仓位</div></div>',
  '<div class="card" style="padding:16px"><div class="kicker">全市场空间板</div><div class="big">'+(space.height==null?"—":escapeHtml(space.height+" 板"))+'</div><div class="sub">'+escapeHtml(space.count||0)+' 只并列最高板 · '+escapeHtml((space.stocks||[]).map(x=>x.code).join("、")||"无代码")+'</div></div>',
  '<div class="card" style="padding:16px"><div class="kicker">市场总龙头</div><div class="big" style="font-size:20px">'+escapeHtml(total.code||candidate.code||"暂不指定")+'</div><div style="margin:6px 0">'+statusPill(total.status)+'</div><div class="sub">'+escapeHtml(candidate.name||total.reason||"等待交叉验证")+'</div></div>'
 ].join("");
 const ladder=leaders.ladder||[], max= Math.max(1,...ladder.map(x=>Number(x.count)||0));
 $("ladder").innerHTML=ladder.length?ladder.map(x=>'<div class="lrow"><b>'+escapeHtml(x.height)+' 板</b><div class="track"><div class="bar" style="width:'+Math.max(4,(x.count/max)*100)+'%"></div></div><div style="text-align:right">'+escapeHtml(x.count)+'</div><div class="codes">'+escapeHtml((x.codes||[]).join(" · "))+'</div></div>').join(""):'<div class="empty">暂无连板高度数据。</div>';
 const mainlines=leaders.mainline_leaders||[];
 $("mainlineLeaders").innerHTML=mainlines.length?mainlines.map(x=>'<div class="item"><div><b>'+escapeHtml(x.mainline||"主线待归属")+'</b><small>主线排名 #'+escapeHtml(x.mainline_rank||"—")+'</small></div><div style="text-align:right"><b>'+escapeHtml(x.code)+'</b><small>'+escapeHtml(x.height==null?"高度未知":x.height+" 板")+'</small></div></div>').join(""):'<div class="empty">暂无可识别的主线龙头。</div>';
 const candidates=review.review_candidates||[];
 $("candidates").innerHTML=candidates.map(x=>'<tr><td><b class="code">'+escapeHtml(x.code)+'</b><br><span class="sub">'+escapeHtml(x.name)+'</span></td><td>'+escapeHtml(x.mainline?.board_name||"—")+'</td><td>'+escapeHtml(x.role||"未知")+'</td><td>'+escapeHtml(x.height==null?"—":x.height+" 板")+'</td><td><b>'+escapeHtml(fmt(x.review_score))+'</b></td><td>'+escapeHtml(x.eligibility||"unknown")+'</td><td>'+escapeHtml(x.coverage==null?"—":pct(x.coverage))+'</td></tr>').join("");
 $("emptyCandidates").hidden=candidates.length>0;
 $("coverage").textContent="涨停池覆盖："+(coverage.complete?"完整":"不完整")+" · 已观测 "+fmt(coverage.observed_total)+" / 报告 "+fmt(coverage.reported_total);
}
async function loadSnapshot(){
 if(!selectedDate){showNotice("云端数据库目前没有复盘快照。请在允许时段先执行龙头扫描，再执行盘后复盘。");$("metrics").innerHTML=metricCard("情绪温度","—","等待真实复盘数据");$("leaderCards").innerHTML="";$("ladder").innerHTML="";$("mainlineLeaders").innerHTML="";$("candidates").innerHTML="";$("emptyCandidates").hidden=false;return;}
 const snapshot=await api("/api/prep/"+encodeURIComponent(selectedDate)+"/snapshot?slim=true");
 render(snapshot);showNotice("");
}
async function refreshAll(){
 $("refresh").disabled=true;
 try{await loadCalendar();await loadSnapshot();await refreshEligibility();}
 catch(e){showNotice(e.message,true);}
 finally{$("refresh").disabled=false;}
}
async function refreshEligibility(){
 const [scan,prep]=await Promise.all([
  api("/api/runs/scan/eligibility"),
  api("/api/runs/prep/eligibility")
 ]);
 const line=(job,label)=>label+"："+(job.enabled?"可执行":(job.blockers||[]).map(x=>x.text).join("；"));
 $("eligibility").textContent=line(scan,"扫描")+"　|　"+line(prep,"复盘");
 $("scan").disabled=!scan.enabled;
 $("prep").disabled=!prep.enabled;
}
async function runJob(job){
 if(activeJob)return;
 activeJob=job;
 const button=$(job);
 button.disabled=true;
 $("jobStatus").textContent=(job==="scan"?"正在启动龙头扫描…":"正在启动盘后复盘…");
 try{
  const body=job==="scan"?{top:25,candidates:5,workers:2}:{mode:"incremental"};
  await api("/api/runs/"+job,{method:"POST",body:JSON.stringify(body)});
  await pollJob(job);
 }catch(e){$("jobStatus").textContent=e.message;activeJob=null;await refreshEligibility().catch(()=>{});}
}
async function pollJob(job){
 try{
  const status=await api("/api/runs/"+job+"/status");
  const last=status.last_run;
  $("jobStatus").textContent=last?(last.label+" · "+status.state+(last.output_tail?"\\n"+last.output_tail:"")):"任务状态等待中";
  if(status.state==="running"){pollHandle=window.setTimeout(()=>pollJob(job),2500);return;}
  activeJob=null;
  await refreshAll();
 }catch(e){$("jobStatus").textContent=e.message;activeJob=null;}
}
$("refresh").addEventListener("click",refreshAll);
$("date").addEventListener("change",async e=>{selectedDate=e.target.value;try{await loadSnapshot()}catch(err){showNotice(err.message,true)}});
$("scan").addEventListener("click",()=>runJob("scan"));
$("prep").addEventListener("click",()=>runJob("prep"));
refreshAll();
</script>
</body>
</html>"""
