"""Skill 基类与注册表。"""
import json


class Skill:
    """所有技能的基类：声明式定义 → 自动转成 OpenAI function-calling 规范。"""

    name: str = ""
    description: str = ""
    parameters: dict = {"type": "object", "properties": {}}

    def run(self, ctx: dict, args: dict) -> str:
        raise NotImplementedError

    def to_openai_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class SkillRegistry:
    """技能注册表 + 统一执行入口（ctx 注入工作区/记忆/配置）。"""

    def __init__(self, ctx: dict = None):
        self._skills: dict = {}
        self.ctx = ctx or {}

    def register(self, skill: Skill):
        if not isinstance(skill, Skill) or not skill.name:
            raise ValueError("注册的技能必须是 Skill 子类实例且包含 name")
        self._skills[skill.name] = skill

    def all(self):
        return list(self._skills.values())

    def names(self):
        return list(self._skills.keys())

    def get(self, name: str):
        return self._skills.get(name)

    def run(self, name: str, args: dict) -> str:
        skill = self._skills.get(name)
        if skill is None:
            raise KeyError(f"未知工具: {name}")
        out = skill.run(self.ctx, args or {})
        if isinstance(out, str):
            return out
        return json.dumps(out, ensure_ascii=False)


def load_external_skills(registry: SkillRegistry, directory) -> list:
    """从目录热加载外部技能插件（skills_external/*.py，定义 Skill 子类）。

    返回加载报告列表；单个文件失败不影响其他插件。
    """
    import importlib.util
    from pathlib import Path

    p = Path(directory)
    if not p.is_dir():
        return []
    report = []
    for f in sorted(p.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"ol_ext_{f.stem}", f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # 扫描本模块定义的所有 Skill 子类（按 __module__ 过滤掉 import 进来的基类）
            found = [
                obj for obj in vars(mod).values()
                if isinstance(obj, type) and issubclass(obj, Skill)
                and obj is not Skill and obj.__module__ == mod.__name__
            ]
            if found:
                for cls in found:
                    registry.register(cls())
                report.append(f"{f.name} -> {', '.join(c.name for c in found)}")
            else:
                report.append(f"{f.name} -> 跳过（未定义 Skill 子类）")
        except Exception as e:  # noqa: BLE001 插件隔离：失败不影响主程序
            report.append(f"{f.name} -> 加载失败: {e}")
    return report
