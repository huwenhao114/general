"""代码执行技能：子进程隔离 + 超时保护（诚实声明：非强安全沙盒）。"""
import subprocess
import sys

from .base import Skill

MAX_OUTPUT = 4000


def _format(proc) -> str:
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    text = out + (f"\n[stderr]\n{err}" if err else "")
    return (text or "(无输出)")[:MAX_OUTPUT]


class PythonExecSkill(Skill):
    name = "python_exec"
    description = ("在工作区沙盒目录中以子进程执行 Python 代码并返回输出。"
                   "有 20 秒超时保护；不要执行破坏性操作。")
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的 Python 代码"},
            "timeout": {"type": "integer", "description": "超时秒数，默认 20"},
        },
        "required": ["code"],
    }

    def run(self, ctx, args):
        code = str(args.get("code", "")).strip()
        if not code:
            raise ValueError("code 不能为空")
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=ctx["workspace"], capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=int(args.get("timeout", 20)),
            )
            return _format(proc)
        except subprocess.TimeoutExpired as e:
            return f"执行超时（>{e.timeout}s），已终止"


class ShellExecSkill(Skill):
    name = "shell_exec"
    description = "执行本机 shell 命令（危险！默认关闭，需配置 shell_exec_enabled=true）"
    parameters = {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "命令行"}},
        "required": ["command"],
    }

    def run(self, ctx, args):
        if not ctx.get("config", {}).get("skills", {}).get("shell_exec_enabled"):
            raise PermissionError("shell_exec 未启用：请在 config 的 skills.shell_exec_enabled 设为 true")
        cmd = str(args.get("command", "")).strip()
        if not cmd:
            raise ValueError("command 不能为空")
        proc = subprocess.run(cmd, shell=True, cwd=ctx["workspace"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=30)
        return _format(proc)
