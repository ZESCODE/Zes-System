#!/usr/bin/env python3
"""ZES Dashboard v4 — Real-time System Console
SSE-pushed live updates · Provider heat map · MCP panel · Hook audit log · Terminal
http://localhost:8084
"""

import http.server
import json
import os
import socket
import subprocess
import threading
import time
import urllib.request
import urllib.error
import hashlib
import re
import socketserver
from datetime import datetime, timezone
from urllib.parse import urlparse

# ── Plugin Registry ──────────────────────────────────────────────────
PLUGIN_REGISTRY = {}
if "test-plugin" in PLUGIN_REGISTRY: del PLUGIN_REGISTRY["test-plugin"]
if "unknown" in PLUGIN_REGISTRY: del PLUGIN_REGISTRY["unknown"]
PLUGIN_LOCK = threading.Lock()

HOST = "127.0.0.1"
PORT = 8083
POLL_INTERVAL = 3  # SSE push interval

# ── SSE clients registry ──────────────────────────────────────────────
sse_clients = []
sse_lock = threading.Lock()

def broadcast(event, data):
    msg = f"event: {event}\ndata: {data}\n\n"
    with sse_lock:
        dead = []
        for q in sse_clients:
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for q in dead:
            sse_clients.remove(q)

# ── Helpers ───────────────────────────────────────────────────────────
def tcp_open(host, port, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except Exception:
        return False

def http_code(url, timeout=2):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return r.status
    except Exception as e:
        return getattr(e, "code", None)

def run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout.strip() or r.stderr.strip() or "")[:2000]
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return f"(error: {e})"

def cli_token():
    try:
        d = os.path.expanduser("~/.9router")
        mid = open(d + "/machine-id").read().strip()
        sec = open(d + "/auth/cli-secret").read().strip()
        return hashlib.sha256((mid + "9r-cli-auth" + sec).encode()).hexdigest()[:16]
    except Exception:
        return ""

def r9_providers():
    tok = cli_token()
    if not tok:
        return []
    try:
        req = urllib.request.Request("http://localhost:20128/api/providers",
            headers={"x-9r-cli-token": tok})
        r = urllib.request.urlopen(req, timeout=5)
        return json.loads(r.read()) if r.status == 200 else []
    except Exception:
        return []

# ── Service definitions ───────────────────────────────────────────────
SERVICES = [
    {"id":"codex","name":"Codex App Server","port":5900,"url":"http://127.0.0.1:5900/","icon":"⚡","desc":"AI API Proxy + Zen Gateway"},
    {"id":"ttyd","name":"Web Terminal","port":7173,"url":"http://127.0.0.1:7173/","icon":"🖥","desc":"Browser-based terminal"},
    {"id":"r9","name":"9Router","port":20128,"url":"http://127.0.0.1:20128/","icon":"🌐","desc":"AI Router · 18 providers"},
    {"id":"hermes","name":"Hermes Gateway","bin":"hermes","icon":"🤖","desc":"Claude Sonnet 4.6 · cron · scheduler"},
    {"id":"claude","name":"Claude Code","bin":"claude","icon":"🧠","desc":"Anthropic Claude Code 2.1.207"},
    {"id":"tor","name":"Tor SOCKS5","port":9050,"icon":"🔒","desc":"Anonymizing proxy pool"},
    {"id":"sshd","name":"SSH Server","port":8022,"icon":"🔑","desc":"Remote shell access"},
    {"id":"zeschrome","name":"zesChrome MCP","port":5901,"icon":"🧩","desc":"18 browser + ZES system tools"},
    {"id":"zes-bridge","name":"ZES Bridge MCP","bin":"node", "check":"test","icon":"🔌","desc":"10 system API tools"},
    {"id":"vscode","name":"VS Code Server","port":8000,"url":"http://127.0.0.1:8000/","icon":"💻","desc":"Web VS Code"},
    {"id":"chrome","name":"Chrome CDP","port":9222,"icon":"🌍","desc":"Headless Chromium"},
    {"id":"agent-ui","name":"Agent UI","port":8084,"is_self":True,"url":"http://127.0.0.1:8084/","icon":"🤖","desc":"Agent chat dashboard"},
    {"id":"swarm","name":"ZES Swarm","port":5030,"icon":"🐝","desc":"Multi-agent orchestrator"},
    {"id":"vscode-mobile","name":"VS Code Mobile","port":8001,"url":"http://127.0.0.1:8001/","icon":"📱","desc":"Mobile-optimized VS Code"},
    {"id":"agent-dash","name":"Agent Dashboard API","port":8002,"icon":"📊","desc":"Agent monitoring REST API"},
    {"id":"agent-dash-web","name":"Agent Dashboard Web","port":8003,"url":"http://127.0.0.1:8003/","icon":"📈","desc":"Agent Dashboard frontend"},
    {"id":"composio","name":"Composio CLI","bin":"composio","icon":"📬","desc":"Gmail + 1000+ API integrations"},
]

MCP_SERVERS = [
    {"id":"zeschrome","name":"zesChrome MCP","command":"node","args":["zes-chrome/mcp-server/server.js"],"port":5901,"tools":18},
    {"id":"zes-bridge","name":"ZES Bridge MCP","command":"node","args":["zes-chrome/zes-bridge-mcp/server.js"],"tools":10},
    {"id":"chrome-devtools","name":"Chrome DevTools","command":"npx","args":["-y","chrome-devtools-mcp@latest"],"tools":8},
    {"id":"filesystem","name":"Filesystem MCP","command":"npx","args":["-y","@modelcontextprotocol/server-filesystem"],"tools":5},
    {"id":"memory","name":"Memory MCP","command":"npx","args":["-y","@modelcontextprotocol/server-memory"],"tools":3},
    {"id":"sequential-thinking","name":"Sequential Thinking","command":"npx","args":["-y","@modelcontextprotocol/server-sequential-thinking"],"tools":2},
]

def scan_services():
    results = []
    for s in SERVICES:
        status = "stopped"
        if s.get("check") == "test":
            # ZES Bridge: check if the server file exists and node can run it
            status = "running" if os.path.exists(
                os.path.expanduser("~/Zes-System/zes-chrome/zes-bridge-mcp/server.js")) else "stopped"
        elif "port" in s and s["port"]:
            status = "running" if tcp_open("127.0.0.1", s["port"]) else "stopped"
        elif "bin" in s:
            status = "running" if run(f"which {s['bin']} 2>/dev/null") else "stopped"
        results.append({**s, "status": status, "timestamp": datetime.now(timezone.utc).isoformat()})
    return results

def scan_mcp():
    results = []
    for m in MCP_SERVERS:
        alive = False
        if "port" in m:
            alive = tcp_open("127.0.0.1", m["port"])
        results.append({**m, "alive": alive})
    return results

def get_providers():
    provs = r9_providers()
    if isinstance(provs, list):
        return provs
    if isinstance(provs, dict):
        # 9Router API may return 'connections' or '_providers'
        if "connections" in provs:
            return provs["connections"]
        if "_providers" in provs:
            return provs["_providers"]
    return []

def get_hook_logs():
    """Read recent hook audit events from governance log."""
    logdir = os.path.expanduser("~/.claude/plugins/ecc/logs")
    if not os.path.isdir(logdir):
        # Try governance log path
        logdir = os.path.expanduser("~/.claude/logs")
        if not os.path.isdir(logdir):
            return [{"time": datetime.now(timezone.utc).isoformat(), "event": "Hook monitoring active", "source": "system"}]
    logs = []
    try:
        for f in sorted(os.listdir(logdir), reverse=True)[:5]:
            path = os.path.join(logdir, f)
            with open(path) as fh:
                for line in fh.readlines()[-20:]:
                    logs.append({"time": datetime.now(timezone.utc).isoformat(), "event": line.strip()[:120], "source": f})
    except Exception:
        pass
    return logs or [{"time": datetime.now(timezone.utc).isoformat(), "event": "Hook audit log — monitoring enabled", "source": "system"}]

def get_env_info():
    try:
        uptime = run("uptime -p") or run("cat /proc/uptime | awk '{print int($1/86400)\"d \"int(($1%86400)/3600)\"h\"}'") or "unknown"
        return {
            "hostname": socket.gethostname(),
            "python": run("python3 --version 2>/dev/null"),
            "node": run("node --version 2>/dev/null"),
            "claude": run("claude --version 2>/dev/null"),
            "uptime": uptime,
            "services_total": len(SERVICES),
            "services_running": 0,
        }
    except:
        return {}

# ── SSE poll thread ───────────────────────────────────────────────────
def sse_poll_loop():
    while True:
        services = scan_services()
        mcp = scan_mcp()
        providers = get_providers()
        env = get_env_info()
        env["services_running"] = sum(1 for s in services if s["status"] == "running")
        env["services_total"] = len(services)

        broadcast("services", json.dumps(services))
        broadcast("mcp", json.dumps(mcp))
        broadcast("providers", json.dumps(providers))
        broadcast("env", json.dumps(env))
        broadcast("plugins", json.dumps([{
            "id": pid,
            "name": p.get("name", pid),
            "version": p.get("version", "0.1"),
            "description": p.get("description", ""),
            "widgets": p.get("widgets", []),
            "endpoints": p.get("endpoints", {}),
            "lastSeen": p.get("lastSeen", datetime.now(timezone.utc).isoformat()),
            "status": "registered"
        } for pid, p in PLUGIN_REGISTRY.items()]))

        time.sleep(POLL_INTERVAL)

# ── HTTP Handlers ─────────────────────────────────────────────────────
class SSEQueue:
    def __init__(self):
        self.queue = []
    def put_nowait(self, msg):
        self.queue.append(msg)
    def get_all(self):
        items = self.queue[:]
        self.queue.clear()
        return items

class ZESHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def _send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_html(INDEX_HTML)
        elif path == "/events":
            self._handle_sse()
        elif path == "/api/status":
            self._send_json({
                "services": scan_services(),
                "mcp": scan_mcp(),
                "providers": get_providers(),
                "env": get_env_info(),
                "logs": get_hook_logs(),
                "plugins": [{
                    "id": pid,
                    "name": p.get("name", pid),
                    "version": p.get("version", "0.1"),
                    "description": p.get("description", ""),
                    "widgets": p.get("widgets", []),
                    "endpoints": p.get("endpoints", {}),
                    "lastSeen": p.get("lastSeen", ""),
                    "status": p.get("status", "registered")
                } for pid, p in PLUGIN_REGISTRY.items()],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif path == "/api/status/services":
            self._send_json(scan_services())
        elif path == "/api/status/mcp":
            self._send_json(scan_mcp())
        elif path == "/api/status/providers":
            self._send_json(get_providers())
        elif path == "/api/status/logs":
            self._send_json(get_hook_logs())
        elif path == "/api/status/env":
            self._send_json(get_env_info())
        elif path.startswith("/api/service/restart/"):
            name = path.split("/")[-1]
            out = run(f"sv restart /data/data/com.termux/files/usr/var/service/{name} 2>/dev/null")
            self._send_json({"service": name, "result": out})
        elif path == "/api/tor/rotate":
            out = run('echo -e "AUTHENTICATE \\"\\"\\r\\nSIGNAL NEWNYM\\r\\nQUIT\\r\\n" | nc -w 2 127.0.0.1 9051 2>/dev/null || echo "Tor control port unreachable"')
            self._send_json({"result": out})
        elif path == "/api/evals":
            out = run("python3 ~/Zes-System/scripts/run-evals.py 2>&1")
            self._send_json({"result": out})
        elif path == "/api/plugins":
            self._send_json([{
                "id": pid,
                "name": p.get("name", pid),
                "version": p.get("version", "0.1"),
                "description": p.get("description", ""),
                "widgets": p.get("widgets", []),
                "endpoints": p.get("endpoints", {}),
                "lastSeen": p.get("lastSeen", ""),
                "status": p.get("status", "registered")
            } for pid, p in PLUGIN_REGISTRY.items()])
        elif path == "/api/plugins/ping":
            self._send_json({"status": "ok", "registry_size": len(PLUGIN_REGISTRY)})
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404")


    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length > 0 else "{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}
        
        if path == "/api/plugins/register":
            pid = data.get("id", data.get("name", "unknown")).replace(" ", "-").lower()
            with PLUGIN_LOCK:
                PLUGIN_REGISTRY[pid] = {
                    "name": data.get("name", pid),
                    "version": data.get("version", "0.1"),
                    "description": data.get("description", ""),
                    "widgets": data.get("widgets", []),
                    "endpoints": data.get("endpoints", {}),
                    "status": "registered",
                    "lastSeen": datetime.now(timezone.utc).isoformat()
                }
            self._send_json({"status": "registered", "id": pid})
        else:
            self._send_json({"error": "Not found"}, 404)
 
    def _handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = SSEQueue()
        with sse_lock:
            sse_clients.append(q)
        try:
            while True:
                msgs = q.get_all()
                for m in msgs:
                    self.wfile.write(m.encode())
                    self.wfile.flush()
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with sse_lock:
                if q in sse_clients:
                    sse_clients.remove(q)

# ── Start SSE background thread ───────────────────────────────────────
threading.Thread(target=sse_poll_loop, daemon=True).start()

# ── Server ────────────────────────────────────────────────────────────
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0,user-scalable=yes,viewport-fit=cover">
<title>ZES Control Center v4</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b1121; --surface:#131b2e; --surface2:#1a2540; --border:#1e3050; --border2:#2a4068;
  --text:#e2e8f0; --text2:#8899bb; --text3:#5a7aab;
  --green:#22d686; --green-bg:rgba(34,214,134,0.12);
  --red:#ff5470; --red-bg:rgba(255,84,112,0.12);
  --amber:#f5a623; --amber-bg:rgba(245,166,35,0.12);
  --blue:#4a9eff; --blue-bg:rgba(74,158,255,0.10);
  --purple:#a855f7; --purple-bg:rgba(168,85,247,0.12);
  --radius:12px; --radius-sm:8px; --header-h:56px;
}
/* ─── DRAWER NAV ─── */
.drawer-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:998;opacity:0;pointer-events:none;transition:opacity .3s}
.drawer-overlay.open{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;left:0;bottom:0;width:270px;background:var(--surface);border-right:1px solid var(--border);z-index:999;transform:translateX(-100%);transition:transform .3s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column;overflow-y:auto}
.drawer.open{transform:translateX(0)}
.drawer-header{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border)}
.drawer-logo{font-size:16px;font-weight:700;background:linear-gradient(90deg,#03a9f4,#f441a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.drawer-close{background:none;border:none;color:var(--text3);font-size:20px;cursor:pointer;padding:4px;line-height:1}
.drawer-section{padding:8px 0}
.drawer-section-title{padding:6px 16px;font-size:10px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:1px}
.drawer-item{display:flex;align-items:center;gap:10px;padding:8px 16px;color:var(--text2);text-decoration:none;font-size:13px;transition:all .15s;cursor:pointer;border:none;background:none;width:100%;text-align:left;font-family:inherit}
.drawer-item:hover{background:var(--surface2);color:var(--text)}
.drawer-item .di-icon{font-size:14px;width:20px;text-align:center}
.drawer-item .di-status{width:6px;height:6px;border-radius:50%;margin-left:auto;flex-shrink:0}
.drawer-item .di-status.green{background:var(--green)}
.drawer-item .di-status.red{background:var(--red)}
.drawer-footer{padding:12px 16px;border-top:1px solid var(--border);font-size:10px;color:var(--text3)}
.drawer-footer span{display:block;margin-top:2px}

#mainContent.shifted{padding-left:270px}

@media(max-width:768px){
  .drawer{width:100%;max-width:300px}
  #mainContent.shifted{padding-left:16px}
}

body{-webkit-tap-highlight-color:transparent;touch-action:manipulation;font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}

.header{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 16px;z-index:100;backdrop-filter:blur(12px)}
.header-left{display:flex;align-items:center;gap:12px}
.header h1{font-size:17px;font-weight:700;letter-spacing:-0.3px}
.header h1 .accent{background:linear-gradient(90deg,#03a9f4,#f441a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header-right{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--text2)}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}
.dot.green{background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse 2s infinite}
.dot.red{background:var(--red);box-shadow:0 0 8px var(--red)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}

#mainContent{padding-top:calc(var(--header-h) + 16px);padding:calc(var(--header-h) + 16px) 16px 40px;max-width:1200px;margin:0 auto}

.tab-bar{display:flex;gap:2px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:4px;margin-bottom:16px;overflow-x:auto}
.tab-btn{padding:8px 16px;border:none;background:transparent;color:var(--text2);font-size:13px;font-weight:500;cursor:pointer;border-radius:8px;transition:all .2s;white-space:nowrap;font-family:inherit;display:flex;align-items:center;gap:6px}
.tab-btn:hover{background:var(--surface2);color:var(--text)}
.tab-btn.active{background:var(--blue-bg);color:var(--blue)}
.tab-btn .badge{background:var(--red-bg);color:var(--red);font-size:10px;padding:1px 5px;border-radius:8px;font-weight:600}
.tab-content{display:none}
.tab-content.active{display:block}

/* Quick action bar */
.actions{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.actions button{background:var(--surface2);border:1px solid var(--border);color:var(--text2);padding:6px 14px;border-radius:8px;cursor:pointer;font-size:12px;font-family:inherit;transition:all .2s}
.actions button:hover{background:var(--border);color:var(--text)}
.actions button:active{transform:scale(0.96)}

/* Service grid */
.service-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}
.service-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;transition:border-color .3s}
.service-card.running{border-color:var(--green-bg)}
.service-card.stopped{border-color:var(--red-bg)}
.service-card .top{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.service-card .icon{font-size:22px;width:32px;text-align:center}
.service-card .name{font-size:14px;font-weight:600}
.service-card .status-badge{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;text-transform:uppercase;margin-left:auto}
.service-card .status-badge.running{background:var(--green-bg);color:var(--green)}
.service-card .status-badge.stopped{background:var(--red-bg);color:var(--red)}
.service-card .desc{font-size:11px;color:var(--text3);margin-bottom:6px}
.service-card .meta{font-size:10px;color:var(--text3);display:flex;gap:12px;flex-wrap:wrap}
.service-card .port{background:var(--surface2);padding:2px 6px;border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:10px}

/* Providers grid */
.providers-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}
.prov-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;display:flex;align-items:center;gap:10px}
.prov-card .dot{width:10px;height:10px;flex-shrink:0}
.prov-card .dot.active{background:var(--green);box-shadow:0 0 6px var(--green)}
.prov-card .dot.unavailable{background:var(--amber);box-shadow:0 0 6px var(--amber)}
.prov-card .dot.error{background:var(--red);box-shadow:0 0 6px var(--red)}
.prov-card .dot.unknown{background:var(--text3)}
.prov-card .info{flex:1;min-width:0}
.prov-card .model-bar{font-size:9px;color:var(--blue);margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:help}
.prov-card .pname{font-size:12px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.prov-card .ptype{font-size:10px;color:var(--text3)}
.prov-card .pauth{font-size:9px;color:var(--text3);text-transform:uppercase}

/* Plugins panel */
.plugins-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.plug-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;transition:border-color .3s}
.plug-card:hover{border-color:var(--blue-bg)}
.plug-header{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.plug-icon{font-size:18px}
.plug-name{font-size:14px;font-weight:600;flex:1}
.plug-version{font-size:10px;color:var(--text3);background:var(--surface2);padding:2px 6px;border-radius:4px}
.plug-desc{font-size:11px;color:var(--text3);margin-bottom:8px}
.plug-widgets{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.plug-widget{background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:11px;color:var(--text2);cursor:pointer;transition:all .15s}
.plug-widget:hover{background:var(--accent2);color:var(--text)}
.plug-none{font-size:10px;color:var(--text3);font-style:italic}
.plug-meta{font-size:9px;color:var(--text3);border-top:1px solid var(--border);padding-top:6px;margin-top:4px}
.plug-empty{padding:40px 20px;text-align:center;color:var(--text3);font-size:13px}
.plug-widget-frame{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px}
@media(max-width:480px){.plugins-grid{grid-template-columns:1fr}}

/* MCP panel */
.mcp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.mcp-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px}
.mcp-card.alive{border-color:var(--green-bg)}
.mcp-card .top{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.mcp-card .name{font-size:14px;font-weight:600}
.mcp-card .status{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;margin-left:auto}
.mcp-card .status.alive{background:var(--green-bg);color:var(--green)}
.mcp-card .status.dead{background:var(--red-bg);color:var(--red)}
.mcp-card .cmd{font-size:10px;color:var(--text3);font-family:'JetBrains Mono',monospace;background:var(--surface2);padding:4px 8px;border-radius:4px;margin-bottom:4px}
.mcp-card .tools{font-size:11px;color:var(--text2)}
.mcp-card .tools span{background:var(--blue-bg);color:var(--blue);padding:1px 6px;border-radius:6px;font-size:10px;margin-left:4px}

/* Log panel */
.log-panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:12px;max-height:500px;overflow-y:auto;font-family:'JetBrains Mono',monospace;font-size:11px}
.log-entry{padding:4px 0;border-bottom:1px solid var(--border);display:flex;gap:8px}
.log-time{color:var(--text3);flex-shrink:0}
.log-src{color:var(--blue);flex-shrink:0;min-width:60px}
.log-msg{color:var(--text2);word-break:break-all}

/* Stats bar */
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:16px}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;text-align:center}
.stat-card .num{font-size:24px;font-weight:800;background:linear-gradient(135deg,#03a9f4,#f441a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-card .label{font-size:11px;color:var(--text3);margin-top:2px}

/* Terminal tab */
.terminal-container{border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;height:600px;background:#000}
.terminal-container iframe{width:100%;height:100%;border:none}

/* Settings */
.settings-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}

/* ─── Mobile Optimizations ─── */
@media(max-width:768px){
  .header h1{font-size:14px}
  .header-right .dot{width:6px;height:6px}
  .header-right{font-size:10px;gap:6px}
  .actions button{padding:8px 12px;font-size:11px}
  .stats{grid-template-columns:repeat(2,1fr)}
  .stat-card{padding:10px}
  .stat-card .num{font-size:20px}
  .tab-btn{padding:6px 10px;font-size:11px}
  .terminal-container{height:350px}
}
@media(max-width:480px){
  .header{padding:0 10px}
  .header h1{font-size:13px}
  .header h1 span{font-size:11px}
  .header-right{font-size:9px}
  .actions{gap:4px}
  .actions button{padding:6px 10px;font-size:10px;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .stats{grid-template-columns:repeat(2,1fr);gap:6px}
  .stat-card{padding:8px}
  .stat-card .num{font-size:18px}
  .stat-card .label{font-size:10px}
  .tab-bar{gap:1px;padding:3px;margin-bottom:12px}
  .tab-btn{padding:5px 8px;font-size:10px}
  .tab-btn .badge{font-size:8px;padding:1px 4px}
  .service-grid{grid-template-columns:1fr;gap:8px}
  .service-card{padding:10px}
  .service-card .icon{font-size:18px;width:26px}
  .service-card .name{font-size:12px}
  .service-card .desc{font-size:10px}
  .providers-grid{grid-template-columns:1fr;gap:6px}
  .prov-card{padding:8px;gap:8px}
  .prov-card{flex-direction:column;align-items:flex-start;gap:4px;padding:8px}
  .prov-card .pname{font-size:11px}
  .prov-card .ptype{font-size:9px}
  .prov-card .model-bar{font-size:8px!important;max-width:100%}
  .prov-card .dot{width:8px;height:8px}
  .mcp-grid{grid-template-columns:1fr;gap:8px}
  .mcp-card{padding:10px}
  .mcp-card .name{font-size:12px}
  .mcp-card .cmd{font-size:9px}
  .mcp-card .tools{font-size:10px}
  .terminal-container{height:250px}
  .log-panel{max-height:300px;font-size:10px}
  .settings-grid{grid-template-columns:1fr;gap:8px}
  #mainContent{padding-left:10px;padding-right:10px}
  .drawer{width:100%;max-width:100%}
  .drawer-item{padding:10px 14px;font-size:14px}
  .drawer-item .di-icon{font-size:16px}
  .stats .stat-card:last-child:nth-child(odd){grid-column:1/3}
}
</style>
</head>
<body>

<div class="header navbar bg-base-200 border-b border-base-300 min-h-[56px] px-3">
  <div class="flex items-center gap-2">
    <button class="menu-btn btn btn-ghost btn-square btn-sm" onclick="toggleDrawer()">☰</button>
    <h1 class="text-lg font-bold"><span class="text-primary">ZES</span> Control Center <span class="text-base-content/40 font-normal text-xs">v4</span></h1>
  </div>
  <div class="flex items-center gap-3 ml-auto">
    <span id="statusDot" class="dot badge badge-xs badge-success"></span>
    <span id="statusText" class="text-sm text-base-content/70">Connected</span>
    <span id="clock" class="text-xs text-base-content/40"></span>
  </div>
</div>


<!-- ─── DRAWER ─── -->
<div class="drawer-overlay" id="drawerOverlay" onclick="toggleDrawer()"></div>
<div class="drawer" id="drawer">
  <div class="drawer-header">
    <span class="drawer-logo">ZES System</span>
    <button class="drawer-close" onclick="toggleDrawer()">✕</button>
  </div>
  <div class="drawer-section">
    <div class="drawer-section-title">Services</div>
    <div id="drawerServiceList"></div>
  </div>
  <div class="drawer-section">
    <div class="drawer-section-title">Quick Links</div>
    <a class="drawer-item" href="http://localhost:20128/" target="_blank"><span class="di-icon">🌐</span> 9Router</a>
    <a class="drawer-item" href="http://localhost:8000/" target="_blank"><span class="di-icon">💻</span> VS Code Server</a>
    <a class="drawer-item" href="http://localhost:7173/" target="_blank"><span class="di-icon">🖥</span> ttyd Terminal</a>
    <a class="drawer-item" href="http://localhost:5900/" target="_blank"><span class="di-icon">⚡</span> Codex API</a>
    <a class="drawer-item" href="http://localhost:8001/" target="_blank"><span class="di-icon">📱</span> VS Code Mobile</a>
    <a class="drawer-item" href="http://localhost:8084/" target="_blank"><span class="di-icon">🤖</span> Agent UI</a>
    <a class="drawer-item" href="http://localhost:8083/" target="_blank"><span class="di-icon">📊</span> Dashboard v4</a>
    <a class="drawer-item" href="http://localhost:5905/" target="_blank"><span class="di-icon">🧠</span> Claude Proxy (9Router)</a>
  </div>
  <div class="drawer-section">
    <div class="drawer-section-title">System</div>
    <a class="drawer-item" onclick="switchTab('terminal')"><span class="di-icon">🧠</span> Claude Code Terminal</a>
    <a class="drawer-item" onclick="rotateTor();toggleDrawer()"><span class="di-icon">🌐</span> Rotate Tor IP</a>
    <a class="drawer-item" onclick="runEvals();toggleDrawer()"><span class="di-icon">🏥</span> Run Health Evals</a>
    <a class="drawer-item" onclick="refreshAll();toggleDrawer()"><span class="di-icon">🔄</span> Force Refresh Dashboard</a>
  </div>
  <div class="drawer-footer">
    ZES Control Center v4 <span id="drawerVersion"></span>
  </div>
</div>

<div id="mainContent">
  <!-- Quick Actions -->
  <div class="actions" id="actionBar">
    <button onclick="restartService('hermes-gateway')">🔄 Restart Hermes</button>
    <button onclick="rotateTor()">🌐 Rotate Tor IP</button>
    <button onclick="runEvals()">🏥 Run Health Evals</button>
    <button onclick="switchTab('terminal')">💻 Open Terminal</button>
  </div>

  <!-- Stats -->
  <div class="stats" id="statsBar">
    <div class="stat-card stat bg-base-200 border border-base-300 rounded-xl p-4"><div class="stat-value text-3xl text-primary" id="statServices">0</div><div class="stat-title text-xs">Services</div></div>
    <div class="stat-card stat bg-base-200 border border-base-300 rounded-xl p-4"><div class="stat-value text-3xl text-success" id="statRunning">0</div><div class="stat-title text-xs">Running</div></div>
    <div class="stat-card stat bg-base-200 border border-base-300 rounded-xl p-4"><div class="stat-value text-3xl text-info" id="statProviders">0</div><div class="stat-title text-xs">Providers</div></div>
    <div class="stat-card stat bg-base-200 border border-base-300 rounded-xl p-4"><div class="stat-value text-3xl text-secondary" id="statMCP">0</div><div class="stat-title text-xs">MCP Servers</div></div>
  </div>

  <!-- Tabs -->
  <div class="tab-bar" id="tabBar">
    <button class="tab-btn btn btn-ghost btn-sm active" data-tab="services">📊 Services</button>
    <button class="tab-btn btn btn-ghost btn-sm" data-tab="providers">🔌 Providers <span class="badge badge-sm" id="provBadge">18</span></button>
    <button class="tab-btn btn btn-ghost btn-sm" data-tab="mcp">🧩 MCP <span class="badge badge-sm" id="mcpBadge">6</span></button>
    <button class="tab-btn btn btn-ghost btn-sm" data-tab="logs">📋 Audit Log</button>
    <button class="tab-btn btn btn-ghost btn-sm" data-tab="terminal">💻 Terminal</button>
    <button class="tab-btn btn btn-ghost btn-sm" data-tab="plugins">🔌 Plugins <span class="badge badge-sm" id="plugBadge">0</span></button>
    <button class="tab-btn btn btn-ghost btn-sm" data-tab="settings">⚙️ Settings</button>
  </div>

  <div id="tab-services" class="tab-content active"><div class="service-grid" id="serviceGrid"></div></div>
  <div id="tab-providers" class="tab-content"><div class="providers-grid" id="provGrid"></div></div>
  <div id="tab-mcp" class="tab-content"><div class="mcp-grid" id="mcpGrid"></div></div>
  <div id="tab-logs" class="tab-content"><div class="log-panel" id="logPanel"><div class="log-entry">Connecting...</div></div></div>
  <div id="tab-terminal" class="tab-content"><div class="terminal-container"><iframe src="http://localhost:7173/" id="termFrame" loading="lazy"></iframe></div></div>
  <div id="tab-plugins" class="tab-content"><div class="plugins-grid" id="pluginGrid"><div class="plug-empty">No plugins registered. MCP servers can register a plugin via POST to /api/plugins/register</div></div></div>
  <div id="tab-settings" class="tab-content"><div class="settings-grid" id="settingsGrid"></div></div>
</div>

<script>
// ── SSE Connection ───────────────────────────────────────────────────
const evtSource = new EventSource('/events');

evtSource.addEventListener('services', function(e) {
  const services = JSON.parse(e.data);
  renderServices(services);
  renderDrawerServices(services);
  document.getElementById('statServices').textContent = services.length;
  const running = services.filter(s => s.status === 'running').length;
  document.getElementById('statRunning').textContent = running;
});

evtSource.addEventListener('mcp', function(e) {
  const mcp = JSON.parse(e.data);
  renderMCP(mcp);
  document.getElementById('statMCP').textContent = mcp.length;
  const alive = mcp.filter(m => m.alive).length;
  document.getElementById('mcpBadge').textContent = alive + '/' + mcp.length;
});

evtSource.addEventListener('providers', function(e) {
  const providers = JSON.parse(e.data);
  renderProviders(providers);
  document.getElementById('statProviders').textContent = providers.length;
  const active = providers.filter(p => p.status === 'active' || p.active === true).length;
  document.getElementById('provBadge').textContent = active + '/' + providers.length;
});

evtSource.addEventListener('plugins', function(e) {
  const plugins = JSON.parse(e.data);
  renderPlugins(plugins);
  document.getElementById('plugBadge').textContent = plugins.length;
});

evtSource.addEventListener('env', function(e) {
  const env = JSON.parse(e.data);
  document.getElementById('statServices').textContent = env.services_total || '0';
  document.getElementById('statRunning').textContent = env.services_running || '0';
});

evtSource.onopen = function() {
  document.getElementById('statusDot').className = 'dot green';
  document.getElementById('statusText').textContent = 'Live';
};

evtSource.onerror = function() {
  document.getElementById('statusDot').className = 'dot red';
  document.getElementById('statusText').textContent = 'Reconnecting...';
  if (!window._sseFallback) {
    window._sseFallback = setInterval(function() {
      fetch('/api/status').then(function(r) { return r.json(); }).then(function(data) {
        if (data.services) { renderServices(data.services); renderDrawerServices(data.services); }
        if (data.providers) renderProviders(data.providers);
        if (data.mcp) renderMCP(data.mcp);
        if (data.env) {
          document.getElementById('statServices').textContent = data.env.services_total || data.services?.length || 0;
          document.getElementById('statRunning').textContent = data.env.services_running || 0;
        }
      }).catch(function(){});
    }, 5000);
  }
};
evtSource.addEventListener('open', function() {
  if (window._sseFallback) { clearInterval(window._sseFallback); window._sseFallback = null; }
});
// ── Clock ────────────────────────────────────────────────────────────
function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

// ── Tab switching ────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.querySelector(`.tab-btn[data-tab="${name}"]`)?.classList.add('active');
  document.getElementById(`tab-${name}`)?.classList.add('active');
  if (name === 'terminal') {
    document.getElementById('termFrame').src = 'http://localhost:7173/';
  }
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    switchTab(this.dataset.tab);
  });
});

// ── Render Plugins ──────────────────────────────────────────────────
function renderPlugins(plugins) {
  const grid = document.getElementById('pluginGrid');
  if (!plugins || plugins.length === 0) {
    grid.innerHTML = '<div class="plug-empty" style="color:var(--text3);padding:20px;text-align:center">No plugins registered. MCP servers can register widgets via POST to /api/plugins/register</div>';
    return;
  }
  grid.innerHTML = plugins.map(p => {
    const widgets = p.widgets || [];
    return '<div class="plug-card">' +
      '<div class="plug-header"><span class="plug-icon">🧩</span><span class="plug-name">' + p.name + '</span><span class="plug-version">v' + p.version + '</span></div>' +
      '<div class="plug-desc">' + (p.description || '') + '</div>' +
      (widgets.length ? '<div class="plug-widgets">' + widgets.map(w => 
        '<div class="plug-widget" onclick="loadPluginWidget(\'' + p.id + '\', \'' + (w.id || w.name || 'main') + '\')">' +
        '📦 ' + (w.name || w.id || 'widget') +
        '</div>'
      ).join('') + '</div>' : '<div class="plug-widgets plug-none">No widgets</div>') +
      '<div class="plug-meta">ID: ' + p.id + ' · Last seen: ' + (p.lastSeen || 'unknown') + '</div>' +
      '</div>';
  }).join('');
}

function loadPluginWidget(pluginId, widgetId) {
  const grid = document.getElementById('pluginGrid');
  fetch('/api/plugins/' + pluginId).then(r => r.json()).then(p => {
    const endpoint = p.endpoints && p.endpoints[widgetId];
    if (endpoint) {
      grid.innerHTML = '<div class="plug-widget-frame"><iframe src="' + endpoint + '" style="width:100%;height:400px;border:none;border-radius:8px;background:var(--surface)"></iframe>' +
        '<button onclick="renderPlugins(' + JSON.stringify([p]) + ')" style="margin-top:8px;padding:6px 14px;border-radius:8px;border:1px solid var(--border);background:var(--surface2);color:var(--text2);cursor:pointer">← Back to plugins</button></div>';
    }
  });
}

// ── Render Services ─────────────────────────────────────────────────

// ── Drawer ──
let drawerTouchStartX = 0;
let drawerTouchStartY = 0;
document.addEventListener('touchstart', function(e) {
  drawerTouchStartX = e.touches[0].clientX;
  drawerTouchStartY = e.touches[0].clientY;
}, {passive: true});
document.addEventListener('touchend', function(e) {
  const dx = e.changedTouches[0].clientX - drawerTouchStartX;
  const dy = e.changedTouches[0].clientY - drawerTouchStartY;
  // Swipe left to close drawer (on mobile, from anywhere)
  if (dx < -80 && Math.abs(dy) < 100 && window.innerWidth <= 480) {
    const drawer = document.getElementById('drawer');
    if (drawer && drawer.classList.contains('open')) {
      toggleDrawer();
    }
  }
  // Swipe right from left edge to open drawer
  if (drawerTouchStartX < 30 && dx > 60 && Math.abs(dy) < 100) {
    const drawer = document.getElementById('drawer');
    if (drawer && !drawer.classList.contains('open')) {
      toggleDrawer();
    }
  }
}, {passive: true});

function toggleDrawer() {
  document.getElementById('drawer').classList.toggle('open');
  document.getElementById('drawerOverlay').classList.toggle('open');
  document.getElementById('mainContent').classList.toggle('shifted');
}

function renderDrawerServices(services) {
  const list = document.getElementById('drawerServiceList');
  if (!list) return;
  list.innerHTML = services.map(s => `
    <div class="drawer-item" onclick="toggleDrawer();switchTab('services')">
      <span class="di-icon">${s.icon || '🔧'}</span>
      <span>${s.name}</span>
      <span class="di-status ${s.status === 'running' ? 'green' : 'red'}"></span>
    </div>
  `).join('');
}

function renderServices(services) {
  const grid = document.getElementById('serviceGrid');
  grid.innerHTML = services.map(s => `
    <div class="service-card ${s.status}">
      <div class="top">
        <div class="icon">${s.icon || '🔧'}</div>
        <div class="name">${s.name}</div>
        <span class="status-badge ${s.status}">${s.status === 'running' ? '● Live' : '○ Stop'}</span>
      </div>
      <div class="desc">${s.desc || ''}</div>
      <div class="meta">
        ${s.port ? `<span class="port">:${s.port}</span>` : ''}
        <span>${s.status === 'running' ? '✅ Online' : '❌ Offline'}</span>
        ${s.url ? `<a href="${s.url}" target="_blank" style="color:var(--blue);text-decoration:none">Open</a>` : ''}
      </div>
    </div>
  `).join('');
}

// ── Render Providers ─────────────────────────────────────────────────
function renderProviders(providers) {
  const grid = document.getElementById('provGrid');
  if (!providers || providers.length === 0) {
    grid.innerHTML = '<div style="color:var(--text3);padding:20px">No provider data</div>';
    return;
  }
  grid.innerHTML = providers.map(p => {
    const status = (p.testStatus || p.status || '').toLowerCase();
    const active = status === 'active' || p.active === true;
    const dotClass = active ? 'active' : (status === 'unavailable' ? 'unavailable' : (status === 'error' ? 'error' : 'unknown'));
    
    // Extract and clean model names from modelLock_ keys
    const modelKeys = Object.keys(p).filter(k => k.startsWith('modelLock_'));
    const modelList = modelKeys.map(k => {
      let name = k.replace('modelLock_', '');
      // Clean up @cf/, @gemini/ etc vendor prefixes for display
      name = name.replace(/^@[^/]+\//, '');
      // For paths like deepseek-ai/deepseek-v4-flash, take last part
      name = name.includes('/') ? name.split('/').pop() : name;
      return name;
    });
    const modelCount = modelList.length;
    // Show first 2 models + count badge if more
    const modelsDisplay = modelList.slice(0, 2).join(', ');
    const models = modelCount > 2 
      ? modelsDisplay + ' +' + (modelCount - 2) + ' more'
      : modelList.join(', ');
    
    const name = p.name || p.type || 'Unknown';
    const type = p.type || '';
    const authType = p.authType || '';
    const proxy = p.proxy || 'direct';
    
    return `
      <div class="prov-card">
        <span class="dot ${dotClass}"></span>
        <div class="info">
          <div class="pname">${name}</div>
          <div class="ptype">${type}</div>
          <div style="font-size:9px;color:var(--text3);margin-top:2px">${authType} · ${proxy}</div>
          ${modelCount > 0 ? `<div class="model-bar" title="${modelList.join(', ')}">🤖 ${models}</div>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

// ── Render MCP ───────────────────────────────────────────────────────
function renderMCP(servers) {
  const grid = document.getElementById('mcpGrid');
  grid.innerHTML = servers.map(m => `
    <div class="mcp-card ${m.alive ? 'alive' : ''}">
      <div class="top">
        <span class="name">${m.name}</span>
        <span class="status ${m.alive ? 'alive' : 'dead'}">${m.alive ? '● Live' : '○ Offline'}</span>
      </div>
      <div class="cmd">${m.command} ${(m.args || []).join(' ')}</div>
      <div class="tools">Tools: <span>${m.tools || '?'}</span></div>
      ${m.port ? `<div class="meta" style="margin-top:4px"><span class="port">:${m.port}</span></div>` : ''}
    </div>
  `).join('');
}

// ── Actions ──────────────────────────────────────────────────────────
function restartService(name) {
  fetch('/api/service/restart/' + name)
    .then(r => r.json())
    .then(d => alert('Restart ' + name + ': ' + d.result))
    .catch(e => alert('Error: ' + e));
}

function rotateTor() {
  fetch('/api/tor/rotate')
    .then(r => r.json())
    .then(d => alert('Tor rotate: ' + d.result))
    .catch(e => alert('Error: ' + e));
}

function runEvals() {
  const btn = event.target;
  btn.textContent = '⏳ Running...';
  btn.disabled = true;
  fetch('/api/evals')
    .then(r => r.json())
    .then(d => {
      alert('Health Evals:\n' + d.result);
      btn.textContent = '🏥 Run Health Evals';
      btn.disabled = false;
    })
    .catch(e => { alert('Error: ' + e); btn.disabled = false; });
}

// ── Initial data load ────────────────────────────────────────────────

// ── Force refresh all data ──────────────────────────────────────
function refreshAll() {
  fetch('/api/status').then(function(r) { return r.json(); }).then(function(data) {
    if (data.services) { renderServices(data.services); renderDrawerServices(data.services); }
    if (data.providers) renderProviders(data.providers);
    if (data.plugins) { renderPlugins(data.plugins); document.getElementById('plugBadge').textContent = data.plugins.length; }
    if (data.mcp) renderMCP(data.mcp);
    if (data.env) {
      document.getElementById('statServices').textContent = data.env.services_total || data.services?.length || 0;
      document.getElementById('statRunning').textContent = data.env.services_running || 0;
    }
    if (data.logs) renderLogs(data.logs);
    document.getElementById('statusDot').className = 'dot green';
    document.getElementById('statusText').textContent = 'Live';
  }).catch(function(){});
}
fetch('/api/status').then(r => r.json()).then(data => {
  if (data.services) { renderServices(data.services); renderDrawerServices(data.services); }
  if (data.providers) renderProviders(data.providers);
  if (data.plugins) { renderPlugins(data.plugins); document.getElementById('plugBadge').textContent = data.plugins.length; }
  if (data.mcp) renderMCP(data.mcp);
  if (data.env) {
    document.getElementById('statServices').textContent = data.env.services_total || data.services?.length || 0;
    document.getElementById('statRunning').textContent = data.env.services_running || 0;
    document.getElementById('statProviders').textContent = data.providers?.length || 0;
    document.getElementById('statMCP').textContent = data.mcp?.length || 0;
  }
  if (data.logs) {
    renderLogs(data.logs);
  }
});

// ── Logs via polling (not SSE) ───────────────────────────────────────
function renderLogs(logs) {
  const panel = document.getElementById('logPanel');
  if (!logs || logs.length === 0) {
    panel.innerHTML = '<div class="log-entry">No audit events yet</div>';
    return;
  }
  panel.innerHTML = logs.map(l => `
    <div class="log-entry">
      <span class="log-time">${(l.time || '').slice(11,19)}</span>
      <span class="log-src">${(l.source || 'hook').slice(0,12)}</span>
      <span class="log-msg">${(l.event || l.message || '').slice(0,200)}</span>
    </div>
  `).join('');
}

function refreshLogs() {
  fetch('/api/status/logs')
    .then(r => r.json())
    .then(d => renderLogs(d))
    .catch(() => {});
}
setInterval(refreshLogs, 5000);

// ── Settings tab ─────────────────────────────────────────────────────
const settingsGrid = document.getElementById('settingsGrid');
settingsGrid.innerHTML = [
  {icon:'ℹ️', name:'ZES Control Center v4', desc:'SSE real-time · Provider heat map · MCP panel · Audit log', meta:'Updated ' + new Date().toLocaleString()},
  {icon:'⚡', name:'Refresh Rate', desc:'SSE pushes every 3 seconds — no polling needed', meta:'Real-time via /events'},
  {icon:'📡', name:'6 MCP Servers', desc:'zeschrome, zes-bridge, chrome-devtools, filesystem, memory, sequential-thinking', meta:'Config: ~/.claude.json'},
  {icon:'🛡️', name:'Security Hooks', desc:'3 hooks active: MCP health, GateGuard, Config protection', meta:'Hooks: ~/.claude.json'},
  {icon:'🧠', name:'Claude Code', desc:'Anthropic Claude Code 2.1.207 via proot-distro Debian', meta:'CLI: claude \"prompt\"'},
  {icon:'🔌', name:'9Router Providers', desc:'18 providers · 13 active · Via OAuth + API key', meta:'Port 20128'},
  {icon:'🌀', name:'ZES Bridge MCP', desc:'10 system API tools: dashboard, 9Router, services, Tor, evals', meta:'Node stdio'},
  {icon:'📚', name:'26 Skills · 10 Agents', desc:'ZES-native + ECC-imported skills and agents', meta:'~/.agents/skills/'},
].map(c => `
  <div class="service-card" style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px">
    <div class="top"><div style="font-size:20px">${c.icon}</div></div>
    <div class="name" style="font-size:13px;font-weight:600;margin:4px 0">${c.name}</div>
    <div class="desc" style="font-size:11px;color:var(--text3)">${c.desc}</div>
    <div style="font-size:10px;color:var(--text3);margin-top:4px">${c.meta}</div>
  </div>
`).join('');
</script>
</body>
</html>
"""


def auto_register_plugins():
    import subprocess, time
    time.sleep(3)
    try:
        subprocess.run(["python3", os.path.expanduser("~/Zes-System/scripts/register-system-plugins.py")], timeout=10, capture_output=True)
    except:
        pass

if __name__ == "__main__":
    threading.Thread(target=auto_register_plugins, daemon=True).start()
    server = ThreadedHTTPServer((HOST, PORT), ZESHandler)
    print(f"🚀 ZES Dashboard v4 running on http://{HOST}:{PORT}")
    print(f"   SSE: /events · API: /api/status · Logs: /api/status/logs")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

# ── Frontend HTML (SPA with SSE) ──────────────────────────────────────

