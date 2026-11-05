"""Markdown 持久记忆（复刻 OpenClaw 的 SOUL.md / memory/*.md 设计）。

workspace/
├── SOUL.md              # 助手"灵魂文件"：人设与信条，注入 system prompt
├── memory/*.md          # 长期记忆（remember 写入，recall 检索）
└── sessions/*.json      # 各渠道会话历史（Gateway 维护）
"""
import re
import time
from pathlib import Path

DEFAULT_SOUL = """# SOUL

我是运行在 OpenLobster 网关上的助手。

## 信条
- 先理解需求，再动手干活
- 工具返回的结果需要核实后再转述
- 用户数据保存在本机工作区，不上传任何第三方
- 诚实说明自己做不到的事
"""


class WorkspaceMemory:
    def __init__(self, workspace):
        self.root = Path(workspace).resolve()
        self.mem_dir = self.root / "memory"
        self.sessions_dir = self.root / "sessions"
        self.mem_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    # ---------- SOUL ----------
    @property
    def soul_path(self) -> Path:
        return self.root / "SOUL.md"

    def ensure_soul(self, text: str = DEFAULT_SOUL):
        if not self.soul_path.exists():
            self.soul_path.write_text(text, encoding="utf-8")

    def load_soul(self) -> str:
        self.ensure_soul()
        return self.soul_path.read_text(encoding="utf-8")

    # ---------- 长期记忆 ----------
    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r'[\\/:*?"<>|\s]+', "_", name)[:40].strip("_") or "notes"

    def remember(self, text: str, topic: str = None) -> str:
        date = time.strftime("%Y-%m-%d")
        fname = f"{date}_{self._safe_name(topic or 'notes')}.md"
        path = self.mem_dir / fname
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"- {time.strftime('%H:%M:%S')} {text.strip()}\n")
        return str(path)

    def recall(self, keyword: str = None, limit: int = 20):
        hits = []
        for path in sorted(self.mem_dir.glob("*.md"), reverse=True):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                if keyword is None or keyword.lower() in line.lower():
                    hits.append(f"{path.name} | {line.strip()}")
                    if len(hits) >= limit:
                        return hits
        return hits

    # ---------- 会话历史 ----------
    def _session_path(self, session_id: str) -> Path:
        safe = self._safe_name(session_id)
        return self.sessions_dir / f"{safe}.json"

    def load_session(self, session_id: str):
        p = self._session_path(session_id)
        if not p.exists():
            return []
        try:
            import json
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("messages", [])
        except (ValueError, OSError):
            return []

    def save_session(self, session_id: str, messages, keep_last: int = 40):
        import json
        p = self._session_path(session_id)
        data = {"session_id": session_id, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "messages": messages[-keep_last:]}
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def clear_session(self, session_id: str):
        p = self._session_path(session_id)
        if p.exists():
            p.unlink()
