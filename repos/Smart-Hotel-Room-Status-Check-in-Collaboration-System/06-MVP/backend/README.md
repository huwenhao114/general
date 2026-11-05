# 酒店房态与入住协同系统 MVP - 后端

基于 Python Flask + SQLite 的 RESTful API 服务。

## 技术栈

- **Web 框架**: Flask 3.1
- **数据库**: SQLite3（内置，零配置）
- **跨域**: flask-cors
- **前端托管**: 同时托管 `../frontend/` 静态文件

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py
```

启动后访问：
- 前端页面：http://127.0.0.1:5001/
- API 接口：http://127.0.0.1:5001/api/...

首次启动会自动创建 `hotel.db` 数据库并填充 100 间房的种子数据。

## API 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rooms?floor=1&status=vacant` | 房间列表（支持按楼层/状态筛选） |
| GET | `/api/rooms/stats` | 房态统计（各状态数量+入住率） |
| GET | `/api/rooms/<num>` | 单个房间详情 |
| PUT | `/api/rooms/<num>` | 更新房态（body: `{"status":"cleaning"}`） |
| POST | `/api/checkin` | 办理入住 |
| GET | `/api/checkin` | 入住记录列表 |
| GET | `/api/tasks` | 协同任务列表 |
| POST | `/api/tasks` | 创建协同任务 |
| PUT | `/api/tasks/<id>` | 更新任务状态 |
| GET | `/api/dashboard` | 管理驾驶舱综合数据 |

## 数据模型

### rooms（房间表）
| 字段 | 类型 | 说明 |
|------|------|------|
| num | INTEGER PK | 房号 |
| floor | INTEGER | 楼层 |
| type | TEXT | 房型 |
| status | TEXT | 房态（occupied/vacant/cleaning/maintenance/reserved/checkout） |
| guest | TEXT | 入住客人 |
| checkin_time | TEXT | 入住时间 |

### checkins（入住记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| room_num | INTEGER | 房号 |
| room_type | TEXT | 房型 |
| name | TEXT | 客人姓名 |
| idcard | TEXT | 证件号 |
| phone | TEXT | 联系电话 |
| way | TEXT | 入住方式 |
| deposit | INTEGER | 押金 |
| time | TEXT | 办理时间 |

### tasks（协同任务表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| title | TEXT | 任务标题 |
| description | TEXT | 任务描述 |
| department | TEXT | 负责部门 |
| priority | TEXT | 优先级（low/mid/high） |
| status | TEXT | 状态（pending/doing/done） |
| created_at | TEXT | 创建时间 |

## 核心业务逻辑

- **房态联动**：房间从"在住"变为其他状态时，自动生成清洁任务
- **入住校验**：仅"空净可售"状态的房间可办理入住
- **数据持久化**：SQLite 文件 `hotel.db`，删除后重启可重新生成种子数据

## 重置数据

```bash
# 删除数据库文件，重启服务即可重新生成
del hotel.db
python app.py
```
