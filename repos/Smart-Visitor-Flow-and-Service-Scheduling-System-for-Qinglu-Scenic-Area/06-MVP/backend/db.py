# -*- coding: utf-8 -*-
"""数据库表结构 + 种子数据"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'scenic.db')

AREAS = [
    ('入口广场', 1500, 1820),
    ('核心观景区', 1000, 1240),
    ('西区竹林', 1200, 480),
    ('南区花海', 900, 760),
    ('东区索道', 800, 950),
    ('北区古街', 1000, 1120),
]

AREA_DETAILS = {
    '入口广场': ['101','102','103','104','105'],
    '核心观景区': ['201','202','203','204','205'],
    '西区竹林': ['301','302','303','304','305'],
    '南区花海': ['401','402','403','404','405'],
    '东区索道': ['501','502','503','504','505'],
    '北区古街': ['601','602','603','604','605'],
}

INIT_TASKS = [
    ('入口广场客流超阈值', '引导员立即开展分流，引导游客前往西区竹林', '入口引导员', 'high', 'doing'),
    ('东区索道排队疏导', '索道排队超20分钟，增开临时通道', '区域引导员', 'high', 'doing'),
    ('南区花海保洁', '游客遗留垃圾较多，安排保洁清理', '保洁', 'mid', 'pending'),
    ('入口闸机巡检', '每日例行设备巡检', '设备维护', 'low', 'done'),
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        capacity INTEGER,
        current_flow INTEGER,
        status TEXT DEFAULT 'normal'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS spots (
        id TEXT PRIMARY KEY,
        area_name TEXT,
        flow INTEGER DEFAULT 0,
        status TEXT DEFAULT 'normal'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        department TEXT,
        priority TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS flow_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_name TEXT,
        flow INTEGER,
        time TEXT DEFAULT (datetime('now','localtime'))
    )''')

    # 种子数据
    c.execute('SELECT COUNT(*) FROM areas')
    if c.fetchone()[0] == 0:
        for name, cap, flow in AREAS:
            c.execute('INSERT INTO areas(name,capacity,current_flow,status) VALUES(?,?,?,?)',
                      (name, cap, flow, 'crowded' if flow > cap else 'normal'))
        for area, spots in AREA_DETAILS.items():
            base = AREAS[[a[0] for a in AREAS].index(area)][2] // 5
            for sp in spots:
                c.execute('INSERT INTO spots(id,area_name,flow,status) VALUES(?,?,?,?)',
                          (sp, area, base + (hash(sp)%40-20), 'normal'))
        for t in INIT_TASKS:
            c.execute('INSERT INTO tasks(title,description,department,priority,status) VALUES(?,?,?,?,?)', t)
        for name, cap, flow in AREAS:
            c.execute('INSERT INTO flow_records(area_name,flow) VALUES(?,?)', (name, flow))
        print('[DB] 种子数据填充完成')

    conn.commit()
    conn.close()
    print('[DB] 数据库初始化完成:', DB_PATH)

if __name__ == '__main__':
    init_db()
