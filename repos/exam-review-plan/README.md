# exam-review-plan
# 考试复习计划 (Exam Review Plan)

一款基于 HarmonyOS NEXT 的考试倒计时与复习计划管理应用,帮助你在考试前的剩余时间里合理安排复习日程,把握每一秒。

## 功能特性

### 考试倒计时
- 实时显示距离考试的剩余时间(天 / 时 / 分 / 秒,每秒刷新)
- 顶部渐变卡片直观展示倒计时
- 显示考试日期和星期
- 自动计算复习进度百分比

### 复习计划管理
- 自定义添加复习计划:复习内容、复习日期、时长、备注
- 按日期升序自动排列,日程一目了然
- 一键标记完成 / 未完成(完成后显示删除线)
- 支持编辑和删除已有计划
- 完成进度统计(已完成 / 总数 + 百分比)

### 数据持久化
- 基于 HarmonyOS Preferences API
- 关闭应用后数据不丢失
- 无需联网,完全本地存储

## 技术栈

| 项目 | 说明 |
|------|------|
| 操作系统 | HarmonyOS NEXT |
| 语言 | ArkTS |
| UI 框架 | ArkUI 声明式开发范式 |
| 数据存储 | @kit.ArkData - Preferences |
| API 版本 | compatibleSdkVersion 6.1.1 (API 24) |
| 构建工具 | Hvigor |

## 项目结构

```
deveeco/
├── AppScope/                                # 应用级配置
│   ├── app.json5                           # 应用配置
│   └── resources/base/                     # 应用资源(字符串、图标)
├── entry/                                   # 主模块
│   ├── src/main/
│   │   ├── ets/
│   │   │   ├── entryability/EntryAbility.ets         # 入口 Ability
│   │   │   ├── entrybackupability/EntryBackupAbility.ets
│   │   │   ├── model/
│   │   │   │   └── DataStore.ets                      # 数据存储层
│   │   │   └── pages/
│   │   │       └── Index.ets                          # 主页面
│   │   ├── module.json5                    # 模块配置
│   │   └── resources/                      # 模块资源
│   ├── build-profile.json5
│   ├── hvigorfile.ts
│   └── oh-package.json5
├── hvigor/hvigor-config.json5              # 构建配置
├── build-profile.json5                     # 项目级构建配置
├── oh-package.json5                        # 项目级依赖
├── code-linter.json5                       # 代码检查配置
└── .gitignore
```

## 核心代码说明

### 数据模型 — `entry/src/main/ets/model/DataStore.ets`

定义了两个核心数据结构:

```typescript
// 考试信息
interface ExamInfo {
  name: string;        // 考试名称
  timestamp: number;   // 考试时间戳(毫秒)
}

// 复习计划项
interface ReviewPlan {
  id: string;           // 唯一 ID
  timestamp: number;   // 计划日期时间戳
  content: string;     // 复习内容
  duration: number;    // 时长(分钟)
  completed: boolean;  // 是否完成
  note: string;        // 备注
}
```

`DataStore` 采用单例模式,通过 Preferences 实现:
- `getExam()` / `saveExam()` — 读取和保存考试信息
- `getPlans()` / `savePlans()` — 读取和保存复习计划列表

### 主页面 — `entry/src/main/ets/pages/Index.ets`

包含以下 UI 组件:
- **buildCountdownCard** — 顶部倒计时卡片(渐变背景)
- **buildPlanList** — 复习计划列表(支持滚动)
- **buildPlanItem** — 单条计划项(状态切换、编辑、删除)
- **buildExamDialog** — 设置考试弹窗
- **buildPlanDialog** — 添加/编辑计划弹窗

## 安装与运行

### 环境要求
- [DevEco Studio](https://developer.harmonyos.com/cn/develop/deveco-studio/) 5.0 及以上
- HarmonyOS SDK (API 24+)
- HarmonyOS NEXT 设备或模拟器

### 步骤
1. 克隆仓库到本地:
   ```bash
   git clone https://github.com/你的用户名/exam-review-plan.git
   ```
2. 用 DevEco Studio 打开项目目录
3. 等待 IDE 自动同步依赖(ohpm install)
4. 连接 HarmonyOS 设备或启动模拟器
5. 点击工具栏的 **Run** 按钮(或按 `Shift + F10`)构建并运行

## 使用说明

### 首次使用
1. 打开应用,会看到顶部显示"暂未设置考试"
2. 点击底部的 **设置考试** 按钮
3. 输入考试名称(如"期末考试")和考试日期(格式:YYYY-MM-DD)
4. 点击保存,顶部卡片将开始倒计时

### 添加复习计划
1. 点击底部的 **添加计划** 按钮
2. 填写复习内容、复习日期、时长(分钟)、备注(可选)
3. 点击保存,计划将出现在列表中并按日期排序

### 管理计划
- **标记完成**:点击计划左侧的圆形按钮,切换完成状态
- **编辑计划**:点击计划右侧的"编辑"文字,修改后保存
- **删除计划**:点击计划右侧的"删除"文字,立即移除

### 查看进度
- 顶部卡片的进度条显示已完成计划占总计划的百分比
- 卡片右下角显示 `已完成数 / 总数`

## 界面预览

![Uploading image.png…]()

```

## 开发说明

### 倒计时实现
使用 `setInterval` 每秒更新状态变量,在 `aboutToAppear` 中启动定时器,在 `aboutToDisappear` 中清除定时器,避免内存泄漏。

### 数据绑定
通过 ArkUI 的 `@State` 装饰器声明状态变量,UI 会自动响应数据变化并重新渲染。

### 自定义弹窗
使用 `Stack` + 条件渲染(`if this.dialogMode === 1`)实现自定义弹窗,而非系统弹窗组件,以获得更灵活的样式控制。

## 兼容性
- 支持 HarmonyOS NEXT 设备(phone 类型)
- 支持浅色和深色模式
- 不需要任何特殊权限

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议,可自由使用和修改。

## 反馈与贡献

欢迎提交 Issue 或 Pull Request 来改进本项目。

