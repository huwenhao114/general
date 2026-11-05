import { Habit } from '../models/HabitModel';
import { HabitStorage } from '../services/HabitStorage';
import { router } from '@kit.ArkUI';
import { common } from '@kit.AbilityKit';

const ICON_OPTIONS: string[] = ['🏃', '📚', '🧘', '💧', '✏️', '🌙', '📝', '🌅', '🥗', '💪', '🎯', '🎵'];
const COLOR_OPTIONS: string[] = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#51CF66', '#FFD43B', '#845EF7', '#FF922B'];
const WEEKDAY_LABELS: string[] = ['日', '一', '二', '三', '四', '五', '六'];

interface DetailParams {
  habitId: string;
}

@Entry
@Component
struct Index {
  @State habits: Habit[] = [];
  @State checkedTodayIds: string[] = [];
  @State todayDate: string = '';
  @State todayDisplay: string = '';
  @State weekDay: number = 0;
  @State showDialog: boolean = false;

  @State dialogName: string = '';
  @State dialogIconIndex: number = 0;
  @State dialogColorIndex: number = 1;
  @State dialogDays: boolean[] = [false, true, true, true, true, true, false];

  private storage: HabitStorage = HabitStorage.getInstance();

  async aboutToAppear() {
    await this.storage.init(getContext(this) as common.Context);
    this.todayDate = this.storage.getToday();
    const now = new Date();
    this.todayDisplay = `${now.getMonth() + 1}月${now.getDate()}日`;
    this.weekDay = now.getDay();
    await this.loadData();
  }

  onPageShow() {
    this.loadData();
  }

  async loadData() {
    const habits = await this.storage.getAllHabits();
    this.habits = habits;
    const checkedIds: string[] = [];
    for (const habit of habits) {
      const isChecked = await this.storage.isCheckinOnDate(habit.id, this.todayDate);
      if (isChecked) {
        checkedIds.push(habit.id);
      }
    }
    this.checkedTodayIds = checkedIds;
  }

  isCheckedToday(habitId: string): boolean {
    return this.checkedTodayIds.includes(habitId);
  }

  async onToggleCheckin(habit: Habit) {
    await this.storage.toggleCheckin(habit.id, this.todayDate);
    await this.loadData();
  }

  openDialog() {
    this.dialogName = '';
    this.dialogIconIndex = 0;
    this.dialogColorIndex = 1;
    this.dialogDays = [false, true, true, true, true, true, false];
    this.showDialog = true;
  }

  closeDialog() {
    this.showDialog = false;
  }

  async onConfirmAdd() {
    const name = this.dialogName.trim();
    if (name.length === 0) {
      return;
    }
    const icon = ICON_OPTIONS[this.dialogIconIndex];
    const color = COLOR_OPTIONS[this.dialogColorIndex];
    const targetDays: number[] = [];
    for (let i = 0; i < 7; i++) {
      if (this.dialogDays[i]) {
        targetDays.push(i);
      }
    }
    if (targetDays.length === 0) {
      targetDays.push(1, 2, 3, 4, 5);
    }
    await this.storage.addHabit(name, icon, color, targetDays);
    this.closeDialog();
    await this.loadData();
  }

  toggleDay(index: number) {
    const newDays = [...this.dialogDays];
    newDays[index] = !newDays[index];
    this.dialogDays = newDays;
  }

  getCompletedCount(): number {
    return this.checkedTodayIds.length;
  }

  getTodayTargetCount(): number {
    let count = 0;
    for (const habit of this.habits) {
      if (habit.targetDays.includes(this.weekDay)) {
        count++;
      }
    }
    return count;
  }

  getProgressPercent(): number {
    const total = this.getTodayTargetCount();
    if (total === 0) {
      return 0;
    }
    return Math.round((this.getCompletedCount() / total) * 100);
  }

  navigateToDetail(habitId: string) {
    router.pushUrl({
      url: 'pages/HabitDetailPage',
      params: { habitId: habitId } as DetailParams
    });
  }

  build() {
    Stack() {
      Column() {
        this.TopBar()
        if (this.habits.length > 0) {
          this.TodaySummary()
        }
        if (this.habits.length === 0) {
          this.EmptyView()
        } else {
          this.HabitListView()
        }
      }
      .width('100%')
      .height('100%')

      this.FloatingButton()

      if (this.showDialog) {
        this.DialogOverlay()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor($r('app.color.page_background'))
  }

  @Builder
  TopBar() {
    Row() {
      Text('习惯打卡')
        .fontSize(26)
        .fontWeight(FontWeight.Bold)
        .fontColor($r('app.color.title_text'))
        .layoutWeight(1)

      Text(this.todayDisplay)
        .fontSize(14)
        .fontColor($r('app.color.secondary_text'))
    }
    .width('100%')
    .padding({ left: 20, right: 20, top: 16, bottom: 12 })
  }

  @Builder
  TodaySummary() {
    Column() {
      Row() {
        Text('今日打卡')
          .fontSize(14)
          .fontColor($r('app.color.secondary_text'))
        Blank()
        Text(`${this.getCompletedCount()}/${this.getTodayTargetCount()}`)
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor($r('app.color.accent'))
      }
      .width('100%')

      Stack({ alignContent: Alignment.Start }) {
        Column()
          .width('100%')
          .height(8)
          .borderRadius(4)
          .backgroundColor($r('app.color.progress_track'))

        Column()
          .width(`${this.getProgressPercent()}%`)
          .height(8)
          .borderRadius(4)
          .backgroundColor($r('app.color.accent'))
      }
      .width('100%')
      .margin({ top: 10 })
    }
    .width('100%')
    .padding({ left: 20, right: 20, bottom: 12 })
  }

  @Builder
  HabitListView() {
    List({ space: 12 }) {
      ForEach(this.habits, (habit: Habit) => {
        ListItem() {
          this.HabitCard(habit)
        }
      }, (habit: Habit) => `${habit.id}_${this.isCheckedToday(habit.id)}`)
    }
    .width('100%')
    .layoutWeight(1)
    .padding({ left: 16, right: 16, bottom: 80, top: 4 })
    .scrollBar(BarState.Off)
  }

  @Builder
  HabitCard(habit: Habit) {
    Row() {
      Text(habit.icon)
        .fontSize(28)
        .width(48)
        .height(48)
        .textAlign(TextAlign.Center)
        .borderRadius(24)
        .backgroundColor('#1A' + habit.color.substring(1))

      Column() {
        Text(habit.name)
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor($r('app.color.title_text'))
          .maxLines(1)
          .textOverflow({ overflow: TextOverflow.Ellipsis })

        Row() {
          Text(`🔥 ${habit.streakCount}`)
            .fontSize(12)
            .fontColor($r('app.color.secondary_text'))
          Text(`· 累计${habit.totalCount}天`)
            .fontSize(12)
            .fontColor($r('app.color.secondary_text'))
            .margin({ left: 6 })
        }
        .margin({ top: 4 })
      }
      .alignItems(HorizontalAlign.Start)
      .margin({ left: 12 })
      .layoutWeight(1)

      Button() {
        if (this.isCheckedToday(habit.id)) {
          Text('✓')
            .fontSize(22)
            .fontColor(Color.White)
        } else {
          Text('打卡')
            .fontSize(14)
            .fontColor(habit.color)
        }
      }
      .width(this.isCheckedToday(habit.id) ? 48 : 60)
      .height(this.isCheckedToday(habit.id) ? 48 : 36)
      .borderRadius(this.isCheckedToday(habit.id) ? 24 : 18)
      .backgroundColor(this.isCheckedToday(habit.id) ? habit.color : Color.Transparent)
      .border({
        width: this.isCheckedToday(habit.id) ? 0 : 1.5,
        color: habit.color
      })
      .hitTestBehavior(HitTestMode.Block)
      .onClick(() => {
        this.onToggleCheckin(habit)
      })
    }
    .width('100%')
    .padding(16)
    .backgroundColor($r('app.color.card_background'))
    .borderRadius(16)
    .onClick(() => {
      this.navigateToDetail(habit.id)
    })
  }

  @Builder
  EmptyView() {
    Column() {
      Text('🎯')
        .fontSize(72)
      Text('还没有习惯')
        .fontSize(18)
        .fontWeight(FontWeight.Medium)
        .fontColor($r('app.color.title_text'))
        .margin({ top: 20 })
      Text('点击右下角加号\n添加第一个习惯')
        .fontSize(14)
        .fontColor($r('app.color.secondary_text'))
        .margin({ top: 8 })
        .textAlign(TextAlign.Center)
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
  }

  @Builder
  FloatingButton() {
    Button() {
      Text('+')
        .fontSize(32)
        .fontColor(Color.White)
    }
    .width(56)
    .height(56)
    .borderRadius(28)
    .backgroundColor($r('app.color.accent'))
    .shadow(ShadowStyle.OUTER_DEFAULT_MD)
    .position({ right: 20, bottom: 20 })
    .onClick(() => {
      this.openDialog()
    })
  }

  @Builder
  DialogOverlay() {
    Stack() {
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#80000000')
        .onClick(() => {
          this.closeDialog()
        })

      Column() {
        Text('添加习惯')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor($r('app.color.title_text'))
          .width('100%')
          .textAlign(TextAlign.Center)

        TextInput({ text: this.dialogName, placeholder: '输入习惯名称' })
          .fontSize(16)
          .height(48)
          .borderRadius(12)
          .backgroundColor($r('app.color.page_background'))
          .margin({ top: 20 })
          .onChange((value: string) => {
            this.dialogName = value
          })

        Text('选择图标')
          .fontSize(14)
          .fontColor($r('app.color.secondary_text'))
          .width('100%')
          .margin({ top: 20 })

        this.IconSelector()

        Text('选择颜色')
          .fontSize(14)
          .fontColor($r('app.color.secondary_text'))
          .width('100%')
          .margin({ top: 16 })

        this.ColorSelector()

        Text('目标天数')
          .fontSize(14)
          .fontColor($r('app.color.secondary_text'))
          .width('100%')
          .margin({ top: 16 })

        this.WeekdaySelector()

        Row() {
          Button('取消')
            .fontSize(16)
            .fontColor($r('app.color.secondary_text'))
            .layoutWeight(1)
            .height(44)
            .borderRadius(12)
            .backgroundColor($r('app.color.page_background'))
            .onClick(() => {
              this.closeDialog()
            })

          Button('确认')
            .fontSize(16)
            .fontColor(Color.White)
            .layoutWeight(1)
            .height(44)
            .borderRadius(12)
            .backgroundColor($r('app.color.accent'))
            .margin({ left: 12 })
            .onClick(() => {
              this.onConfirmAdd()
            })
        }
        .width('100%')
        .margin({ top: 24 })
      }
      .width('85%')
      .padding(24)
      .borderRadius(20)
      .backgroundColor($r('app.color.card_background'))
    }
    .width('100%')
    .height('100%')
    .alignContent(Alignment.Center)
  }

  @Builder
  IconSelector() {
    Flex({ wrap: FlexWrap.Wrap }) {
      ForEach(ICON_OPTIONS, (icon: string, index: number) => {
        Text(icon)
          .fontSize(24)
          .width(44)
          .height(44)
          .textAlign(TextAlign.Center)
          .borderRadius(12)
          .backgroundColor(this.dialogIconIndex === index ? '#1A007DFF' : $r('app.color.page_background'))
          .border({
            width: this.dialogIconIndex === index ? 2 : 0,
            color: $r('app.color.accent')
          })
          .margin({ right: 8, top: 8 })
          .onClick(() => {
            this.dialogIconIndex = index
          })
      }, (icon: string, index: number) => `${icon}_${index}`)
    }
    .width('100%')
    .margin({ top: 4 })
  }

  @Builder
  ColorSelector() {
    Flex({ wrap: FlexWrap.Wrap }) {
      ForEach(COLOR_OPTIONS, (color: string, index: number) => {
        Stack() {
          if (this.dialogColorIndex === index) {
            Text('✓')
              .fontSize(16)
              .fontColor(Color.White)
          }
        }
        .width(36)
        .height(36)
        .borderRadius(18)
        .backgroundColor(color)
        .margin({ right: 8, top: 8 })
        .onClick(() => {
          this.dialogColorIndex = index
        })
      }, (color: string, index: number) => `${color}_${index}`)
    }
    .width('100%')
    .margin({ top: 4 })
  }

  @Builder
  WeekdaySelector() {
    Row() {
      ForEach([1, 2, 3, 4, 5, 6, 0], (dayIndex: number) => {
        Text(WEEKDAY_LABELS[dayIndex])
          .fontSize(14)
          .width(36)
          .height(36)
          .textAlign(TextAlign.Center)
          .borderRadius(18)
          .backgroundColor(this.dialogDays[dayIndex] ? $r('app.color.accent') : $r('app.color.page_background'))
          .fontColor(this.dialogDays[dayIndex] ? Color.White : $r('app.color.secondary_text'))
          .layoutWeight(1)
          .margin({ left: 4 })
          .onClick(() => {
            this.toggleDay(dayIndex)
          })
      }, (dayIndex: number) => `day_${dayIndex}`)
    }
    .width('100%')
    .margin({ top: 4 })
  }
}
