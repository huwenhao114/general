# 酒店房态与入住协同系统 MVP

一个可运行的全栈最小可行产品，包含 **Flask 后端** + **SQLite 数据库** + **原生前端**。

## 📁 目录结构

```
06-MVP/
├── backend/                 # 后端服务（Python Flask + SQLite）
│   ├── app.py              # 主应用：API 路由 + 前端托管
│   ├── db.py               # 数据库初始化、表结构、种子数据
│   ├── requirements.txt    # Python 依赖
│   ├── start.bat           # Windows 一键启动脚本
│   └── README.md           # 后端详细文档
├── frontend/                # 前端页面（原生 HTML/CSS/JS）
│   ├── index.html          # 主页面
│   ├── css/style.css       # 样式
│   └── js/app.js           # 业务逻辑（API 优先 + 离线降级）
└── README.md                # 本文件
```

## 🚀 快速启动

### 方式一：完整模式（推荐）

```bash
cd backend
pip install -r requirements.txt
python app.py
```

启动后浏览器访问 **http://127.0.0.1:5001/**

Windows 用户可直接双击 `backend/start.bat`。

### 方式二：离线模式（仅前端）

如果不想启动后端，可直接双击 `frontend/index.html` 用浏览器打开。
此时数据存储在浏览器 localStorage 中，功能完整但不与后端同步。

前端会自动检测后端是否在线，右上角显示当前模式：
- 🟢 **后端在线**：数据走真实 API，存储在 SQLite
- 🟠 **离线模式**：数据存储在浏览器 localStorage

## 🎯 功能模块

### 1. 房态看板
- 5 层楼 × 20 间 = 100 间房的实时状态矩阵
- 颜色区分：在住 / 空净可售 / 待清洁 / 维修中 / 已预订 / 今日离店
- 点击房间查看详情并修改房态
- 修改房态触发联动（如离店自动生成清洁任务）

### 2. 入住办理
- 录入客人信息（姓名、证件号、电话）
- 选择空净房间办理入住
- 支持自助机/小程序/前台人工三种方式
- 入住成功后房态自动更新

### 3. 协同任务
- 跨部门工单（客房部、工程部等）
- 优先级标识（高/中/低）
- 状态流转：待处理 → 处理中 → 已完成
- 离店自动生成清洁任务

### 4. 入住记录
- 查看所有入住记录
- 证件号脱敏显示
- 支持按时间倒序

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rooms` | 房间列表 |
| GET | `/api/rooms/stats` | 房态统计 |
| PUT | `/api/rooms/<num>` | 更新房态 |
| POST | `/api/checkin` | 办理入住 |
| GET | `/api/checkin` | 入住记录 |
| GET | `/api/tasks` | 任务列表 |
| POST | `/api/tasks` | 创建任务 |
| PUT | `/api/tasks/<id>` | 更新任务 |
| GET | `/api/dashboard` | 驾驶舱数据 |

## 🛠️ 技术栈

- **后端**: Python 3.8+ / Flask 3 / SQLite3
- **前端**: 原生 HTML5 + CSS3 + JavaScript (ES6+)
- **数据**: SQLite（文件型数据库，零配置）

## 🔄 重置数据

- **后端模式**：删除 `backend/hotel.db`，重启服务自动重建
- **离线模式**：点击页面右上角"重置"按钮
