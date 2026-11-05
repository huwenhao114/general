"""模型提供商层：统一 chat(messages, tools) 接口。

- OpenAICompatProvider：任何 OpenAI /chat/completions 兼容服务
  （DeepSeek、Qwen(DashScope 兼容模式)、Kimi、OpenAI、Ollama、vLLM…）
- MockProvider：离线测试用，验证 Gateway/Agent/技能全链路。
"""
import json
import urllib.error
import urllib.request


class ProviderError(Exception):
    pass


class OpenAICompatProvider:
    def __init__(self, name, base_url, model, api_key=None, timeout=120):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, messages, tools=None):
        payload = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            raise ProviderError(f"[{self.name}] HTTP {e.code}: {body}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise ProviderError(f"[{self.name}] 网络错误: {e}") from e
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError) as e:
            raise ProviderError(f"[{self.name}] 响应格式异常: {data}") from e
        return {
            "content": msg.get("content"),
            "tool_calls": msg.get("tool_calls"),
        }


class MockProvider:
    """离线回声模型：支持一次工具调用演示（用户消息包含「记一下」时触发 remember）。"""

    def __init__(self, name="mock", note=""):
        self.name = name
        self.note = note

    def chat(self, messages, tools=None):
        last = messages[-1]
        if last.get("role") == "tool":
            return {"content": f"（{self.note}工具执行完毕）结果已收到：{str(last.get('content'))[:120]}",
                    "tool_calls": None}
        text = str(last.get("content", ""))
        if tools and any(t["function"]["name"] == "remember" for t in tools) and "记一下" in text:
            return {
                "content": None,
                "tool_calls": [{
                    "id": "call_mock_1",
                    "type": "function",
                    "function": {
                        "name": "remember",
                        "arguments": json.dumps({"text": "mock 演示记忆", "topic": "demo"},
                                                ensure_ascii=False),
                    },
                }],
            }
        return {"content": f"[mock{('/' + self.note) if self.note else ''}] 收到：{text}",
                "tool_calls": None}


def build_provider(cfg: dict):
    t = cfg.get("type", "openai")
    if t == "mock":
        return MockProvider(note=cfg.get("note", ""))
    if t == "openai":
        if not cfg.get("base_url"):
            raise ProviderError(f"提供商 {cfg.get('name')} 缺少 base_url")
        return OpenAICompatProvider(
            name=cfg.get("name", "openai"),
            base_url=cfg["base_url"],
            model=cfg.get("model", "gpt-4o-mini"),
            api_key=cfg.get("_api_key"),
        )
    raise ProviderError(f"未知提供商类型: {t}")
