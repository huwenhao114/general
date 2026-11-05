"""文件读写技能：受工作区沙盒约束，禁止路径越界。"""
from pathlib import Path

from .base import Skill


def safe_path(ctx: dict, rel) -> Path:
    """把用户给的相对路径限制在工作区内（防 ../ 越界）。"""
    root = Path(ctx["workspace"]).resolve()
    p = (root / str(rel)).resolve()
    if p != root and root not in p.parents:
        raise PermissionError(f"路径越界，已拒绝: {rel}")
    return p


class ReadFileSkill(Skill):
    name = "read_file"
    description = "读取工作区内文本文件（前 8000 字符）"
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "工作区内相对路径"}},
        "required": ["path"],
    }

    def run(self, ctx, args):
        p = safe_path(ctx, args["path"])
        if not p.is_file():
            raise FileNotFoundError(f"文件不存在: {args['path']}")
        return p.read_text(encoding="utf-8", errors="replace")[:8000]


class WriteFileSkill(Skill):
    name = "write_file"
    description = "在工作区内写入/覆盖文本文件（自动创建目录）"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "工作区内相对路径"},
            "content": {"type": "string", "description": "要写入的内容"},
        },
        "required": ["path", "content"],
    }

    def run(self, ctx, args):
        p = safe_path(ctx, args["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(args["content"]), encoding="utf-8")
        return f"已写入 {p}（{len(str(args['content']))} 字符）"


class ListFilesSkill(Skill):
    name = "list_files"
    description = "列出工作区文件（最多两层深度）"
    parameters = {
        "type": "object",
        "properties": {"subdir": {"type": "string", "description": "可选子目录"}},
    }

    def run(self, ctx, args):
        base = safe_path(ctx, args.get("subdir") or ".")
        if not base.is_dir():
            raise NotADirectoryError(f"目录不存在: {base}")
        out = []
        for item in sorted(base.rglob("*")):
            rel = item.relative_to(base)
            if len(rel.parts) > 2 or any(part.startswith(".") for part in rel.parts):
                continue
            out.append(("[D] " if item.is_dir() else "[F] ") + "/".join(rel.parts))
            if len(out) >= 100:
                break
        return "\n".join(out) or "(空目录)"
