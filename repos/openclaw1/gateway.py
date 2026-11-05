"""Gateway：常驻控制平面（复刻 OpenClaw Gateway 思想）。

职责：
- 装配 providers / agents / skills / memory；
- 多 Agent 路由（@名字 显式指定 或 关键词匹配，默认 main）；
- 会话管理（内存缓存 + workspace/sessions/*.json 持久化）。
"""
import time

from .agent import Agent
from .config import Config
from .memory import DEFAULT_SOUL, WorkspaceMemory
from .providers import ProviderError, build_provider
from .skills import build_registry, load_external_skills


class Gateway:
    def __init__(self, config: Config):
        self.config = config
        self.memory = WorkspaceMemory(config.workspace)
        self.memory.ensure_soul(DEFAULT_SOUL)

        # 技能
        self.registry = build_registry(config)
        self.external_report = load_external_skills(
            self.registry, config.external_skill_dir)

        # 提供商（不可用的保留原因，装配 agent 时降级为 mock）
        self.provider_issues = {}
        self.providers = {}
        for name in config.raw.get("providers", {}):
            pcfg = config.provider_cfg(name)
            pcfg["name"] = name
            if pcfg.get("_available") is False:
                self.provider_issues[name] = (
                    "缺少 base_url" if not pcfg.get("base_url") else "API Key 未配置（env 未设置）")
                continue
            try:
                self.providers[name] = build_provider(pcfg)
            except ProviderError as e:
                self.provider_issues[name] = str(e)

        # 多 Agent
        self.agents = {}
        for acfg in config.raw.get("agents", []):
            pname = acfg.get("provider", "mock")
            note = ""
            if pname in self.providers:
                provider = self.providers[pname]
            else:
                reason = self.provider_issues.get(pname, "未定义")
                provider = build_provider({"type": "mock", "note": f"降级:{reason}"})
                note = f"（提供商 {pname} 不可用：{reason}，已降级为 mock）"
            agent = Agent(
                name=acfg.get("name", "main"),
                title=acfg.get("title", "助手"),
                provider=provider,
                registry=self.registry,
                max_steps=config.max_tool_steps,
                system_extra=self.memory.load_soul(),
            )
            agent.degraded_note = note
            agent.keywords = acfg.get("keywords", []) or []
            self.agents[agent.name] = agent

        if "main" not in self.agents:
            self.agents["main"] = Agent("main", "主助手",
                                        build_provider({"type": "mock"}),
                                        self.registry, config.max_tool_steps,
                                        self.memory.load_soul())

        # 会话缓存
        self._sessions = {}

    # ---------- 路由 ----------
    def route(self, text: str):
        """返回 (agent, 清理后的文本)。支持 "@coder xxx" 显式路由与关键词匹配。"""
        t = text.strip()
        if t.startswith("@"):
            parts = t.split(None, 1)
            name = parts[0][1:]
            rest = parts[1] if len(parts) > 1 else ""
            if name in self.agents:
                return self.agents[name], rest
        for agent in self.agents.values():
            for kw in getattr(agent, "keywords", []):
                if kw and kw in t:
                    return agent, t
        return self.agents.get("main", next(iter(self.agents.values()))), t

    # ---------- 会话 ----------
    def session(self, session_id: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = self.memory.load_session(session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str):
        self._sessions.pop(session_id, None)
        self.memory.clear_session(session_id)

    # ---------- 主入口 ----------
    def handle(self, session_id: str, text: str):
        """处理一条用户消息，返回 (回复文本, agent名)。"""
        agent, clean_text = self.route(text)
        history = self.session(session_id)
        reply = agent.run(clean_text, history)
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})
        self.memory.save_session(session_id, history)
        return reply, agent.name

    # ---------- 信息 ----------
    def status(self) -> dict:
        return {
            "agents": {n: {"title": a.title, "provider": a.provider.name,
                           "degraded": a.degraded_note or ""}
                       for n, a in self.agents.items()},
            "skills": self.registry.names(),
            "external_report": self.external_report,
            "provider_issues": self.provider_issues,
            "workspace": str(self.memory.root),
        }


def now_tag() -> str:
    return time.strftime("%Y%m%d-%H%M%S")
