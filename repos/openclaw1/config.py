"""配置加载：JSON 配置 + 环境变量密钥解析。

约定：
- 相对路径一律相对于配置文件所在目录解析；
- 密钥写法 "env:VAR_NAME" 表示从环境变量读取，缺失时该提供商标记为不可用而不是崩溃。
"""
import json
import os
from pathlib import Path

DEFAULTS = {
    "workspace": "./workspace",
    "max_tool_steps": 6,
    "providers": {"mock": {"type": "mock"}},
    "agents": [{"name": "main", "provider": "mock", "title": "主助手", "keywords": []}],
    "skills": {
        "builtin": ["web_search", "fetch_url", "read_file", "write_file",
                    "list_files", "python_exec", "remember", "recall"],
        "external_dir": "./skills_external",
        "shell_exec_enabled": False,
    },
    "channels": {"web_host": "127.0.0.1", "web_port": 8787},
}


class ConfigError(Exception):
    pass


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def resolve_secret(value):
    """解析 "env:NAME" 形式的密钥；返回 None 表示未配置。"""
    if value is None:
        return None
    value = str(value)
    if value.startswith("env:"):
        return os.environ.get(value[4:]) or None
    return value or None


class Config:
    def __init__(self, raw: dict, base_dir: Path):
        self.raw = _deep_merge(DEFAULTS, raw)
        self.base_dir = Path(base_dir).resolve()

    # ---------- 构造 ----------
    @classmethod
    def from_dict(cls, raw: dict, base_dir=None) -> "Config":
        return cls(raw, base_dir or Path.cwd())

    @classmethod
    def load(cls, path=None) -> "Config":
        """按优先级查找配置：显式路径 > ./config.json > ./config.example.json。"""
        candidates = []
        if path:
            candidates.append(Path(path))
        else:
            candidates += [Path("config.json"), Path("config.example.json")]
        for p in candidates:
            if p.is_file():
                try:
                    raw = json.loads(p.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    raise ConfigError(f"配置文件 {p} 不是合法 JSON: {e}")
                return cls(raw, p.resolve().parent)
        return cls({}, Path.cwd())

    # ---------- 常用访问器 ----------
    @property
    def workspace(self) -> Path:
        return (self.base_dir / self.raw["workspace"]).resolve() if not Path(self.raw["workspace"]).is_absolute() \
            else Path(self.raw["workspace"])

    @property
    def external_skill_dir(self) -> Path:
        d = self.raw["skills"]["external_dir"]
        p = Path(d)
        return p if p.is_absolute() else (self.base_dir / d)

    @property
    def max_tool_steps(self) -> int:
        return int(self.raw.get("max_tool_steps", 6))

    def provider_cfg(self, name: str):
        cfg = dict(self.raw["providers"].get(name) or {})
        cfg.setdefault("type", "openai")
        if cfg["type"] == "openai":
            cfg["_api_key"] = resolve_secret(cfg.get("api_key"))
            cfg["_available"] = bool(cfg.get("base_url")) and (
                cfg["_api_key"] is not None or cfg.get("api_key") == ""
            )
        else:
            cfg["_available"] = True
        return cfg
