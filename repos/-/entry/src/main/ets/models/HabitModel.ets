/** 习惯数据模型 */

/** 习惯定义 */
export interface Habit {
  /** 唯一标识 */
  id: string;
  /** 习惯名称 */
  name: string;
  /** 图标 emoji */
  icon: string;
  /** 卡片主题色，十六进制 */
  color: string;
  /** 目标频率：每周哪几天打卡，0=周日, 1=周一 ... 6=周六 */
  targetDays: number[];
  /** 连续打卡天数 */
  streakCount: number;
  /** 总打卡天数 */
  totalCount: number;
  /** 最后一次打卡日期 yyyy-MM-dd */
  lastCheckinDate: string;
  /** 创建时间戳 */
  createdAt: number;
  /** 排序序号 */
  sortIndex: number;
}

/** 打卡记录 */
export interface CheckinRecord {
  /** 习惯 ID */
  habitId: string;
  /** 日期 yyyy-MM-dd */
  date: string;
  /** 是否完成 */
  isCompleted: boolean;
}

/** 习惯统计信息 */
export interface HabitStats {
  /** 今日是否已打卡 */
  isCheckinToday: boolean;
  /** 本周打卡天数 */
  weekCount: number;
  /** 连续打卡天数 */
  streakCount: number;
  /** 总打卡天数 */
  totalCount: number;
}

/** 创建习惯时的预设模板 */
export interface HabitTemplate {
  name: string;
  icon: string;
  color: string;
  targetDays: number[];
}

/** 预设习惯模板列表 */
export const HABIT_TEMPLATES: HabitTemplate[] = [
  { name: '早起', icon: '🌅', color: '#FF6B6B', targetDays: [1, 2, 3, 4, 5, 6, 0] },
  { name: '运动', icon: '🏃', color: '#4ECDC4', targetDays: [1, 2, 3, 4, 5] },
  { name: '阅读', icon: '📚', color: '#45B7D1', targetDays: [1, 2, 3, 4, 5, 6, 0] },
  { name: '冥想', icon: '🧘', color: '#96CEB4', targetDays: [1, 2, 3, 4, 5, 6, 0] },
  { name: '喝水', icon: '💧', color: '#51CF66', targetDays: [1, 2, 3, 4, 5, 6, 0] },
  { name: '学习', icon: '✏️', color: '#FFD43B', targetDays: [1, 2, 3, 4, 5] },
  { name: '早睡', icon: '🌙', color: '#845EF7', targetDays: [1, 2, 3, 4, 5, 6, 0] },
  { name: '日记', icon: '📝', color: '#FF922B', targetDays: [1, 2, 3, 4, 5, 6, 0] },
];
