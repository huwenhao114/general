import { common } from '@kit.AbilityKit';
import { promptAction } from '@kit.ArkUI';
import { DataStore, ExamInfo, ReviewPlan } from '../model/DataStore';

@Entry
@Component
struct Index {
  @State exam: ExamInfo | null = null;
  @State plans: ReviewPlan[] = [];
  @State days: number = 0;
  @State hours: number = 0;
  @State minutes: number = 0;
  @State seconds: number = 0;
  @State dialogMode: number = 0; // 0=none, 1=exam, 2=plan
  @State editingPlanId: string = '';

  // 弹窗临时状态
  @State tempName: string = '';
  @State tempExamDate: string = '';
  @State tempContent: string = '';
  @State tempPlanDate: string = '';
  @State tempDuration: number = 60;
  @State tempNote: string = '';

  private store: DataStore = DataStore.getInstance();
  private timerId: number = -1;

  async aboutToAppear() {
    const ctx = this.getUIContext().getHostContext() as common.Context;
    await this.store.init(ctx);
    await this.loadData();
    this.updateCountdown();
    this.timerId = setInterval(() => {
      this.updateCountdown();
    }, 1000);
  }

  aboutToDisappear() {
    if (this.timerId !== -1) {
      clearInterval(this.timerId);
      this.timerId = -1;
    }
  }

  async loadData() {
    this.exam = await this.store.getExam();
    this.plans = await this.store.getPlans();
    this.plans.sort((a: ReviewPlan, b: ReviewPlan) => a.timestamp - b.timestamp);
  }

  updateCountdown() {
    if (!this.exam) {
      this.days = 0;
      this.hours = 0;
      this.minutes = 0;
      this.seconds = 0;
      return;
    }
    const now = Date.now();
    const diff = this.exam.timestamp - now;
    if (diff <= 0) {
      this.days = 0;
      this.hours = 0;
      this.minutes = 0;
      this.seconds = 0;
      return;
    }
    this.days = Math.floor(diff / (1000 * 60 * 60 * 24));
    this.hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    this.minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    this.seconds = Math.floor((diff % (1000 * 60)) / 1000);
  }

  openExamDialog() {
    if (this.exam) {
      this.tempName = this.exam.name;
      this.tempExamDate = this.formatDateForInput(this.exam.timestamp);
    } else {
      this.tempName = '';
      const future = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
      this.tempExamDate = this.formatDateForInput(future.getTime());
    }
    this.dialogMode = 1;
  }

  openPlanDialog() {
    this.editingPlanId = '';
    this.tempContent = '';
    this.tempPlanDate = this.formatDateForInput(Date.now());
    this.tempDuration = 60;
    this.tempNote = '';
    this.dialogMode = 2;
  }

  openEditPlanDialog(plan: ReviewPlan) {
    this.editingPlanId = plan.id;
    this.tempContent = plan.content;
    this.tempPlanDate = this.formatDateForInput(plan.timestamp);
    this.tempDuration = plan.duration;
    this.tempNote = plan.note;
    this.dialogMode = 2;
  }

  async saveExam() {
    if (this.tempName.trim().length === 0) {
      promptAction.showToast({ message: '请输入考试名称' });
      return;
    }
    const ts = this.parseInputDate(this.tempExamDate);
    if (isNaN(ts)) {
      promptAction.showToast({ message: '请输入正确的日期 (YYYY-MM-DD)' });
      return;
    }
    this.exam = { name: this.tempName.trim(), timestamp: ts };
    await this.store.saveExam(this.exam);
    this.updateCountdown();
    this.dialogMode = 0;
    promptAction.showToast({ message: '考试已保存' });
  }

  async savePlan() {
    if (this.tempContent.trim().length === 0) {
      promptAction.showToast({ message: '请输入复习内容' });
      return;
    }
    const ts = this.parseInputDate(this.tempPlanDate);
    if (isNaN(ts)) {
      promptAction.showToast({ message: '请输入正确的日期 (YYYY-MM-DD)' });
      return;
    }
    if (this.editingPlanId.length > 0) {
      this.plans = this.plans.map((p: ReviewPlan): ReviewPlan => {
        if (p.id === this.editingPlanId) {
          return {
            id: p.id,
            content: this.tempContent.trim(),
            timestamp: ts,
            duration: this.tempDuration,
            completed: p.completed,
            note: this.tempNote.trim()
          };
        }
        return p;
      });
    } else {
      const newPlan: ReviewPlan = {
        id: Date.now().toString() + Math.floor(Math.random() * 100000).toString(),
        content: this.tempContent.trim(),
        timestamp: ts,
        duration: this.tempDuration,
        completed: false,
        note: this.tempNote.trim()
      };
      this.plans.push(newPlan);
    }
    this.plans.sort((a: ReviewPlan, b: ReviewPlan) => a.timestamp - b.timestamp);
    await this.store.savePlans(this.plans);
    this.dialogMode = 0;
    promptAction.showToast({ message: '计划已保存' });
  }

  async togglePlan(plan: ReviewPlan) {
    this.plans = this.plans.map((p: ReviewPlan): ReviewPlan => {
      if (p.id === plan.id) {
        return {
          id: p.id,
          content: p.content,
          timestamp: p.timestamp,
          duration: p.duration,
          completed: !p.completed,
          note: p.note
        };
      }
      return p;
    });
    await this.store.savePlans(this.plans);
  }

  async deletePlan(plan: ReviewPlan) {
    this.plans = this.plans.filter((p: ReviewPlan) => p.id !== plan.id);
    await this.store.savePlans(this.plans);
    promptAction.showToast({ message: '已删除' });
  }

  formatDateForInput(ts: number): string {
    const d = new Date(ts);
    const y = d.getFullYear();
    const m = (d.getMonth() + 1).toString().padStart(2, '0');
    const day = d.getDate().toString().padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  parseInputDate(s: string): number {
    const parts = s.split('-');
    if (parts.length !== 3) {
      return NaN;
    }
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10) - 1;
    const d = parseInt(parts[2], 10);
    if (isNaN(y) || isNaN(m) || isNaN(d)) {
      return NaN;
    }
    const date = new Date(y, m, d, 23, 59, 59);
    return date.getTime();
  }

  formatDate(ts: number): string {
    const d = new Date(ts);
    const y = d.getFullYear();
    const m = (d.getMonth() + 1).toString().padStart(2, '0');
    const day = d.getDate().toString().padStart(2, '0');
    const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()];
    return `${y}-${m}-${day} 周${week}`;
  }

  getProgress(): number {
    if (this.plans.length === 0) {
      return 0;
    }
    const completed = this.plans.filter((p: ReviewPlan) => p.completed).length;
    return Math.round((completed / this.plans.length) * 100);
  }

  build() {
    Stack() {
      Column() {
        // 顶部倒计时卡片
        this.buildCountdownCard()
        // 计划列表
        this.buildPlanList()
      }
      .width('100%')
      .height('100%')
      .alignItems(HorizontalAlign.Center)

      // 底部按钮
      Row() {
        Button('设置考试')
          .fontSize(16)
          .fontColor('#FFFFFF')
          .backgroundColor('#FF6B6B')
          .borderRadius(24)
          .height(48)
          .layoutWeight(1)
          .margin({ right: 8 })
          .onClick(() => this.openExamDialog())
        Button('添加计划')
          .fontSize(16)
          .fontColor('#FFFFFF')
          .backgroundColor('#4ECDC4')
          .borderRadius(24)
          .height(48)
          .layoutWeight(1)
          .margin({ left: 8 })
          .onClick(() => this.openPlanDialog())
      }
      .width('92%')
      .position({ bottom: 16 })

      // 弹窗
      if (this.dialogMode === 1) {
        this.buildExamDialog()
      }
      if (this.dialogMode === 2) {
        this.buildPlanDialog()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F6FA')
  }

  @Builder
  buildCountdownCard() {
    Column() {
      if (this.exam) {
        Text(this.exam.name)
          .fontSize(20)
          .fontColor('#FFFFFF')
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 8 })

        Text('距离考试还有')
          .fontSize(14)
          .fontColor('rgba(255,255,255,0.85)')
          .margin({ bottom: 12 })

        Row() {
          Column() {
            Text(this.days.toString())
              .fontSize(36)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold)
            Text('天')
              .fontSize(12)
              .fontColor('rgba(255,255,255,0.85)')
          }
          .layoutWeight(1)

          Column() {
            Text(this.hours.toString().padStart(2, '0'))
              .fontSize(28)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold)
            Text('时')
              .fontSize(12)
              .fontColor('rgba(255,255,255,0.85)')
          }
          .layoutWeight(1)

          Column() {
            Text(this.minutes.toString().padStart(2, '0'))
              .fontSize(28)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold)
            Text('分')
              .fontSize(12)
              .fontColor('rgba(255,255,255,0.85)')
          }
          .layoutWeight(1)

          Column() {
            Text(this.seconds.toString().padStart(2, '0'))
              .fontSize(28)
              .fontColor('#FFFFFF')
              .fontWeight(FontWeight.Bold)
            Text('秒')
              .fontSize(12)
              .fontColor('rgba(255,255,255,0.85)')
          }
          .layoutWeight(1)
        }
        .width('100%')
        .margin({ bottom: 12 })

        Text(`考试日期: ${this.formatDate(this.exam.timestamp)}`)
          .fontSize(13)
          .fontColor('rgba(255,255,255,0.85)')

        // 进度条
        Row() {
          Text(`复习进度 ${this.getProgress()}%`)
            .fontSize(12)
            .fontColor('rgba(255,255,255,0.85)')
            .layoutWeight(1)
          Text(`${this.plans.filter((p: ReviewPlan) => p.completed).length}/${this.plans.length}`)
            .fontSize(12)
            .fontColor('rgba(255,255,255,0.85)')
        }
        .width('100%')
        .margin({ top: 16, bottom: 6 })

        // 进度条背景
        Stack({ alignContent: Alignment.Start }) {
          Column()
            .width('100%')
            .height(8)
            .backgroundColor('rgba(255,255,255,0.25)')
            .borderRadius(4)
          Column()
            .width(`${this.getProgress()}%`)
            .height(8)
            .backgroundColor('#FFFFFF')
            .borderRadius(4)
        }
        .width('100%')
        .height(8)
      } else {
        Text('暂未设置考试')
          .fontSize(18)
          .fontColor('#FFFFFF')
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 8 })
        Text('点击下方按钮设置考试信息')
          .fontSize(13)
          .fontColor('rgba(255,255,255,0.85)')
      }
    }
    .width('92%')
    .padding(20)
    .margin({ top: 16, bottom: 12 })
    .borderRadius(20)
    .linearGradient({
      angle: 135,
      colors: [['#FF6B6B', 0], ['#FF8E53', 1]]
    })
    .alignItems(HorizontalAlign.Center)
  }

  @Builder
  buildPlanList() {
    Column() {
      Row() {
        Text('复习计划')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .layoutWeight(1)
        Text(`共 ${this.plans.length} 项`)
          .fontSize(13)
          .fontColor('#999999')
      }
      .width('100%')
      .margin({ bottom: 10 })

      if (this.plans.length === 0) {
        Column() {
          Text('暂无复习计划')
            .fontSize(15)
            .fontColor('#999999')
            .margin({ top: 40, bottom: 8 })
          Text('点击下方按钮添加复习计划')
            .fontSize(12)
            .fontColor('#BBBBBB')
        }
        .width('100%')
        .alignItems(HorizontalAlign.Center)
      } else {
        Scroll() {
          Column() {
            ForEach(this.plans, (plan: ReviewPlan) => {
              this.buildPlanItem(plan)
            })
          }
          .width('100%')
        }
        .layoutWeight(1)
        .scrollBar(BarState.Off)
        .align(Alignment.Top)
      }
    }
    .width('92%')
    .layoutWeight(1)
    .margin({ bottom: 80 })
  }

  @Builder
  buildPlanItem(plan: ReviewPlan) {
    Row() {
      // 完成状态圆形
      Stack() {
        if (plan.completed) {
          Text('✓')
            .fontSize(16)
            .fontColor('#FFFFFF')
            .fontWeight(FontWeight.Bold)
        }
      }
      .width(28)
      .height(28)
      .borderRadius(14)
      .backgroundColor(plan.completed ? '#4ECDC4' : '#EEEEEE')
      .border({ width: 1, color: plan.completed ? '#4ECDC4' : '#CCCCCC' })
      .onClick(() => this.togglePlan(plan))
      .margin({ right: 12 })

      Column() {
        Row() {
          Text(plan.content)
            .fontSize(16)
            .fontWeight(FontWeight.Medium)
            .fontColor(plan.completed ? '#AAAAAA' : '#333333')
            .decoration({
              type: plan.completed ? TextDecorationType.LineThrough : TextDecorationType.None
            })
            .layoutWeight(1)
          Text(`${plan.duration}分钟`)
            .fontSize(12)
            .fontColor('#FF6B6B')
            .backgroundColor('rgba(255,107,107,0.1)')
            .padding({ left: 8, right: 8, top: 4, bottom: 4 })
            .borderRadius(8)
        }
        .width('100%')

        Row() {
          Text(this.formatDate(plan.timestamp))
            .fontSize(12)
            .fontColor('#999999')
            .layoutWeight(1)
          if (plan.note.length > 0) {
            Text(plan.note)
              .fontSize(12)
              .fontColor('#888888')
              .maxLines(1)
              .textOverflow({ overflow: TextOverflow.Ellipsis })
              .layoutWeight(1)
          }
        }
        .width('100%')
        .margin({ top: 6 })
      }
      .layoutWeight(1)
      .alignItems(HorizontalAlign.Start)

      // 操作按钮
      Column() {
        Text('编辑')
          .fontSize(12)
          .fontColor('#4ECDC4')
          .margin({ bottom: 8 })
          .onClick(() => this.openEditPlanDialog(plan))
        Text('删除')
          .fontSize(12)
          .fontColor('#FF6B6B')
          .onClick(() => this.deletePlan(plan))
      }
      .alignItems(HorizontalAlign.Center)
    }
    .width('100%')
    .padding(14)
    .margin({ bottom: 8 })
    .borderRadius(14)
    .backgroundColor('#FFFFFF')
    .alignItems(VerticalAlign.Center)
  }

  @Builder
  buildExamDialog() {
    Stack({ alignContent: Alignment.Center }) {
      // 遮罩
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .onClick(() => { this.dialogMode = 0; })

      // 弹窗内容
      Column() {
        Text('设置考试')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ bottom: 20 })

        Text('考试名称')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 6 })
          .width('100%')
        TextInput({ text: this.tempName, placeholder: '请输入考试名称' })
          .fontSize(15)
          .height(44)
          .borderRadius(10)
          .backgroundColor('#F5F5F5')
          .margin({ bottom: 16 })
          .onChange((value: string) => { this.tempName = value; })

        Text('考试日期')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 6 })
          .width('100%')
        TextInput({ text: this.tempExamDate, placeholder: 'YYYY-MM-DD' })
          .fontSize(15)
          .height(44)
          .borderRadius(10)
          .backgroundColor('#F5F5F5')
          .margin({ bottom: 8 })
          .onChange((value: string) => { this.tempExamDate = value; })
        Text('格式: YYYY-MM-DD (如 2026-12-31)')
          .fontSize(11)
          .fontColor('#AAAAAA')
          .margin({ bottom: 20 })

        Row() {
          Button('取消')
            .fontSize(15)
            .fontColor('#666666')
            .backgroundColor('#EEEEEE')
            .borderRadius(22)
            .height(44)
            .layoutWeight(1)
            .margin({ right: 8 })
            .onClick(() => { this.dialogMode = 0; })
          Button('保存')
            .fontSize(15)
            .fontColor('#FFFFFF')
            .backgroundColor('#FF6B6B')
            .borderRadius(22)
            .height(44)
            .layoutWeight(1)
            .margin({ left: 8 })
            .onClick(() => this.saveExam())
        }
        .width('100%')
      }
      .width('80%')
      .padding(24)
      .borderRadius(16)
      .backgroundColor('#FFFFFF')
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .height('100%')
  }

  @Builder
  buildPlanDialog() {
    Stack({ alignContent: Alignment.Center }) {
      // 遮罩
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('rgba(0,0,0,0.5)')
        .onClick(() => { this.dialogMode = 0; })

      // 弹窗内容
      Column() {
        Text(this.editingPlanId.length > 0 ? '编辑计划' : '添加计划')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#333333')
          .margin({ bottom: 20 })

        Text('复习内容')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 6 })
          .width('100%')
        TextInput({ text: this.tempContent, placeholder: '请输入复习内容' })
          .fontSize(15)
          .height(44)
          .borderRadius(10)
          .backgroundColor('#F5F5F5')
          .margin({ bottom: 16 })
          .onChange((value: string) => { this.tempContent = value; })

        Text('复习日期')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 6 })
          .width('100%')
        TextInput({ text: this.tempPlanDate, placeholder: 'YYYY-MM-DD' })
          .fontSize(15)
          .height(44)
          .borderRadius(10)
          .backgroundColor('#F5F5F5')
          .margin({ bottom: 16 })
          .onChange((value: string) => { this.tempPlanDate = value; })

        Text('时长(分钟)')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 6 })
          .width('100%')
        TextInput({ text: this.tempDuration.toString(), placeholder: '60' })
          .fontSize(15)
          .height(44)
          .borderRadius(10)
          .backgroundColor('#F5F5F5')
          .margin({ bottom: 16 })
          .type(InputType.Number)
          .onChange((value: string) => {
            const n = parseInt(value, 10);
            this.tempDuration = isNaN(n) ? 0 : n;
          })

        Text('备注(可选)')
          .fontSize(14)
          .fontColor('#666666')
          .margin({ bottom: 6 })
          .width('100%')
        TextInput({ text: this.tempNote, placeholder: '请输入备注' })
          .fontSize(15)
          .height(44)
          .borderRadius(10)
          .backgroundColor('#F5F5F5')
          .margin({ bottom: 20 })
          .onChange((value: string) => { this.tempNote = value; })

        Row() {
          Button('取消')
            .fontSize(15)
            .fontColor('#666666')
            .backgroundColor('#EEEEEE')
            .borderRadius(22)
            .height(44)
            .layoutWeight(1)
            .margin({ right: 8 })
            .onClick(() => { this.dialogMode = 0; })
          Button('保存')
            .fontSize(15)
            .fontColor('#FFFFFF')
            .backgroundColor('#4ECDC4')
            .borderRadius(22)
            .height(44)
            .layoutWeight(1)
            .margin({ left: 8 })
            .onClick(() => this.savePlan())
        }
        .width('100%')
      }
      .width('85%')
      .padding(24)
      .borderRadius(16)
      .backgroundColor('#FFFFFF')
      .alignItems(HorizontalAlign.Start)
    }
    .width('100%')
    .height('100%')
  }
}
