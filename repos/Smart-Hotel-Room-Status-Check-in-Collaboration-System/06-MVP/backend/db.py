# -*- coding: utf-8 -*-
"""
酒店房态与入住协同系统 - 数据库模块
SQLite 数据库连接、表结构初始化、种子数据
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'hotel.db')

ROOM_TYPES = ['标准间', '大床房', '商务房', '套房']
STATUSES = ['occupied', 'vacant', 'cleaning', 'maintenance', 'reserved', 'checkout']
DEPARTMENTS = ['客房部', '工程部', '餐饮部', '安保部']
PRIORITIES = ['low', 'mid', 'high']
TASK_STATUS = ['pending', 'doing', 'done']


def get_conn():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_conn()
    cur = conn.cursor()

    # 房间表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            num         INTEGER PRIMARY KEY,
            floor       INTEGER NOT NULL,
            type        TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'vacant',
            guest       TEXT,
            checkin_time TEXT
        )
    ''')

    # 入住记录表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            room_num    INTEGER NOT NULL,
            room_type   TEXT NOT NULL,
            name        TEXT NOT NULL,
            idcard      TEXT NOT NULL,
            phone       TEXT,
            way         TEXT NOT NULL,
            deposit     INTEGER DEFAULT 0,
            time        TEXT NOT NULL
        )
    ''')

    # 协同任务表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            department  TEXT NOT NULL,
            priority    TEXT NOT NULL DEFAULT 'mid',
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print(f'[DB] 数据库初始化完成: {DB_PATH}')


def seed_data():
    """填充种子数据（仅在房间表为空时执行）"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM rooms')
    if cur.fetchone()[0] > 0:
        conn.close()
        print('[DB] 房间数据已存在，跳过种子填充')
        return

    # 生成 5 层 x 20 间 = 100 间房
    import random
    random.seed(42)
    now = datetime.now()
    for floor in range(1, 6):
        for n in range(1, 21):
            num = floor * 100 + n
            r = random.random()
            if r < 0.55:
                status = 'occupied'
                guest = random.choice(['张先生', '李女士', '王总', '刘女士', '陈先生', '杨女士', '赵先生', '黄女士'])
                checkin_time = f'{random.randint(10, 22):02d}:{random.randint(0, 59):02d}'
            elif r < 0.75:
                status, guest, checkin_time = 'vacant', None, None
            elif r < 0.88:
                status, guest, checkin_time = 'cleaning', None, None
            elif r < 0.93:
                status, guest, checkin_time = 'maintenance', None, None
            elif r < 0.97:
                status, guest, checkin_time = 'reserved', None, None
            else:
                status, guest, checkin_time = 'checkout', None, None

            room_type = random.choice(ROOM_TYPES)
            cur.execute(
                'INSERT INTO rooms (num, floor, type, status, guest, checkin_time) VALUES (?,?,?,?,?,?)',
                (num, floor, room_type, status, guest, checkin_time)
            )

    # 初始协同任务
    seed_tasks = [
        ('1008房紧急清洁', '客人14:00入住，需提前清洁', '客房部', 'high', 'pending'),
        ('502房空调维修', '客人反馈空调不制冷', '工程部', 'high', 'doing'),
        ('3楼走廊灯光检查', '例行巡检', '工程部', 'low', 'pending'),
        ('805房布草更换', '长住客每周更换', '客房部', 'mid', 'done'),
    ]
    for title, desc, dept, pri, st in seed_tasks:
        cur.execute(
            'INSERT INTO tasks (title, description, department, priority, status, created_at) VALUES (?,?,?,?,?,?)',
            (title, desc, dept, pri, st, now.strftime('%Y-%m-%d %H:%M:%S'))
        )

    conn.commit()
    conn.close()
    print('[DB] 种子数据填充完成: 100间房 + 4条协同任务')


if __name__ == '__main__':
    init_db()
    seed_data()
