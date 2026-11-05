"""Agent 运行时：ReAct 式「模型 ↔ 工具」迭代循环（复刻 OpenClaw 的 agent harness 思想）。"""
import json


class Agent:
    def __init__(self, name, title, provider, registry, max_steps=6, system_extra=""):
        self.name = name
        self.title = title
        self.provider = provider
        self.registry = registry
        self.max_steps = max(1, int(max_steps))
        self.system_extra = system_extra

    @property
    def tool_specs(self):
        return [s.to_openai_spec() for s in self.registry.all()]

    def system_prompt(self) -> str:
        lines = [
            f"你是 {self.title}（代号 {self.name}），运行在 OpenLobster 本地网关上的 AI 助手。",
            "你可以调用工具来搜索、读写文件、执行代码、记录记忆。",
            "规则：",
            "1. 需要外部信息或操作时先调用工具，不要凭空编造；",
            "2. 工具失败时向用户如实说明，不要静默编造结果；",
            "3. 用用户的语言简洁回答。",
        ]
        if self.system_extra:
            lines.append(self.system_extra)
        return "\n".join(lines)

    def run(self, user_text: str, history: list) -> str:
        messages = [{"role": "system", "content": self.system_prompt()}]
        messages += history
        messages.append({"role": "user", "content": user_text})
        tools = self.tool_specs or None

        for _ in range(self.max_steps):
            msg = self.provider.chat(messages, tools=tools)
            calls = msg.get("tool_calls")
            if calls:
                messages.append({
                    "role": "assistant",
                    "content": msg.get("content") or "",
                    "tool_calls": calls,
                })
                for call in calls:
                    result = self._execute(call)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": result,
                    })
                continue
            return msg.get("content") or "（模型返回为空）"
        return "（已达最大工具调用步数，任务未完成；请把问题拆小后重试。）"

    def _execute(self, call: dict) -> str:
        fn = call.get("function", {})
        name = fn.get("name", "")
        try:
            args = json.loads(fn.get("arguments") or "{}")
            if not isinstance(args, dict):
                raise ValueError("参数必须是 JSON 对象")
        except (ValueError, TypeError) as e:
            return f"工具参数解析失败: {e}"
        try:
            return self.registry.run(name, args)
        except Exception as e:  # noqa: BLE001 工具失败要回传给模型，而不是崩溃
            return f"工具 {name} 执行失败: {e}"
