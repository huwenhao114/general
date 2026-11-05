import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';
import { Habit, CheckinRecord } from '../models/HabitModel';

const STORE_NAME = 'habit_store';
const KEY_HABITS = 'habits';
const KEY_CHECKINS = 'checkins';

/**
 * 习惯数据存储服务，基于 Preferences 轻量键值存储
 */
export class HabitStorage {
  private static instance: HabitStorage | null = null;
  private prefs: preferences.Preferences | null = null;

  private constructor() {}

  static getInstance(): HabitStorage {
    if (HabitStorage.instance === null) {
      HabitStorage.instance = new HabitStorage();
    }
    return HabitStorage.instance;
  }

  /** 初始化 Preferences 实例 */
  async init(context: common.Context): Promise<void> {
    if (this.prefs !== null) {
      return;
    }
    this.prefs = await preferences.getPreferences(context, STORE_NAME);
  }

  /** 安全 flush，捕获 Promise 异常 */
  private async safeFlush(): Promise<void> {
    if (this.prefs === null) {
      return;
    }
    try {
      await this.prefs.flush();
    } catch (e) {
      console.error(`HabitStorage flush failed: ${JSON.stringify(e)}`);
    }
  }

  /** 生成唯一 ID */
  private generateId(): string {
    return `habit_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
  }

  /** 获取所有习惯 */
  async getAllHabits(): Promise<Habit[]> {
    if (this.prefs === null) {
      return [];
    }
    try {
      const raw = await this.prefs.get(KEY_HABITS, '[]') as string;
      const habits: Habit[] = JSON.parse(raw) as Habit[];
      return habits.sort((a, b) => a.sortIndex - b.sortIndex);
    } catch (e) {
      console.error(`getAllHabits failed: ${JSON.stringify(e)}`);
      return [];
    }
  }

  /** 添加新习惯 */
  async addHabit(name: string, icon: string, color: string, targetDays: number[]): Promise<Habit> {
    const habits = await this.getAllHabits();
    const newHabit: Habit = {
      id: this.generateId(),
      name: name,
      icon: icon,
      color: color,
      targetDays: targetDays,
      streakCount: 0,
      totalCount: 0,
      lastCheckinDate: '',
      createdAt: Date.now(),
      sortIndex: habits.length,
    };
    habits.push(newHabit);
    await this.saveHabits(habits);
    return newHabit;
  }

  /** 删除习惯 */
  async deleteHabit(habitId: string): Promise<void> {
    const habits = await this.getAllHabits();
    const filtered = habits.filter(h => h.id !== habitId);
    // 重新排序
    filtered.forEach((h, i) => { h.sortIndex = i; });
    await this.saveHabits(filtered);

    // 同时删除该习惯的打卡记录
    const checkins = await this.getAllCheckins();
    const filteredCheckins = checkins.filter(c => c.habitId !== habitId);
    await this.saveCheckins(filteredCheckins);
  }

  /** 保存习惯列表到存储 */
  private async saveHabits(habits: Habit[]): Promise<void> {
    if (this.prefs === null) {
      return;
    }
    await this.prefs.put(KEY_HABITS, JSON.stringify(habits));
    await this.safeFlush();
  }

  /** 获取所有打卡记录 */
  async getAllCheckins(): Promise<CheckinRecord[]> {
    if (this.prefs === null) {
      return [];
    }
    try {
      const raw = await this.prefs.get(KEY_CHECKINS, '[]') as string;
      return JSON.parse(raw) as CheckinRecord[];
    } catch (e) {
      console.error(`getAllCheckins failed: ${JSON.stringify(e)}`);
      return [];
    }
  }

  /** 保存打卡记录列表 */
  private async saveCheckins(checkins: CheckinRecord[]): Promise<void> {
    if (this.prefs === null) {
      return;
    }
    await this.prefs.put(KEY_CHECKINS, JSON.stringify(checkins));
    await this.safeFlush();
  }

  /** 切换某天某习惯的打卡状态 */
  async toggleCheckin(habitId: string, date: string): Promise<boolean> {
    const habits = await this.getAllHabits();
    const habit = habits.find(h => h.id === habitId);
    if (habit === undefined) {
      return false;
    }

    const checkins = await this.getAllCheckins();
    const existing = checkins.find(c => c.habitId === habitId && c.date === date);

    if (existing !== undefined) {
      // 已打卡 → 取消
      existing.isCompleted = !existing.isCompleted;
      if (!existing.isCompleted) {
        habit.totalCount = Math.max(0, habit.totalCount - 1);
        habit.streakCount = await this.recalculateStreak(habitId, checkins.filter(c => c.isCompleted));
      }
    } else {
      // 未打卡 → 新增
      checkins.push({ habitId, date, isCompleted: true });
      habit.totalCount += 1;
      habit.lastCheckinDate = date;
      habit.streakCount = await this.recalculateStreak(habitId, checkins.filter(c => c.isCompleted));
    }

    await this.saveHabits(habits);
    await this.saveCheckins(checkins);
    return true;
  }

  /** 重新计算连续天数 */
  private async recalculateStreak(habitId: string, completedCheckins: CheckinRecord[]): Promise<number> {
    const dates = completedCheckins
      .filter(c => c.habitId === habitId)
      .map(c => c.date)
      .sort();

    if (dates.length === 0) {
      return 0;
    }

    let streak = 0;
    let current = new Date();
    current.setHours(0, 0, 0, 0);

    // 从今天往回数连续天数
    while (true) {
      const dateStr = this.formatDate(current);
      if (dates.includes(dateStr)) {
        streak++;
        current.setDate(current.getDate() - 1);
      } else {
        // 如果今天还没打卡，但昨天有，从昨天开始算
        if (streak === 0 && dates.length > 0) {
          const yesterday = new Date(current);
          yesterday.setDate(yesterday.getDate() - 1);
          if (dates.includes(this.formatDate(yesterday))) {
            current = yesterday;
            continue;
          }
        }
        break;
      }
    }
    return streak;
  }

  /** 检查某天是否已打卡 */
  async isCheckinOnDate(habitId: string, date: string): Promise<boolean> {
    const checkins = await this.getAllCheckins();
    const record = checkins.find(c => c.habitId === habitId && c.date === date);
    return record !== undefined && record.isCompleted;
  }

  /** 获取某习惯的打卡日期列表 */
  async getCheckinDates(habitId: string): Promise<string[]> {
    const checkins = await this.getAllCheckins();
    return checkins
      .filter(c => c.habitId === habitId && c.isCompleted)
      .map(c => c.date)
      .sort();
  }

  /** 获取本周打卡天数 */
  async getWeekCheckinCount(habitId: string): Promise<number> {
    const dates = await this.getCheckinDates(habitId);
    const now = new Date();
    const dayOfWeek = now.getDay();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - dayOfWeek);
    weekStart.setHours(0, 0, 0, 0);

    let count = 0;
    for (let i = 0; i < 7; i++) {
      const d = new Date(weekStart);
      d.setDate(weekStart.getDate() + i);
      if (dates.includes(this.formatDate(d))) {
        count++;
      }
    }
    return count;
  }

  /** 格式化日期为 yyyy-MM-dd */
  formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /** 获取今日日期字符串 */
  getToday(): string {
    return this.formatDate(new Date());
  }
}
