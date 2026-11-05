// 酒店房态与入住协同 MVP - 主逻辑
// 支持两种模式：后端API模式（优先） / localStorage 离线模式（降级）

const API_BASE = 'http://127.0.0.1:5001';
let backendAvailable = false;

// ---------- API 层（带降级） ----------
async function apiGet(path) {
  try {
    const r = await fetch(API_BASE + path);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const json = await r.json();
    if (json.code !== 0) throw new Error(json.msg);
    return json.data;
  } catch (e) {
    throw e;
  }
}

async function apiPut(path, body) {
  const r = await fetch(API_BASE + path, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const json = await r.json();
  if (json.code !== 0) throw new Error(json.msg);
  return json.data;
}

async function apiPost(path, body) {
  const r = await fetch(API_BASE + path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const json = await r.json();
  if (json.code !== 0) throw new Error(json.msg);
  return json.data;
}

// 检测后端是否可用
async function checkBackend() {
  try {
    await apiGet('/api/dashboard');
    backendAvailable = true;
    document.getElementById('modeBadge').textContent = '后端在线';
    document.getElementById('modeBadge').className = 'tag tag-green';
  } catch (e) {
    backendAvailable = false;
    document.getElementById('modeBadge').textContent = '离线模式';
    document.getElementById('modeBadge').className = 'tag tag-orange';
  }
}

// ---------- 数据层（根据模式切换） ----------
const statusMap = {
  occupied: { label: '在住', cls: 'occupied', tag: 'tag-red' },
  vacant: { label: '空净可售', cls: 'vacant', tag: 'tag-green' },
  cleaning: { label: '待清洁', cls: 'cleaning', tag: 'tag-orange' },
  maintenance: { label: '维修中', cls: 'maintenance', tag: 'tag-gray' },
  reserved: { label: '已预订', cls: 'reserved', tag: 'tag-blue' },
  checkout: { label: '今日离店', cls: 'checkout', tag: 'tag-gray' }
};

let rooms = [];
let checkins = [];
let collabTasks = [];

// 离线模式：从 localStorage 加载
function loadOfflineData() {
  const roomTypes = ['标准间', '大床房', '商务房', '套房'];
  const saved = localStorage.getItem('mvp_rooms');
  if (saved) {
    rooms = JSON.parse(saved);
  } else {
    rooms = [];
    for (let f = 1; f <= 5; f++) {
      for (let n = 1; n <= 20; n++) {
        const num = f * 100 + n;
        const r = Math.random();
        let s, guest = null, ct = null;
        if (r < 0.55) { s = 'occupied'; guest = randomGuest(); ct = randomTime(); }
        else if (r < 0.75) s = 'vacant';
        else if (r < 0.88) s = 'cleaning';
        else if (r < 0.93) s = 'maintenance';
        else if (r < 0.97) s = 'reserved';
        else s = 'checkout';
        rooms.push({ num, floor: f, type: roomTypes[Math.floor(Math.random()*4)], status: s, guest, checkin_time: ct });
      }
    }
  }
  checkins = JSON.parse(localStorage.getItem('mvp_checkins') || '[]');
  const savedTasks = localStorage.getItem('mvp_tasks');
  collabTasks = savedTasks ? JSON.parse(savedTasks) : [
    { id: 1, title: '1008房紧急清洁', desc: '客人14:00入住，需提前清洁', department: '客房部', priority: 'high', status: 'pending' },
    { id: 2, title: '502房空调维修', desc: '客人反馈空调不制冷', department: '工程部', priority: 'high', status: 'doing' },
    { id: 3, title: '3楼走廊灯光检查', desc: '例行巡检', department: '工程部', priority: 'low', status: 'pending' },
    { id: 4, title: '805房布草更换', desc: '长住客每周更换', department: '客房部', priority: 'mid', status: 'done' }
  ];
}

function saveOfflineData() {
  localStorage.setItem('mvp_rooms', JSON.stringify(rooms));
  localStorage.setItem('mvp_checkins', JSON.stringify(checkins));
  localStorage.setItem('mvp_tasks', JSON.stringify(collabTasks));
}

function randomGuest() {
  const s = ['张','李','王','刘','陈','杨','赵','黄','周','吴'];
  return s[Math.floor(Math.random()*s.length)] + (Math.random()>0.5?'先生':'女士');
}
function randomTime() {
  return `${String(10+Math.floor(Math.random()*10)).padStart(2,'0')}:${String(Math.floor(Math.random()*60)).padStart(2,'0')}`;
}

// ---------- 数据加载统一入口 ----------
async function loadAllData() {
  if (backendAvailable) {
    rooms = await apiGet('/api/rooms');
    checkins = await apiGet('/api/checkin');
    collabTasks = await apiGet('/api/tasks');
  } else {
    loadOfflineData();
  }
  updateStats();
}

// ---------- 页面切换 ----------
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
  const link = document.querySelector(`.nav-links a[data-page="${id}"]`);
  if (link) link.classList.add('active');
  if (id === 'page-board') renderBoard();
  if (id === 'page-checkin') renderCheckinForm();
  if (id === 'page-tasks') renderTasks();
  if (id === 'page-records') renderRecords();
}

// ---------- 统计 ----------
function updateStats() {
  const total = rooms.length;
  const occ = rooms.filter(r => r.status === 'occupied').length;
  const vac = rooms.filter(r => r.status === 'vacant').length;
  const cln = rooms.filter(r => r.status === 'cleaning').length;
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statOcc').textContent = occ + ` (${total?(occ/total*100).toFixed(1):0}%)`;
  document.getElementById('statVac').textContent = vac;
  document.getElementById('statCln').textContent = cln;
}

// ---------- 房态看板 ----------
let currentFloor = 1;
function renderBoard() {
  const tabs = document.querySelector('.floor-tabs');
  tabs.innerHTML = '';
  for (let f = 1; f <= 5; f++) {
    const t = document.createElement('div');
    t.className = 'floor-tab' + (f === currentFloor ? ' active' : '');
    t.textContent = `${f}楼`;
    t.onclick = () => { currentFloor = f; renderBoard(); };
    tabs.appendChild(t);
  }
  const board = document.getElementById('roomBoard');
  board.innerHTML = '';
  rooms.filter(r => r.floor === currentFloor).forEach(r => {
    const card = document.createElement('div');
    card.className = `room-card ${statusMap[r.status].cls}`;
    card.innerHTML = `<div class="rn">${r.num}</div><div class="rt">${r.type}</div>`;
    card.onclick = () => showRoomDetail(r);
    board.appendChild(card);
  });
}

function showRoomDetail(r) {
  const modal = document.getElementById('roomModal');
  const info = statusMap[r.status];
  document.getElementById('modalRoomNum').textContent = r.num;
  document.getElementById('modalRoomType').textContent = r.type;
  document.getElementById('modalStatus').innerHTML = `<span class="tag ${info.tag}">${info.label}</span>`;
  document.getElementById('modalGuest').textContent = r.guest || '—';
  document.getElementById('modalCheckinTime').textContent = r.checkin_time || '—';
  const select = document.getElementById('modalStatusSelect');
  select.innerHTML = '';
  Object.entries(statusMap).forEach(([k, v]) => {
    const opt = document.createElement('option');
    opt.value = k; opt.textContent = v.label;
    if (k === r.status) opt.selected = true;
    select.appendChild(opt);
  });
  document.getElementById('modalRoomNum').dataset.num = r.num;
  modal.classList.add('show');
}

async function saveRoomStatus() {
  const num = parseInt(document.getElementById('modalRoomNum').dataset.num);
  const newStatus = document.getElementById('modalStatusSelect').value;
  try {
    if (backendAvailable) {
      await apiPut(`/api/rooms/${num}`, { status: newStatus });
      await loadAllData();
    } else {
      const room = rooms.find(r => r.num === num);
      const old = room.status;
      room.status = newStatus;
      if (newStatus === 'occupied' && !room.guest) { room.guest = randomGuest(); room.checkin_time = randomTime(); }
      if (newStatus !== 'occupied') { room.guest = null; room.checkin_time = null; }
      if (old === 'occupied' && newStatus !== 'occupied') {
        collabTasks.unshift({ id: Date.now(), title: `${num}房清洁`, desc: '客人已离店，需清洁', department: '客房部', priority: 'mid', status: 'pending' });
      }
      saveOfflineData();
    }
    document.getElementById('roomModal').classList.remove('show');
    renderBoard();
    updateStats();
    showToast(`房态已更新：${num}房 → ${statusMap[newStatus].label}`);
  } catch (e) {
    showToast('更新失败: ' + e.message, 'error');
  }
}

// ---------- 入住办理 ----------
function renderCheckinForm() {
  const vacantRooms = rooms.filter(r => r.status === 'vacant');
  const select = document.getElementById('ciRoomSelect');
  select.innerHTML = '<option value="">请选择空房</option>';
  vacantRooms.forEach(r => {
    select.innerHTML += `<option value="${r.num}">${r.num}房 - ${r.type}</option>`;
  });
}

async function doCheckin() {
  const name = document.getElementById('ciName').value.trim();
  const idcard = document.getElementById('ciIdcard').value.trim();
  const phone = document.getElementById('ciPhone').value.trim();
  const roomNum = document.getElementById('ciRoomSelect').value;
  const way = document.getElementById('ciWay').value;
  const deposit = parseInt(document.getElementById('ciDeposit').value) || 0;

  if (!name || !idcard || !roomNum) { showToast('请填写姓名、证件号并选择房间', 'error'); return; }

  try {
    if (backendAvailable) {
      await apiPost('/api/checkin', { name, idcard, phone, room_num: parseInt(roomNum), way, deposit });
      await loadAllData();
    } else {
      const room = rooms.find(r => r.num === parseInt(roomNum));
      room.status = 'occupied'; room.guest = name;
      room.checkin_time = new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'});
      checkins.unshift({ id: Date.now(), room_num: room.num, room_type: room.type, name, idcard, phone, way, deposit, time: new Date().toLocaleString('zh-CN') });
      saveOfflineData();
    }
    showToast(`${name} 办理入住成功！房号 ${roomNum}`);
    ['ciName','ciIdcard','ciPhone','ciDeposit'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('ciRoomSelect').value = '';
    updateStats();
  } catch (e) {
    showToast('入住失败: ' + e.message, 'error');
  }
}

// ---------- 协同任务 ----------
function renderTasks() {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  if (collabTasks.length === 0) {
    list.innerHTML = '<div style="text-align:center;color:#999;padding:30px">暂无协同任务</div>';
    return;
  }
  collabTasks.forEach(t => {
    const pri = { high: 'tag-red', mid: 'tag-orange', low: 'tag-blue' }[t.priority] || 'tag-orange';
    const priLabel = { high: '高', mid: '中', low: '低' }[t.priority] || '中';
    const stLabel = { pending: '待处理', doing: '处理中', done: '已完成' }[t.status] || t.status;
    const stTag = { pending: 'tag-orange', doing: 'tag-blue', done: 'tag-green' }[t.status] || 'tag-gray';
    list.innerHTML += `
      <div class="collab-item">
        <div class="info">
          <div class="title">${t.title} <span class="tag ${pri}">${priLabel}优先级</span> <span class="tag ${stTag}">${stLabel}</span></div>
          <div class="desc">${t.description || t.desc || ''} · ${t.department}</div>
        </div>
        <div class="actions">
          ${t.status !== 'done' ? `<button class="btn btn-success" onclick="updateTask(${t.id},'done')">完成</button>` : ''}
          ${t.status === 'pending' ? `<button class="btn btn-warning" onclick="updateTask(${t.id},'doing')">接单</button>` : ''}
        </div>
      </div>`;
  });
}

async function updateTask(id, status) {
  try {
    if (backendAvailable) {
      await apiPut(`/api/tasks/${id}`, { status });
      await loadAllData();
    } else {
      const t = collabTasks.find(x => x.id === id);
      t.status = status;
      saveOfflineData();
    }
    renderTasks();
    showToast(`任务已更新为${status === 'done' ? '已完成' : '处理中'}`);
  } catch (e) {
    showToast('操作失败: ' + e.message, 'error');
  }
}

async function addTask() {
  const title = prompt('请输入任务标题：');
  if (!title) return;
  const desc = prompt('请输入任务描述：') || '';
  try {
    if (backendAvailable) {
      await apiPost('/api/tasks', { title, description: desc, department: '客房部', priority: 'mid' });
      await loadAllData();
    } else {
      collabTasks.unshift({ id: Date.now(), title, desc, department: '客房部', priority: 'mid', status: 'pending' });
      saveOfflineData();
    }
    renderTasks();
    showToast('任务已创建');
  } catch (e) {
    showToast('创建失败: ' + e.message, 'error');
  }
}

// ---------- 入住记录 ----------
function renderRecords() {
  const tbody = document.getElementById('recordsBody');
  tbody.innerHTML = '';
  if (checkins.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;padding:30px">暂无入住记录</td></tr>';
    return;
  }
  checkins.forEach(c => {
    const wayTag = (c.way === '自助机' || c.way === '小程序') ? 'tag-green' : 'tag-blue';
    const masked = (c.idcard || '').replace(/^(.{6}).*(.{4})$/, '$1********$2');
    tbody.innerHTML += `<tr>
      <td>${c.room_num}</td><td>${c.room_type}</td><td>${c.name}</td>
      <td>${masked}</td><td><span class="tag ${wayTag}">${c.way}</span></td>
      <td>¥${c.deposit || 0}</td><td>${c.time}</td>
    </tr>`;
  });
}

// ---------- 工具 ----------
function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (type === 'error' ? ' error' : '');
  setTimeout(() => t.classList.remove('show'), 2500);
}

async function resetData() {
  if (!confirm('确定要重置所有数据吗？')) return;
  if (backendAvailable) {
    showToast('后端模式下请删除 backend/hotel.db 后重启服务', 'error');
    return;
  }
  localStorage.clear();
  loadOfflineData();
  showPage('page-board');
  showToast('数据已重置');
}

async function refreshData() {
  await loadAllData();
  showPage(document.querySelector('.page.active').id);
  showToast('数据已刷新');
}

// ---------- 初始化 ----------
(async function init() {
  await checkBackend();
  await loadAllData();
  showPage('page-board');
})();
