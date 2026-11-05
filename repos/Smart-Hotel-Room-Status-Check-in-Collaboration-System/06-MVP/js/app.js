// 酒店房态与入住协同 MVP - 主逻辑
// 数据层
const roomTypes = ['标准间', '大床房', '商务房', '套房'];
const statusMap = {
  occupied: { label: '在住', cls: 'occupied', tag: 'tag-red' },
  vacant: { label: '空净可售', cls: 'vacant', tag: 'tag-green' },
  cleaning: { label: '待清洁', cls: 'cleaning', tag: 'tag-orange' },
  maintenance: { label: '维修中', cls: 'maintenance', tag: 'tag-gray' },
  reserved: { label: '已预订', cls: 'reserved', tag: 'tag-blue' },
  checkout: { label: '今日离店', cls: 'checkout', tag: 'tag-gray' }
};

// 初始化房间数据（5层 x 20间 = 100间）
let rooms = JSON.parse(localStorage.getItem('mvp_rooms')) || initRooms();
let checkins = JSON.parse(localStorage.getItem('mvp_checkins')) || [];
let collabTasks = JSON.parse(localStorage.getItem('mvp_tasks')) || initTasks();

function initRooms() {
  const arr = [];
  for (let f = 1; f <= 5; f++) {
    for (let n = 1; n <= 20; n++) {
      const num = f * 100 + n;
      const r = Math.random();
      let s;
      if (r < 0.6) s = 'occupied';
      else if (r < 0.78) s = 'vacant';
      else if (r < 0.88) s = 'cleaning';
      else if (r < 0.92) s = 'maintenance';
      else if (r < 0.97) s = 'reserved';
      else s = 'checkout';
      arr.push({
        num, floor: f, type: roomTypes[Math.floor(Math.random() * roomTypes.length)],
        status: s, guest: s === 'occupied' ? randomGuest() : null,
        checkinTime: s === 'occupied' ? randomTime() : null
      });
    }
  }
  return arr;
}

function initTasks() {
  return [
    { id: 1, title: '1008房紧急清洁', desc: '客人14:00入住，需提前清洁', dept: '客房部', priority: 'high', status: 'pending' },
    { id: 2, title: '502房空调维修', desc: '客人反馈空调不制冷', dept: '工程部', priority: 'high', status: 'doing' },
    { id: 3, title: '3楼走廊灯光检查', desc: '例行巡检', dept: '工程部', priority: 'low', status: 'pending' },
    { id: 4, title: '805房布草更换', desc: '长住客每周更换', dept: '客房部', priority: 'mid', status: 'done' }
  ];
}

function randomGuest() {
  const surnames = ['张', '李', '王', '刘', '陈', '杨', '赵', '黄', '周', '吴'];
  return surnames[Math.floor(Math.random() * surnames.length)] + (Math.random() > 0.5 ? '先生' : '女士');
}
function randomTime() {
  const h = 10 + Math.floor(Math.random() * 10);
  const m = Math.floor(Math.random() * 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function saveData() {
  localStorage.setItem('mvp_rooms', JSON.stringify(rooms));
  localStorage.setItem('mvp_checkins', JSON.stringify(checkins));
  localStorage.setItem('mvp_tasks', JSON.stringify(collabTasks));
}

// 页面切换
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
  document.querySelector(`.nav-links a[data-page="${id}"]`).classList.add('active');
  if (id === 'page-board') renderBoard();
  if (id === 'page-checkin') renderCheckinForm();
  if (id === 'page-tasks') renderTasks();
  if (id === 'page-records') renderRecords();
  updateStats();
}

// 统计
function updateStats() {
  const total = rooms.length;
  const occ = rooms.filter(r => r.status === 'occupied').length;
  const vac = rooms.filter(r => r.status === 'vacant').length;
  const cln = rooms.filter(r => r.status === 'cleaning').length;
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statOcc').textContent = occ + ` (${(occ/total*100).toFixed(1)}%)`;
  document.getElementById('statVac').textContent = vac;
  document.getElementById('statCln').textContent = cln;
}

// 房态看板
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
  document.getElementById('modalCheckinTime').textContent = r.checkinTime || '—';
  
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

function saveRoomStatus() {
  const num = parseInt(document.getElementById('modalRoomNum').dataset.num);
  const newStatus = document.getElementById('modalStatusSelect').value;
  const room = rooms.find(r => r.num === num);
  const oldStatus = room.status;
  room.status = newStatus;
  if (newStatus === 'occupied' && !room.guest) {
    room.guest = randomGuest();
    room.checkinTime = randomTime();
  }
  if (newStatus !== 'occupied') { room.guest = null; room.checkinTime = null; }
  if (oldStatus === 'occupied' && newStatus !== 'occupied') {
    // 自动生成清洁任务
    collabTasks.unshift({
      id: Date.now(), title: `${num}房清洁`, desc: '客人已离店，需清洁',
      dept: '客房部', priority: 'mid', status: 'pending'
    });
  }
  saveData();
  document.getElementById('roomModal').classList.remove('show');
  renderBoard();
  updateStats();
  showToast(`房态已更新：${num}房 → ${statusMap[newStatus].label}`);
}

// 入住办理
function renderCheckinForm() {
  const vacantRooms = rooms.filter(r => r.status === 'vacant');
  const select = document.getElementById('ciRoomSelect');
  select.innerHTML = '<option value="">请选择空房</option>';
  vacantRooms.forEach(r => {
    select.innerHTML += `<option value="${r.num}">${r.num}房 - ${r.type}</option>`;
  });
}

function doCheckin() {
  const name = document.getElementById('ciName').value.trim();
  const idcard = document.getElementById('ciIdcard').value.trim();
  const phone = document.getElementById('ciPhone').value.trim();
  const roomNum = document.getElementById('ciRoomSelect').value;
  const way = document.getElementById('ciWay').value;
  const deposit = document.getElementById('ciDeposit').value;

  if (!name || !idcard || !roomNum) {
    showToast('请填写姓名、证件号并选择房间', 'error');
    return;
  }
  const room = rooms.find(r => r.num === parseInt(roomNum));
  room.status = 'occupied';
  room.guest = name;
  room.checkinTime = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

  checkins.unshift({
    id: Date.now(), roomNum: room.num, roomType: room.type,
    name, idcard, phone, way, deposit,
    time: new Date().toLocaleString('zh-CN')
  });
  saveData();
  showToast(`${name} 办理入住成功！房号 ${room.num}`);
  // 清空表单
  ['ciName', 'ciIdcard', 'ciPhone', 'ciDeposit'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('ciRoomSelect').value = '';
  updateStats();
}

// 协同任务
function renderTasks() {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  collabTasks.forEach(t => {
    const pri = { high: 'tag-red', mid: 'tag-orange', low: 'tag-blue' }[t.priority];
    const priLabel = { high: '高', mid: '中', low: '低' }[t.priority];
    const st = { pending: '待处理', doing: '处理中', done: '已完成' }[t.status];
    const stTag = { pending: 'tag-orange', doing: 'tag-blue', done: 'tag-green' }[t.status];
    list.innerHTML += `
      <div class="collab-item">
        <div class="info">
          <div class="title">${t.title} <span class="tag ${pri}">${priLabel}优先级</span> <span class="tag ${stTag}">${st}</span></div>
          <div class="desc">${t.desc} · ${t.dept}</div>
        </div>
        <div class="actions">
          ${t.status !== 'done' ? `<button class="btn btn-success" onclick="updateTask(${t.id},'done')">完成</button>` : ''}
          ${t.status === 'pending' ? `<button class="btn btn-warning" onclick="updateTask(${t.id},'doing')">接单</button>` : ''}
        </div>
      </div>`;
  });
}

function updateTask(id, status) {
  const t = collabTasks.find(x => x.id === id);
  t.status = status;
  saveData();
  renderTasks();
  showToast(`任务「${t.title}」已更新为${status === 'done' ? '已完成' : '处理中'}`);
}

function addTask() {
  const title = prompt('请输入任务标题：');
  if (!title) return;
  const desc = prompt('请输入任务描述：') || '';
  collabTasks.unshift({
    id: Date.now(), title, desc, dept: '客房部', priority: 'mid', status: 'pending'
  });
  saveData();
  renderTasks();
  showToast('任务已创建');
}

// 入住记录
function renderRecords() {
  const tbody = document.getElementById('recordsBody');
  tbody.innerHTML = '';
  if (checkins.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;padding:30px">暂无入住记录</td></tr>';
    return;
  }
  checkins.forEach(c => {
    const wayTag = c.way === '自助机' || c.way === '小程序' ? 'tag-green' : 'tag-blue';
    tbody.innerHTML += `<tr>
      <td>${c.roomNum}</td><td>${c.roomType}</td><td>${c.name}</td>
      <td>${c.idcard.replace(/^(.{6}).*(.{4})$/, '$1********$2')}</td>
      <td><span class="tag ${wayTag}">${c.way}</span></td>
      <td>¥${c.deposit || 0}</td><td>${c.time}</td>
    </tr>`;
  });
}

// 工具
function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (type === 'error' ? ' error' : '');
  setTimeout(() => t.classList.remove('show'), 2500);
}

function resetData() {
  if (!confirm('确定要重置所有数据吗？')) return;
  localStorage.clear();
  rooms = initRooms();
  checkins = [];
  collabTasks = initTasks();
  saveData();
  showPage('page-board');
  showToast('数据已重置');
}

// 初始化
showPage('page-board');
