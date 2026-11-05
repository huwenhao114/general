"""技能包：内置技能注册 + 外部插件加载。"""
from .base import Skill, SkillRegistry, load_external_skills
from .code_exec import PythonExecSkill, ShellExecSkill
from .files import ListFilesSkill, ReadFileSkill, WriteFileSkill
from .memory_skills import RecallSkill, RememberSkill
from .web import FetchUrlSkill, WebSearchSkill

# 内置技能表（config.skills.builtin 按名字启用；python_exec 常开，shell_exec 由配置门控）
BUILTIN = {
    "web_search": WebSearchSkill,
    "fetch_url": FetchUrlSkill,
    "read_file": ReadFileSkill,
    "write_file": WriteFileSkill,
    "list_files": ListFilesSkill,
    "remember": RememberSkill,
    "recall": RecallSkill,
    "python_exec": PythonExecSkill,
    "shell_exec": ShellExecSkill,
}

EXTRA = {}


def build_registry(config) -> SkillRegistry:
    from openlobster.memory import WorkspaceMemory

    mem = WorkspaceMemory(config.workspace)
    registry = SkillRegistry(ctx={
        "workspace": str(mem.root),
        "memory": mem,
        "config": config.raw,
    })
    enabled = set(config.raw["skills"].get("builtin", [])) | {"python_exec"}
    for name in enabled:
        cls = BUILTIN.get(name) or EXTRA.get(name)
        if cls is not None:
            registry.register(cls())
    return registry


__all__ = [
    "Skill", "SkillRegistry", "load_external_skills", "build_registry",
    "BUILTIN", "EXTRA",
]
