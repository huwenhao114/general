import { preferences } from '@kit.ArkData';
import { common } from '@kit.AbilityKit';

/**
 * 考试信息
 */
export interface ExamInfo {
  name: string;
  timestamp: number; // 考试时间戳(毫秒)
}

/**
 * 复习计划项
 */
export interface ReviewPlan {
  id: string;
  timestamp: number; // 计划日期时间戳(毫秒)
  content: string;   // 复习内容
  duration: number;  // 时长(分钟)
  completed: boolean; // 是否完成
  note: string;       // 备注
}

const STORE_NAME = 'exam_review_store';
const KEY_EXAM = 'exam_info';
const KEY_PLANS = 'review_plans';

/**
 * 数据存储单例,使用 Preferences 持久化考试和计划
 */
export class DataStore {
  private static instance: DataStore;
  private prefs: preferences.Preferences | null = null;

  private constructor() {}

  static getInstance(): DataStore {
    if (!DataStore.instance) {
      DataStore.instance = new DataStore();
    }
    return DataStore.instance;
  }

  async init(context: common.Context): Promise<void> {
    this.prefs = await preferences.getPreferences(context, STORE_NAME);
  }

  async getExam(): Promise<ExamInfo | null> {
    if (!this.prefs) {
      return null;
    }
    const str = await this.prefs.get(KEY_EXAM, '');
    if (typeof str !== 'string' || str.length === 0) {
      return null;
    }
    try {
      return JSON.parse(str) as ExamInfo;
    } catch (e) {
      return null;
    }
  }

  async saveExam(exam: ExamInfo): Promise<void> {
    if (!this.prefs) {
      return;
    }
    await this.prefs.put(KEY_EXAM, JSON.stringify(exam));
    await this.prefs.flush();
  }

  async getPlans(): Promise<ReviewPlan[]> {
    if (!this.prefs) {
      return [];
    }
    const str = await this.prefs.get(KEY_PLANS, '');
    if (typeof str !== 'string' || str.length === 0) {
      return [];
    }
    try {
      return JSON.parse(str) as ReviewPlan[];
    } catch (e) {
      return [];
    }
  }

  async savePlans(plans: ReviewPlan[]): Promise<void> {
    if (!this.prefs) {
      return;
    }
    await this.prefs.put(KEY_PLANS, JSON.stringify(plans));
    await this.prefs.flush();
  }
}
