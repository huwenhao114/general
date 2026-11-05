"""记忆技能：把长期记忆以工具形式暴露给模型。"""
from .base import Skill


class RememberSkill(Skill):
    name = "remember"
    description = "把一条重要事实写入长期记忆（memory/*.md），跨会话可检索"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "要记住的内容"},
            "topic": {"type": "string", "description": "可选主题，用于归类文件名"},
        },
        "required": ["text"],
    }

    def run(self, ctx, args):
        path = ctx["memory"].remember(args["text"], args.get("topic"))
        return f"已记住（{path}）"


class RecallSkill(Skill):
    name = "recall"
    description = "检索长期记忆，返回最近的相关条目"
    parameters = {
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "过滤关键词，留空返回最近记录"},
            "limit": {"type": "integer", "description": "最多返回条数，默认 20"},
        },
    }

    def run(self, ctx, args):
        hits = ctx["memory"].recall(args.get("keyword"), int(args.get("limit", 20)))
        return "\n".join(hits) if hits else "（记忆中没有匹配内容）"
