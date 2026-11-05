"""联网技能：网页搜索与正文抓取（标准库实现，无第三方依赖）。"""
import html as html_lib
import re
import urllib.error
import urllib.parse
import urllib.request

from .base import Skill

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OpenLobster/0.1"}


class WebSearchSkill(Skill):
    name = "web_search"
    description = "搜索互联网，返回前 5 条「标题 / 链接 / 摘要」"
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "搜索关键词"}},
        "required": ["query"],
    }

    @staticmethod
    def _clean(s: str) -> str:
        s = re.sub(r"<[^>]+>", "", s)
        return html_lib.unescape(s).strip()

    def run(self, ctx, args):
        q = str(args.get("query", "")).strip()
        if not q:
            raise ValueError("query 不能为空")
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                page = resp.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as e:
            raise ConnectionError(f"搜索请求失败（网络受限？）: {e}") from e

        results = []
        for m in re.finditer(
                r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
            href, title = m.group(1), self._clean(m.group(2))
            # DDG 跳转链接还原真实 URL
            if "uddg=" in href:
                try:
                    real = urllib.parse.parse_qs(
                        urllib.parse.urlparse(href).query).get("uddg", [href])[0]
                except ValueError:
                    real = href
            else:
                real = href
            results.append((title, real))
            if len(results) >= 5:
                break
        if not results:
            raise RuntimeError("搜索结果解析为空（页面结构变化或网络受限）")

        # 摘要与标题按顺序配对
        snippets = [self._clean(s) for s in
                    re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.S)]
        lines = []
        for i, (title, link) in enumerate(results):
            snip = snippets[i] if i < len(snippets) else ""
            lines.append(f"{i + 1}. {title}\n   {link}\n   {snip[:160]}")
        return "\n".join(lines)


class FetchUrlSkill(Skill):
    name = "fetch_url"
    description = "抓取网页，去除标签后返回正文前 4000 字符"
    parameters = {
        "type": "object",
        "properties": {"url": {"type": "string", "description": "http/https 网址"}},
        "required": ["url"],
    }

    def run(self, ctx, args):
        url = str(args.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            raise ValueError("仅支持 http/https 地址")
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read(200_000)
                charset = resp.headers.get_content_charset() or "utf-8"
        except (urllib.error.URLError, TimeoutError) as e:
            raise ConnectionError(f"抓取失败: {e}") from e
        text = raw.decode(charset, "replace")
        text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html_lib.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:4000] or "(页面无正文)"
