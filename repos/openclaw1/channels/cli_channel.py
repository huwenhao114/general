"""CLI 渠道：交互式命令行对话（复刻 OpenClaw 的 channel 抽象）。"""


HELP = """命令：
  /help            显示本帮助
  /new             清空当前会话记忆
  /agents          列出可用 agent
  /use @名字       切换默认 agent（也可直接用 @名字 消息前缀）
  /status          查看网关状态
  /quit            退出
"""


def run_cli(gateway, session_id: str = "cli"):
    print("🦞 OpenLobster CLI（/help 查看命令，Ctrl+C 退出）")
    status = gateway.status()
    for name, info in status["agents"].items():
        tag = f"  {name}（{info['title']}） <- {info['provider']}"
        print(tag + (f"  {info['degraded']}" if info["degraded"] else ""))
    current = None
    while True:
        try:
            line = input("\n你> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见 🦞")
            return
        if not line:
            continue
        if line.startswith("/"):
            cmd = line.split()[0].lower()
            if cmd == "/quit":
                print("再见 🦞")
                return
            if cmd == "/help":
                print(HELP)
            elif cmd == "/new":
                gateway.reset(session_id)
                print("（会话已清空）")
            elif cmd == "/agents":
                for n, info in status["agents"].items():
                    print(f"  @{n}  {info['title']} <- {info['provider']}")
            elif cmd == "/status":
                for k, v in status.items():
                    print(f"  {k}: {v}")
            elif cmd == "/use":
                name = line.split()[1].lstrip("@") if len(line.split()) > 1 else ""
                if name in gateway.agents:
                    session_id = f"cli:{name}"
                    print(f"（默认 agent 切换为 @{name}）")
                else:
                    print(f"（没有叫 @{name} 的 agent）")
            else:
                print("（未知命令，/help 查看帮助）")
            continue
        try:
            reply, agent_name = gateway.handle(session_id, line)
            print(f"\n🦞 @{agent_name}> {reply}")
        except Exception as e:  # noqa: BLE001 渠道层兜底，不让单条消息崩掉会话
            print(f"\n[错误] {e}")
