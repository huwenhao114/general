# -*- coding: utf-8 -*-
"""青麓景区客流与服务调度系统 MVP 后端"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, random
from db import init_db, DB_PATH

app = Flask(__name__, static_folder=None)
CORS(app)
init_db()

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ok(data=None, msg='success'):
    return jsonify({'code':0, 'data':data, 'msg':msg})

# ===== 托管前端 =====
FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')
@app.route('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND, path)

# ===== 区域客流 =====
@app.route('/api/areas')
def get_areas():
    conn = db(); rows = conn.execute('SELECT * FROM areas ORDER BY id').fetchall()
    conn.close()
    data = []
    for r in rows:
        d = dict(r)
        d['crowd_rate'] = round(d['current_flow']/d['capacity']*100, 1)
        data.append(d)
    return ok(data)

@app.route('/api/areas/stats')
def area_stats():
    conn = db()
    total = conn.execute('SELECT SUM(current_flow) as s FROM areas').fetchone()['s'] or 0
    crowded = conn.execute("SELECT COUNT(*) as c FROM areas WHERE current_flow > capacity").fetchone()['c']
    normal = conn.execute("SELECT COUNT(*) as c FROM areas WHERE current_flow <= capacity").fetchone()['c']
    conn.close()
    return ok({'total_flow': total, 'crowded_areas': crowded, 'normal_areas': normal, 'total_areas': 6})

@app.route('/api/areas/<name>', methods=['PUT'])
def update_area(name):
    flow = request.json.get('flow')
    conn = db()
    cap = conn.execute('SELECT capacity FROM areas WHERE name=?', (name,)).fetchone()
    if not cap: return ok(None, '区域不存在'), 404
    status = 'crowded' if flow > cap['capacity'] else 'normal'
    conn.execute('UPDATE areas SET current_flow=?, status=? WHERE name=?', (flow, status, name))
    conn.execute('INSERT INTO flow_records(area_name,flow) VALUES(?,?)', (name, flow))
    # 客流超阈值自动生成调度任务
    if status == 'crowded':
        existing = conn.execute("SELECT COUNT(*) FROM tasks WHERE title LIKE ? AND status!='done'", (f'%{name}%',)).fetchone()[0]
        if existing == 0:
            conn.execute("INSERT INTO tasks(title,description,department,priority,status) VALUES(?,?,?,?,?)",
                        (f'{name}客流超阈值分流', f'{name}客流{flow}人超承载量，建议分流至空闲区域', '入口引导员', 'high', 'pending'))
    conn.commit(); conn.close()
    return ok(None, '更新成功')

@app.route('/api/areas/<name>/spots')
def get_spots(name):
    conn = db()
    rows = conn.execute('SELECT * FROM spots WHERE area_name=?', (name,)).fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

# ===== AI分流建议 =====
@app.route('/api/ai/suggest')
def ai_suggest():
    conn = db()
    rows = conn.execute('SELECT * FROM areas ORDER BY id').fetchall()
    conn.close()
    areas = [dict(r) for r in rows]
    crowded = sorted([a for a in areas if a['current_flow'] > a['capacity']], key=lambda x:x['current_flow']/x['capacity'], reverse=True)
    free = sorted([a for a in areas if a['current_flow'] < a['capacity']*0.6], key=lambda x:x['current_flow']/x['capacity'])
    suggestions = []
    for c in crowded[:3]:
        rate = round(c['current_flow']/c['capacity']*100,1)
        target = free[0]['name'] if free else '其他区域'
        suggestions.append({
            'from': c['name'], 'to': target,
            'crowd_rate': rate,
            'reason': f'{c["name"]}拥挤度{rate}%，建议引导游客前往{target}（空闲率高）'
        })
    if not suggestions:
        suggestions.append({'from':'-','to':'-','crowd_rate':0,'reason':'当前各区域客流均衡，无需分流'})
    return ok(suggestions)

# ===== 调度工单 =====
@app.route('/api/tasks', methods=['GET','POST'])
def tasks():
    conn = db()
    if request.method == 'POST':
        d = request.json
        conn.execute('INSERT INTO tasks(title,description,department,priority,status) VALUES(?,?,?,?,?)',
                    (d['title'], d.get('description',''), d.get('department',''), d.get('priority','mid'), 'pending'))
        conn.commit(); conn.close()
        return ok(None, '任务创建成功')
    rows = conn.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
    conn.close()
    return ok([dict(r) for r in rows])

@app.route('/api/tasks/<int:tid>', methods=['PUT'])
def update_task(tid):
    status = request.json.get('status')
    conn = db()
    conn.execute('UPDATE tasks SET status=? WHERE id=?', (status, tid))
    conn.commit(); conn.close()
    return ok(None, '状态更新成功')

# ===== 驾驶舱 =====
@app.route('/api/dashboard')
def dashboard():
    conn = db()
    areas = conn.execute('SELECT name,current_flow,capacity FROM areas').fetchall()
    total_flow = sum(a['current_flow'] for a in areas)
    tasks = conn.execute('SELECT status, COUNT(*) as c FROM tasks GROUP BY status').fetchall()
    task_stat = {t['status']: t['c'] for t in tasks}
    records = conn.execute('SELECT * FROM flow_records ORDER BY time DESC LIMIT 20').fetchall()
    conn.close()
    return ok({
        'total_flow': total_flow,
        'areas': [dict(a) for a in areas],
        'tasks': {'pending': task_stat.get('pending',0), 'doing': task_stat.get('doing',0), 'done': task_stat.get('done',0)},
        'recent_records': [dict(r) for r in records]
    })

if __name__ == '__main__':
    print('='*60)
    print('  青麓景区客流与服务调度系统 MVP 后端已启动')
    print('  服务地址: http://127.0.0.1:5002')
    print('  前端入口: http://127.0.0.1:5002/')
    print('='*60)
    app.run(host='0.0.0.0', port=5002, debug=False)
