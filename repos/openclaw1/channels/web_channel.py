"""WebChat 渠道：标准库 http.server 实现的网页聊天界面（零依赖）。"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🦞 OpenLobster WebChat</title>
<style>
:root{--bg:#0b0e0c;--surface:#151b17;--line:#26302a;--text:#e8f0ea;--muted:#94a39a;--green:#4ade80;--purple:#a78bfa}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:radial-gradient(900px 400px at 80% -10%,rgba(124,58,237,.14),transparent 60%),radial-gradient(800px 400px at 0% -10%,rgba(74,222,128,.12),transparent 55%),var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column}
header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px}
header h1{font-size:16px;font-weight:800}
header select{margin-left:auto;background:var(--surface);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:6px 10px}
#chat{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:78%;padding:10px 14px;border-radius:14px;line-height:1.6;white-space:pre-wrap;word-break:break-word;font-size:14px}
.user{align-self:flex-end;background:#1f3a2c;border:1px solid rgba(74,222,128,.3)}
.bot{align-self:flex-start;background:var(--surface);border:1px solid var(--line)}
.bot .who{font-size:11px;color:var(--purple);margin-bottom:4px}
.err{align-self:center;color:#fca5a5;font-size:13px}
footer{display:flex;gap:10px;padding:14px 20px;border-top:1px solid var(--line)}
footer input{flex:1;background:var(--surface);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:12px 14px;font-size:14px;outline:none}
footer input:focus{border-color:rgba(167,139,250,.6)}
footer button{background:var(--green);color:#07100a;border:none;border-radius:10px;padding:0 22px;font-weight:700;font-size:14px;cursor:pointer}
footer button:disabled{opacity:.5}
</style>
</head>
<body>
<header><h1>🦞 OpenLobster</h1><select id="agent"></select></header>
<div id="chat"><div class="msg bot">你好，我是运行在你本机的 OpenLobster 助手。输入 /new 可清空会话。</div></div>
<footer>
  <input id="input" placeholder="发消息…（@coder 前缀可指定 agent，/new 清空会话）" autocomplete="off">
  <button id="send">发送</button>
</footer>
<script>
const chat=document.getElementById('chat'),input=document.getElementById('input'),btn=document.getElementById('send'),sel=document.getElementById('agent');
const sid=(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random());
fetch('/api/agents').then(r=>r.json()).then(a=>{sel.innerHTML=a.map(x=>`<option value="${x.name}">${x.name} · ${x.title}</option>`).join('')});
function add(cls,text,who){const d=document.createElement('div');d.className='msg '+cls;d.innerHTML=(who?`<div class="who">${who}</div>`:'')+text.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));chat.appendChild(d);chat.scrollTop=chat.scrollHeight;return d}
async function send(){
  const text=input.value.trim();if(!text)return;
  if(text==='/new'){await fetch('/api/reset',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid})});add('bot','（会话已清空）');input.value='';return}
  add('user',text);input.value='';btn.disabled=true;
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,message:text,agent:sel.value})});
    const d=await r.json();
    if(d.error)add('err','[错误] '+d.error);else add('bot',d.reply,'🦞 @'+d.agent);
  }catch(e){add('err','请求失败：'+e)}
  btn.disabled=false;input.focus();
}
btn.onclick=send;input.addEventListener('keydown',e=>{if(e.key==='Enter')send()});input.focus();
</script>
</body>
</html>"""


def make_handler(gateway):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                return json.loads(raw.decode("utf-8"))
            except ValueError:
                return {}

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, _PAGE, "text/html; charset=utf-8")
            elif self.path == "/api/agents":
                agents = [{"name": n, "title": a.title}
                          for n, a in gateway.agents.items()]
                self._send(200, json.dumps(agents, ensure_ascii=False))
            elif self.path == "/api/status":
                self._send(200, json.dumps(gateway.status(), ensure_ascii=False))
            else:
                self._send(404, '{"error":"not found"}')

        def do_POST(self):
            body = self._body()
            session_id = str(body.get("session_id") or "web")
            if self.path == "/api/chat":
                text = str(body.get("message", "")).strip()
                if not text:
                    self._send(400, '{"error":"message 不能为空"}')
                    return
                agent_name = body.get("agent")
                if agent_name in gateway.agents and not text.startswith("@"):
                    text = f"@{agent_name} {text}"
                try:
                    reply, who = gateway.handle(session_id, text)
                    self._send(200, json.dumps(
                        {"reply": reply, "agent": who}, ensure_ascii=False))
                except Exception as e:  # noqa: BLE001
                    self._send(500, json.dumps(
                        {"error": str(e)}, ensure_ascii=False))
            elif self.path == "/api/reset":
                gateway.reset(session_id)
                self._send(200, '{"ok":true}')
            else:
                self._send(404, '{"error":"not found"}')

        def log_message(self, fmt, *args):  # 安静模式
            pass

    return Handler


def run_web(gateway, host="127.0.0.1", port=8787):
    server = ThreadingHTTPServer((host, port), make_handler(gateway))
    lock = threading.Lock()  # 会话写入由 Gateway 内部字典+文件保证；此锁预留扩展
    print(f"🦞 OpenLobster WebChat -> http://{host}:{port}  （Ctrl+C 停止）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        server.server_close()
