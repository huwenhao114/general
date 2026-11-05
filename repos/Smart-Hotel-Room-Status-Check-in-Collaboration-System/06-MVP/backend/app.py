# -*- coding: utf-8 -*-
"""
酒店房态与入住协同系统 - Flask 后端服务
提供 RESTful API：房态管理、入住办理、协同任务、统计数据

启动方式：
    pip install flask
    python app.py
默认运行在 http://127.0.0.1:5000
"""
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from db import get_conn, init_db, seed_data, STATUSES

app = Flask(__name__, static_folder=None)
CORS(app)  # 允许前端跨域访问

# ---------------------------------------------------------------------------
# 初始化数据库
# ---------------------------------------------------------------------------
@app.before_request
def _ensure_db():
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'hotel.db')):
        init_db()
        seed_data()


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def row_to_dict(row):
    """sqlite3.Row 转 dict"""
    return dict(row) if row else None


def ok(data=None, msg='success'):
    """统一成功响应"""
    return jsonify({'code': 0, 'msg': msg, 'data': data})


def fail(msg='error', code=1, status=400):
    """统一失败响应"""
    return jsonify({'code': code, 'msg': msg, 'data': None}), status


# ---------------------------------------------------------------------------
# 静态前端托管（可选，直接通过后端访问前端）
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    # API 路径交给具体路由处理，不进入静态文件托管
    if filename.startswith('api/'):
        return fail('接口不存在', status=404)
    return send_from_directory(FRONTEND_DIR, filename)


# ---------------------------------------------------------------------------
# 一、房态管理 API
# ---------------------------------------------------------------------------
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """获取房间列表，支持按楼层/状态筛选"""
    floor = request.args.get('floor', type=int)
    status = request.args.get('status')

    sql = 'SELECT * FROM rooms WHERE 1=1'
    params = []
    if floor:
        sql += ' AND floor = ?'
        params.append(floor)
    if status:
        sql += ' AND status = ?'
        params.append(status)
    sql += ' ORDER BY num'

    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return ok([row_to_dict(r) for r in rows])


@app.route('/api/rooms/stats', methods=['GET'])
def get_room_stats():
    """获取房态统计"""
    conn = get_conn()
    total = conn.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]
    counts = {}
    for s in STATUSES:
        counts[s] = conn.execute('SELECT COUNT(*) FROM rooms WHERE status=?', (s,)).fetchone()[0]
    conn.close()
    occ = counts.get('occupied', 0)
    return ok({
        'total': total,
        'occupied': occ,
        'vacant': counts.get('vacant', 0),
        'cleaning': counts.get('cleaning', 0),
        'maintenance': counts.get('maintenance', 0),
        'reserved': counts.get('reserved', 0),
        'checkout': counts.get('checkout', 0),
        'occupancy_rate': round(occ / total * 100, 1) if total else 0
    })


@app.route('/api/rooms/<int:num>', methods=['GET'])
def get_room(num):
    """获取单个房间详情"""
    conn = get_conn()
    row = conn.execute('SELECT * FROM rooms WHERE num=?', (num,)).fetchone()
    conn.close()
    if not row:
        return fail(f'房间 {num} 不存在', status=404)
    return ok(row_to_dict(row))


@app.route('/api/rooms/<int:num>', methods=['PUT'])
def update_room(num):
    """更新房间状态"""
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')

    if new_status not in STATUSES:
        return fail(f'非法房态: {new_status}，有效值: {STATUSES}')

    conn = get_conn()
    row = conn.execute('SELECT * FROM rooms WHERE num=?', (num,)).fetchone()
    if not row:
        conn.close()
        return fail(f'房间 {num} 不存在', status=404)

    old_status = row['status']
    now = datetime.now().strftime('%H:%M')

    # 状态变更后的联动逻辑
    guest = row['guest']
    checkin_time = row['checkin_time']

    if new_status == 'occupied' and not guest:
        # 新入住：默认填充（实际由入住接口办理时设置）
        guest = data.get('guest', '临时客人')
        checkin_time = now
    elif new_status != 'occupied':
        # 非在住状态清空客人信息
        guest = None
        checkin_time = None

    conn.execute(
        'UPDATE rooms SET status=?, guest=?, checkin_time=? WHERE num=?',
        (new_status, guest, checkin_time, num)
    )

    # 从在住变为其他状态时，自动生成清洁任务
    created_task = None
    if old_status == 'occupied' and new_status in ('checkout', 'cleaning', 'vacant'):
        cur = conn.execute(
            'INSERT INTO tasks (title, description, department, priority, status, created_at) '
            'VALUES (?,?,?,?,?,?)',
            (f'{num}房清洁', '客人已离店，需清洁', '客房部', 'mid', 'pending',
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        created_task = cur.lastrowid

    conn.commit()
    conn.close()

    return ok({
        'num': num,
        'status': new_status,
        'guest': guest,
        'checkin_time': checkin_time,
        'created_task_id': created_task
    }, f'房态已更新: {num} → {new_status}')


# ---------------------------------------------------------------------------
# 二、入住办理 API
# ---------------------------------------------------------------------------
@app.route('/api/checkin', methods=['POST'])
def do_checkin():
    """办理入住"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    idcard = (data.get('idcard') or '').strip()
    phone = (data.get('phone') or '').strip()
    room_num = data.get('room_num')
    way = data.get('way', '前台人工')
    deposit = int(data.get('deposit', 0))

    if not name or not idcard or not room_num:
        return fail('姓名、证件号、房间号不能为空')

    conn = get_conn()
    room = conn.execute('SELECT * FROM rooms WHERE num=?', (room_num,)).fetchone()
    if not room:
        conn.close()
        return fail(f'房间 {room_num} 不存在', status=404)
    if room['status'] != 'vacant':
        conn.close()
        return fail(f'房间 {room_num} 当前状态为 {room["status"]}，无法入住', status=400)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 写入入住记录
    cur = conn.execute(
        'INSERT INTO checkins (room_num, room_type, name, idcard, phone, way, deposit, time) '
        'VALUES (?,?,?,?,?,?,?,?)',
        (room_num, room['type'], name, idcard, phone, way, deposit, now)
    )
    checkin_id = cur.lastrowid
    # 更新房态为已入住
    conn.execute(
        'UPDATE rooms SET status=?, guest=?, checkin_time=? WHERE num=?',
        ('occupied', name, now[11:16], room_num)
    )
    conn.commit()
    conn.close()

    return ok({
        'id': checkin_id,
        'room_num': room_num,
        'name': name,
        'time': now
    }, f'{name} 入住 {room_num} 成功')


@app.route('/api/checkin', methods=['GET'])
def get_checkins():
    """获取入住记录列表"""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM checkins ORDER BY id DESC').fetchall()
    conn.close()
    return ok([row_to_dict(r) for r in rows])


# ---------------------------------------------------------------------------
# 三、协同任务 API
# ---------------------------------------------------------------------------
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取协同任务列表"""
    conn = get_conn()
    rows = conn.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
    conn.close()
    return ok([row_to_dict(r) for r in rows])


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建协同任务"""
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        return fail('任务标题不能为空')

    description = data.get('description', '')
    department = data.get('department', '客房部')
    priority = data.get('priority', 'mid')
    if priority not in ('low', 'mid', 'high'):
        priority = 'mid'

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_conn()
    cur = conn.execute(
        'INSERT INTO tasks (title, description, department, priority, status, created_at) '
        'VALUES (?,?,?,?,?,?)',
        (title, description, department, priority, 'pending', now)
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return ok({'id': task_id, 'title': title}, '任务创建成功')


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务状态"""
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ('pending', 'doing', 'done'):
        return fail(f'非法任务状态: {new_status}')

    conn = get_conn()
    row = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
    if not row:
        conn.close()
        return fail(f'任务 {task_id} 不存在', status=404)

    conn.execute('UPDATE tasks SET status=? WHERE id=?', (new_status, task_id))
    conn.commit()
    conn.close()
    return ok({'id': task_id, 'status': new_status}, f'任务已更新为 {new_status}')


# ---------------------------------------------------------------------------
# 四、综合统计 API
# ---------------------------------------------------------------------------
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """管理驾驶舱综合数据"""
    conn = get_conn()
    total = conn.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]
    occupied = conn.execute('SELECT COUNT(*) FROM rooms WHERE status="occupied"').fetchone()[0]
    vacant = conn.execute('SELECT COUNT(*) FROM rooms WHERE status="vacant"').fetchone()[0]
    cleaning = conn.execute('SELECT COUNT(*) FROM rooms WHERE status="cleaning"').fetchone()[0]
    today_checkins = conn.execute('SELECT COUNT(*) FROM checkins WHERE date(time)=date("now")').fetchone()[0]
    pending_tasks = conn.execute('SELECT COUNT(*) FROM tasks WHERE status="pending"').fetchone()[0]
    doing_tasks = conn.execute('SELECT COUNT(*) FROM tasks WHERE status="doing"').fetchone()[0]
    conn.close()

    return ok({
        'total_rooms': total,
        'occupied': occupied,
        'vacant': vacant,
        'cleaning': cleaning,
        'occupancy_rate': round(occupied / total * 100, 1) if total else 0,
        'today_checkins': today_checkins,
        'pending_tasks': pending_tasks,
        'doing_tasks': doing_tasks,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    init_db()
    seed_data()
    print('=' * 60)
    print('  酒店房态与入住协同系统 MVP 后端已启动')
    print(f'  服务地址: http://127.0.0.1:5001')
    print(f'  前端入口: http://127.0.0.1:5001/')
    print(f'  API 文档:')
    print(f'    GET  /api/rooms          - 房间列表')
    print(f'    GET  /api/rooms/stats    - 房态统计')
    print(f'    PUT  /api/rooms/<num>    - 更新房态')
    print(f'    POST /api/checkin        - 办理入住')
    print(f'    GET  /api/checkin        - 入住记录')
    print(f'    GET  /api/tasks          - 协同任务列表')
    print(f'    POST /api/tasks          - 创建任务')
    print(f'    PUT  /api/tasks/<id>     - 更新任务')
    print(f'    GET  /api/dashboard      - 驾驶舱数据')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5001, debug=False)
