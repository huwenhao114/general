import { Habit } from '../models/HabitModel';
import { HabitStorage } from '../services/HabitStorage';
import { router, promptAction } from '@kit.ArkUI';
import { common } from '@kit.AbilityKit';

interface DetailParams {
  habitId: string;
}

interface DayInfo {
  date: string;
  dayLabel: string;
  weekLabel: string;
  isChecked: boolean;
}

@Entry
@Component
struct HabitDetailPage {
  @State habit: Habit | null = null;
  @State checkinDates: string[] = [];
  @State weekCount: number = 0;
  @State last7Days: DayInfo[] = [];

  private storage: HabitStorage = HabitStorage.getInstance();
  private habitId: string = '';

  async aboutToAppear() {
    await this.storage.init(getContext(this) as common.Context);
    const params = router.getParams() as DetailParams;
    this.habitId = params?.habitId ?? '';
    await this.loadData();
  }

  onPageShow() {
    this.loadData();
  }

  async loadData() {
    const habits = await this.storage.getAllHabits();
    const habit = habits.find((h: Habit) => h.id === this.habitId);
    if (habit !== undefined) {
      this.habit = habit;
      this.checkinDates = await this.storage.getCheckinDates(this.habitId);
      this.weekCount = await this.storage.getWeekCheckinCount(this.habitId);
      this.computeLast7Days();
    }
  }

  computeLast7Days() {
    const days: DayInfo[] = [];
    const today = new Date();
    const weekLabels: string[] = ['日', '一', '二', '三', '四', '五', '六'];
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      const dateStr = this.storage.formatDate(d);
      days.push({
        date: dateStr,
        dayLabel: String(d.getDate()),
        weekLabel: weekLabels[d.getDay()],
        isChecked: this.checkinDates.includes(dateStr)
      });
    }
    this.last7Days = days;
  }

  async onToggleDay(date: string) {
    await this.storage.toggleCheckin(this.habitId, date);
    await this.loadData();
  }

  async onDelete() {
    promptAction.showDialog({
      title: '删除习惯',
      message: '确定要删除这个习惯吗？所有打卡记录将一并删除。',
      buttons: [
        { text: '取消', color: '#99A2B2' },
        { text: '删除', color: '#FF6B6B' }
      ]
    }).then((result: promptAction.ShowDialogSuccessResponse) => {
      if (result.index === 1) {
        this.doDelete();
      }
    });
  }

  async doDelete() {
    await this.storage.deleteHabit(this.habitId);
    router.back();
  }

  build() {
    Column() {
      this.TopBar()

      if (this.habit !== null) {
        this.DetailContent()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor($r('app.color.page_background'))
  }

  @Builder
  TopBar() {
    Row() {
      Text('←')
        .fontSize(26)
        .fontColor($r('app.color.title_text'))
        .onClick(() => {
          router.back()
        })
      Text(this.habit !== null ? this.habit.name : '')
        .fontSize(20)
        .fontWeight(FontWeight.Bold)
        .fontColor($r('app.color.title_text'))
        .layoutWeight(1)
        .margin({ left: 16 })
        .maxLines(1)
        .textOverflow({ overflow: TextOverflow.Ellipsis })
    }
    .width('100%')
    .padding({ left: 20, right: 20, top: 16, bottom: 12 })
  }

  @Builder
  DetailContent() {
    Scroll() {
      Column() {
        this.HeaderCard()
        this.StatsRow()
        this.Last7DaysCard()
        this.DeleteButton()
      }
      .width('100%')
      .padding({ left: 16, right: 16, bottom: 40 })
    }
    .width('100%')
    .layoutWeight(1)
    .scrollBar(BarState.Off)
  }

  @Builder
  HeaderCard() {
    Row() {
      Text(this.habit!.icon)
        .fontSize(40)
        .width(64)
        .height(64)
        .textAlign(TextAlign.Center)
        .borderRadius(32)
        .backgroundColor('#1A' + this.habit!.color.substring(1))

      Column() {
        Text(this.habit!.name)
          .fontSize(22)
          .fontWeight(FontWeight.Bold)
          .fontColor($r('app.color.title_text'))

        Text(`创建于 ${new Date(this.habit!.createdAt).toLocaleDateString()}`)
          .fontSize(12)
          .fontColor($r('app.color.secondary_text'))
          .margin({ top: 4 })
      }
      .margin({ left: 16 })
      .layoutWeight(1)
    }
    .width('100%')
    .padding(20)
    .backgroundColor($r('app.color.card_background'))
    .borderRadius(16)
    .margin({ top: 8 })
  }

  @Builder
  StatsRow() {
    Row() {
      this.StatItem('连续打卡', `${this.habit!.streakCount}`, '天')
      this.StatItem('累计打卡', `${this.habit!.totalCount}`, '天')
      this.StatItem('本周打卡', `${this.weekCount}`, '天')
    }
    .width('100%')
    .margin({ top: 12 })
  }

  @Builder
  StatItem(label: string, value: string, unit: string) {
    Column() {
      Text(value)
        .fontSize(32)
        .fontWeight(FontWeight.Bold)
        .fontColor(this.habit!.color)
      Text(`${label}(${unit})`)
        .fontSize(12)
        .fontColor($r('app.color.secondary_text'))
        .margin({ top: 4 })
    }
    .layoutWeight(1)
    .padding({ top: 16, bottom: 16 })
    .backgroundColor($r('app.color.card_background'))
    .borderRadius(12)
    .margin({ left: 4, right: 4 })
  }

  @Builder
  Last7DaysCard() {
    Column() {
      Text('最近7天')
        .fontSize(16)
        .fontWeight(FontWeight.Medium)
        .fontColor($r('app.color.title_text'))
        .width('100%')

      Row() {
        ForEach(this.last7Days, (day: DayInfo) => {
          Column() {
            Text(day.weekLabel)
              .fontSize(12)
              .fontColor($r('app.color.secondary_text'))
            Stack() {
              if (day.isChecked) {
                Text('✓')
                  .fontSize(18)
                  .fontColor(Color.White)
              }
            }
            .width(40)
            .height(40)
            .borderRadius(20)
            .backgroundColor(day.isChecked ? this.habit!.color : $r('app.color.page_background'))
            .border({
              width: day.isChecked ? 0 : 1,
              color: $r('app.color.divider')
            })
            .margin({ top: 6 })
            .onClick(() => {
              this.onToggleDay(day.date)
            })
            Text(day.dayLabel)
              .fontSize(12)
              .fontColor($r('app.color.secondary_text'))
              .margin({ top: 6 })
          }
          .layoutWeight(1)
          .alignItems(HorizontalAlign.Center)
        }, (day: DayInfo) => day.date)
      }
      .width('100%')
      .margin({ top: 12 })
    }
    .width('100%')
    .padding(20)
    .backgroundColor($r('app.color.card_background'))
    .borderRadius(16)
    .margin({ top: 12 })
  }

  @Builder
  DeleteButton() {
    Button('删除习惯')
      .fontSize(16)
      .fontColor('#FF6B6B')
      .width('100%')
      .height(48)
      .borderRadius(12)
      .backgroundColor($r('app.color.card_background'))
      .margin({ top: 24 })
      .onClick(() => {
        this.onDelete()
      })
  }
}
