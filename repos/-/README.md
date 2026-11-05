# 习惯打卡 (Habit Tracker)

一款基于 HarmonyOS ArkTS 开发的习惯养成打卡应用，帮助你记录每日习惯、坚持打卡、养成好习惯。

## 功能特性

- **习惯管理**：添加、删除习惯，支持自定义图标、颜色和目标天数
- **每日打卡**：一键打卡 / 取消打卡，自动计算连续天数与累计天数
- **今日进度**：主页顶部进度条实时显示今日完成情况
- **打卡详情**：查看单个习惯的统计数据和最近 7 天打卡记录，支持补打卡
- **深色模式**：跟随系统自动适配深色 / 浅色主题
- **本地存储**：基于 HarmonyOS Preferences 轻量键值存储，数据离线保存不丢失

## 应用截图

<img width="631" height="397" alt="image" src="https://github.com/user-attachments/assets/7a91b106-7906-4528-a989-8540a2f9868b" />


## 技术栈

| 项 | 说明 |
|----|------|
| 开发语言 | ArkTS |
| UI 框架 | ArkUI（声明式开发范式） |
| 数据存储 | @ohos.data.preferences |
| 开发工具 | DevEco Studio |
| 编译 SDK | 26.0.0 |
| 兼容版本 | 6.1.1 (API 24) |

## 项目结构

```
├── AppScope/                    # 应用全局配置
├── entry/src/main/
│   ├── ets/
│   │   ├── entryability/        # EntryAbility 入口
│   │   ├── models/
│   │   │   └── HabitModel.ets   # 数据模型（Habit / CheckinRecord）
│   │   ├── services/
│   │   │   └── HabitStorage.ets # Preferences 存储服务封装
│   │   └── pages/
│   │       ├── Index.ets        # 主页面（习惯列表、进度条、添加弹窗）
│   │       └── HabitDetailPage.ets # 详情页（统计、近7天记录、删除）
│   └── resources/               # 颜色、字符串等资源
```

## 快速开始

1. 安装 [DevEco Studio](https://developer.huawei.com/consumer/cn/develop/)
2. 克隆本仓库：
   ```bash
   git clone https://github.com/你的用户名/habit-tracker.git
   ```
3. 用 DevEco Studio 打开项目目录，等待依赖同步完成
4. 运行方式（三选一）：
   - **预览器**：打开 `entry/src/main/ets/pages/Index.ets`，点击编辑器右侧 Previewer
   - **模拟器**：Tools → Device Manager 创建并启动模拟器，点击 Run
   - **真机**：配置签名（File → Project Structure → Signing Configs）后连接鸿蒙设备运行

## 数据模型

```typescript
interface Habit {
  id: string;            // 唯一标识
  name: string;          // 习惯名称
  icon: string;          // 图标（emoji）
  color: string;         // 主题色
  targetDays: number;    // 目标天数
  streakCount: number;   // 连续打卡天数
  totalCount: number;    // 累计打卡天数
  lastCheckinDate: string; // 最后打卡日期
}
```

## License

MIT
