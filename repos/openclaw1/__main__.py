"""OpenLobster 命令行入口。

用法：
  python -m openlobster chat     # CLI 对话
  python -m openlobster serve    # WebChat 网页
  python -m openlobster doctor   # 自检
可选: --config path/to/config.json
"""
import argparse
import sys


def _load_gateway(config_path):
    from openlobster.config import Config
    from openlobster.gateway import Gateway

    cfg = Config.load(config_path)
    return Gateway(cfg), cfg


def _doctor(config_path):
    from openlobster import __version__

    print(f"🦞 OpenLobster doctor (v{__version__})")
    print(f"  Python   : {sys.version.split()[0]} ({sys.executable})")
    try:
        gw, cfg = _load_gateway(config_path)
    except Exception as e:  # noqa: BLE001
        print(f"  [FAIL] 网关装配失败: {e}")
        return 1
    status = gw.status()
    print(f"  工作区   : {status['workspace']}")
    print("  提供商   :")
    for name, issue in status["provider_issues"].items():
        print(f"    - {name}: 不可用（{issue}）")
    for name in cfg.raw.get("providers", {}):
        if name not in status["provider_issues"]:
            print(f"    - {name}: OK")
    print("  Agent    :")
    for n, info in status["agents"].items():
        print(f"    - @{n}（{info['title']}） <- {info['provider']}"
              + (f"  {info['degraded']}" if info["degraded"] else ""))
    print(f"  内置技能 : {', '.join(status['skills'])}")
    if status["external_report"]:
        print("  外部插件 :")
        for line in status["external_report"]:
            print(f"    - {line}")
    # 工作区可写检查
    try:
        probe = gw.memory.root / ".probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        print("  工作区写入: OK")
    except OSError as e:
        print(f"  [FAIL] 工作区不可写: {e}")
        return 1
    print("自检完成 ✅")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="openlobster", description="🦞 迷你 AI 助手网关")
    parser.add_argument("--config", default=None, help="配置文件路径（默认 ./config.json）")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("chat", help="CLI 对话")
    sub.add_parser("serve", help="WebChat 网页")
    sub.add_parser("doctor", help="自检")
    args = parser.parse_args(argv)

    if args.cmd == "doctor":
        return _doctor(args.config)

    gw, cfg = _load_gateway(args.config)
    if args.cmd == "chat":
        from openlobster.channels import run_cli
        run_cli(gw)
        return 0
    if args.cmd == "serve":
        from openlobster.channels import run_web
        ch = cfg.raw.get("channels", {})
        run_web(gw, ch.get("web_host", "127.0.0.1"), int(ch.get("web_port", 8787)))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
