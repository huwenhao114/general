// 青麓景区客流与服务调度 MVP 前端逻辑
const API = 'http://127.0.0.1:5002/api';
let online = false;
let currentArea = null;

// 检测后端是否在线
async function checkOnline() {
  try {
    const r = await fetch(API + '/areas/stats');
    online = r.ok;
  } catch { online = false; }
  const dot = document.querySelector('.dot');
  const txt = document.getElementById('statusText');
  if (online) { dot.classList.add('online'); txt.textContent = '后端在线'; }
  else { dot.classList.remove('online'); txt.textContent = '离线模式'; }
}

// 切换视图
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-' + btn.dataset.view).classList.add('active');
    if (btn.dataset.view === 'ai') loadAI();
    if (btn.dataset.view === 'tasks') loadTasks();
    if (btn.dataset.view === 'records') loadRecords();
  });
});

// 加载统计 + 客流看板
async function loadDashboard() {
  try {
    const [stats, areas] = await Promise.all([
      fetch(API + '/areas/stats').then(r => r.json()),
      fetch(API + '/areas').then(r => r.json())
    ]);
    const s = stats.data;
    document.getElementById('statsBar').innerHTML = `
      <div class="stat-card"><div class="l">当前在园总客流</div><div class="v">${s.total_flow.toLocaleString()}</div></div>
      <div class="stat-card ${s.crowded_areas>0?'danger':'ok'}"><div class="l">拥挤区域</div><div class="v">${s.crowded_areas}</div></div>
      <div class="stat-card ok"><div class="l">正常区域</div><div class="v">${s.normal_areas}</div></div>
      <div class="stat-card warn"><div class="l">总区域数</div><div class="v">${s.total_areas}</div></div>`;
    const grid = document.getElementById('areaGrid');
    grid.innerHTML = areas.data.map(a => {
      const rate = Math.round(a.current_flow / a.capacity * 100);
      const cls = rate >= 100 ? 'danger' : rate >= 80 ? 'warn' : 'ok';
      const cardCls = rate >= 100 ? 'crowded' : '';
      return `<div class="area-card ${cardCls}" onclick="openFlowModal('${a.name}',${a.capacity},${a.current_flow})">
        <div class="an">${a.name}</div>
        <div class="af">${a.current_flow} <small style="font-size:13px;color:#9ca3af">/ ${a.capacity}人</small></div>
        <span class="rate ${cls}">拥挤度 ${rate}%</span>
      </div>`;
    }).join('');
  } catch(e) { console.error(e); }
}

// 修改客流弹窗
function openFlowModal(name, cap, flow) {
  currentArea = name;
  document.getElementById('modalArea').textContent = name;
  document.getElementById('modalCap').textContent = cap;
  document.getElementById('modalFlow').value = flow;
  document.getElementById('flowModal').style.display = 'flex';
}
function closeModal() { document.getElementById('flowModal').style.display = 'none'; }
async function saveFlow() {
  const flow = parseInt(document.getElementById('modalFlow').value);
  if (!flow) return alert('请输入客流人数');
  try {
    await fetch(API + '/areas/' + encodeURIComponent(currentArea), {
      method:'PUT', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({flow})
    });
    closeModal();
    loadDashboard();
    alert('客流已更新，拥挤区域将自动生成分流任务');
  } catch(e) { alert('更新失败'); }
}

// AI分流建议
async function loadAI() {
  try {
    const r = await fetch(API + '/ai/suggest');
    const d = await r.json();
    document.getElementById('aiSuggestions').innerHTML = d.data.map(s => {
      const ok = s.crowd_rate === 0;
      return `<div class="ai-card ${ok?'ok':''}">
        <div class="from-to">${ok?'✅ 客流均衡':`⚠️ ${s.from} → ${s.to}`}</div>
        <div class="reason">${s.reason}</div>
      </div>`;
    }).join('');
  } catch(e) { console.error(e); }
}

// 调度工单
async function loadTasks() {
  try {
    const r = await fetch(API + '/tasks');
    const d = await r.json();
    document.getElementById('taskList').innerHTML = d.data.map(t => {
      const stMap = {pending:['待处理','pending'],doing:['进行中','doing'],done:['已完成','done']};
      return `<div class="task-item ${t.priority}">
        <div class="tt">${t.title}</div>
        <div class="td">${t.description}</div>
        <div class="meta">
          <span>👤 ${t.department}</span>
          <span>⏰ ${t.created_at}</span>
          <span class="tag ${stMap[t.status][1]}">${stMap[t.status][0]}</span>
          <div class="actions">
            ${t.status!=='doing'?`<button class="btn-ghost" onclick="updateTask(${t.id},'doing')">接单</button>`:''}
            ${t.status!=='done'?`<button class="btn-primary" onclick="updateTask(${t.id},'done')">完成</button>`:''}
          </div>
        </div>
      </div>`;
    }).join('');
  } catch(e) { console.error(e); }
}

function showTaskForm() { document.getElementById('taskForm').style.display = 'flex'; }
async function createTask() {
  const title = document.getElementById('tfTitle').value;
  if (!title) return alert('请输入任务标题');
  const data = {
    title, description: document.getElementById('tfDesc').value,
    department: document.getElementById('tfDept').value,
    priority: document.getElementById('tfPri').value
  };
  await fetch(API + '/tasks', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  document.getElementById('tfTitle').value = '';
  document.getElementById('tfDesc').value = '';
  document.getElementById('taskForm').style.display = 'none';
  loadTasks();
}
async function updateTask(id, status) {
  await fetch(API + '/tasks/' + id, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})});
  loadTasks();
}

// 调度记录
async function loadRecords() {
  try {
    const r = await fetch(API + '/dashboard');
    const d = await r.json();
    document.getElementById('recordTable').innerHTML = d.data.recent_records.map(rc =>
      `<tr><td>${rc.time}</td><td>${rc.area_name}</td><td>${rc.flow} 人</td></tr>`
    ).join('');
  } catch(e) { console.error(e); }
}

// 初始化
checkOnline().then(() => { loadDashboard(); setInterval(loadDashboard, 10000); });
