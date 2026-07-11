#!/usr/bin/env python3
"""ZES Control Center v3 — System Dashboard + Agent Control — http://localhost:8083"""

import http.server
import json
import os
import socket
import subprocess
import threading
import urllib.request
import urllib.error
import shlex
import textwrap
import re
import time
from datetime import datetime, timedelta

HOST = "0.0.0.0"
PORT = 8083
HISTORY_FILE = os.path.expanduser("~/.dashboard_history.json")
HISTORY_LOCK = threading.Lock()
MAX_HISTORY = 120

# ─── helpers ────────────────────────────────────────────────────────────────
def tcp_open(host, port, timeout=0.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except Exception:
        return False

def http_status(url, timeout=2):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return r.status
    except Exception as e:
        if hasattr(e, "code"):
            return e.code
        return None

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if out:
            return out[:2000]
        if err:
            return err[:2000]
        return ""
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return f"(error: {e})"

def _cli_token():
    try:
        d = os.path.expanduser("~/.9router")
        mid = open(d + "/machine-id").read().strip()
        sec = open(d + "/auth/cli-secret").read().strip()
        import hashlib
        return hashlib.sha256((mid + "9r-cli-auth" + sec).encode()).hexdigest()[:16]
    except Exception:
        return ""

def _r9_auth_headers():
    tok = _cli_token()
    return {"x-9r-cli-token": tok} if tok else {}

def _r9_chat_headers():
    """Return Authorization header for 9Router OpenAI-compatible endpoint."""
    # Try to get API key from 9Router database
    try:
        db_path = os.path.expanduser("~/.9router/db/data.sqlite")
        if os.path.exists(db_path):
            import subprocess as sp
            # Use the bundled sql.js via node
            r = sp.run(["node", "-e", """
                const initSqlJs = require(process.env.HOME + "/.9router/runtime/node_modules/sql.js");
                async function main() {
                    const SQL = await initSqlJs();
                    const fs = require("fs");
                    const buffer = fs.readFileSync(process.env.HOME + "/.9router/db/data.sqlite");
                    const db = new SQL.Database(buffer);
                    const keys = db.exec("SELECT key FROM apiKeys WHERE isActive = 1 LIMIT 1");
                    if (keys.length > 0 && keys[0].values.length > 0) {
                        console.log(keys[0].values[0][0]);
                    }
                }
                main();
            """], capture_output=True, text=True, timeout=5)
            key = r.stdout.strip()
            if key:
                return {"Authorization": f"Bearer {key}"}
    except:
        pass
    # Fallback: use the known working API key
    return {"Authorization": "Bearer sk-d25ec2e336a68df0-r5e3uw-03b936b4"}

def _r9_fetch(path):
    """Fetch from 9Router API with auth."""
    try:
        req = urllib.request.Request(f"http://localhost:20128{path}")
        for k, v in _r9_auth_headers().items():
            req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None

# ─── services ───────────────────────────────────────────────────────────────
SERVICES = [
    {"id":"codex","name":"Codex App Server","port":5900,"url":"http://127.0.0.1:5900/","desc":"AI API Proxy + Zen Gateway","icon":"⚡"},
    {"id":"ttyd","name":"Web Terminal","port":7173,"url":"http://127.0.0.1:7173/","desc":"Browser-based terminal (ttyd)","icon":"🖥"},
    {"id":"socat","name":"Socat Bridge","port":8090,"desc":"TCP bridge 8090 → 54321","icon":"🔗"},
    {"id":"hermes","name":"Hermes Gateway","port":8787,"url":"","desc":"Claude Sonnet 4.6 · cron · scheduler","icon":"🤖","bin":"hermes"},
    {"id":"hermes-webui","name":"Hermes Dashboard","port":9119,"url":"","desc":"Web UI (unavailable - needs pydantic v2)","icon":"📊"},
    {"id":"r9","name":"9Router","port":20128,"url":"http://127.0.0.1:20128/","desc":"AI Router · 18 providers","icon":"🌐"},
    {"id":"tor","name":"Tor SOCKS5","port":9050,"desc":"Anonymizing proxy pool","icon":"🔒"},
    {"id":"sshd","name":"SSH Server","port":8022,"desc":"Remote shell access","icon":"🔑"},
    {"id":"claude","name":"Claude Code","port":0,"url":"","desc":"Anthropic Claude Code 2.1.207 — AI coding agent (CLI)","icon":"🧠"},
    {"id":"agent-ui","name":"Agent UI","port":8084,"url":"http://127.0.0.1:8084/","desc":"OpenClaw-inspired agent chat dashboard","icon":"🤖"},
    {"id":"composio","name":"Composio CLI","bin":"composio","desc":"Gmail + 1000+ API integrations","icon":"📬","url":"https://composio.dev"},
    {"id":"gmail","name":"Gmail Tool","bin":"gmail-tool","desc":"IMAP/SMTP email client","icon":"✉️","url":"http://localhost:8083/"},
    {"id":"browser","name":"Browser CDP","port":9222,"url":"","desc":"Headless Chromium for web auth","icon":"🌍"},
    {"id":"vscode","name":"VS Code Server","port":8000,"url":"http://127.0.0.1:8000/","desc":"Web VS Code (Cline + Continue ready)","icon":"💻"},
    {"id":"vscode-mobile","name":"VS Code Mobile","port":8001,"url":"http://127.0.0.1:8001/","desc":"Mobile-optimized VS Code panel (touch zoom, toolbar)","icon":"📱"},
    {"id":"agent-dash","name":"Agent Dashboard API","port":8002,"url":"http://127.0.0.1:8002/","desc":"Agent monitoring REST API (daemon)","icon":"🤖"},
    {"id":"agent-dash-web","name":"Agent Dashboard Web","port":8003,"url":"http://127.0.0.1:8003/","desc":"Mobile Agent Dashboard frontend","icon":"📊"},
    {"id":"zeschrome-mcp","name":"zesChrome MCP","port":5901,"url":"http://127.0.0.1:5901/","desc":"MCP server — Chrome automation via CDP","icon":"🧩"},
    {"id":"swarm","name":"ZES Swarm","port":5030,"url":"","desc":"Multi-agent orchestrator (5 agents via 9Router)","icon":"🐝","bin":"python3"},
    {"id":"toolscanner","name":"Tool Scanner","port":0,"desc":"Discover executables · runsv services","icon":"🔍"},
    {"id":"context-feeder","name":"Context Feeder","port":0,"desc":"Workspace watcher for agent context","icon":"📡"},
    {"id":"openclaw","name":"ZES Config","port":0,"url":"","desc":"ZES system config · Claude Code · 9Router","icon":"⚙️"},
    {"id":"plugins","name":"ZES Plugins","port":0,"desc":"Plugin integration — openclaw-config, skills","icon":"🧩"},
]

# ─── env info ────────────────────────────────────────────────────────────────
def _load_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except:
        return []

def _save_history(h):
    with HISTORY_LOCK:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(h[-MAX_HISTORY:], f)

def _log_status(data):
    snapshot = {"t": data["timestamp"], "services": {}}
    for s in data["services"]:
        snapshot["services"][s["id"]] = {"status": s["status"], "tcp": s["tcp"]}
    h = _load_history()
    h.append(snapshot)
    _save_history(h)

def get_env():
    return {
        "hostname": socket.gethostname(),
        "python": os.popen("python3 --version 2>/dev/null").read().strip() or "n/a",
        "node": os.popen("node --version 2>/dev/null").read().strip() or "n/a",
        "npm": os.popen("npm --version 2>/dev/null").read().strip() or "n/a",
        "go": os.popen("go version 2>/dev/null").read().strip() or "n/a",
        "proot": os.popen("proot --version 2>/dev/null | head -1 | awk '{print $2}'").read().strip() or "n/a",
        "proot_distro": os.popen("proot-distro list 2>/dev/null | awk '/^\\*/{print $2}'").read().strip() or "none",
        "uptime": run("uptime -p") or run("uptime") or "n/a",
    }

# ─── status data ────────────────────────────────────────────────────────────
def get_status():
    services = []
    for svc in SERVICES:
        if "pkg" in svc:
            try:
                import importlib.metadata as md
                md.version(svc["pkg"])
                available = True
            except Exception:
                available = False
            services.append({**svc, "tcp": available, "http": None, "status": "running" if available else "stopped"})
        elif "bin" in svc:
            try:
                import shutil
                available = shutil.which(svc["bin"]) is not None
                if not available:
                    for _hb in [os.path.expanduser("~/.local/bin"), os.path.expanduser("~/bin")]:
                        _bp = os.path.join(_hb, svc["bin"])
                        if os.path.isfile(_bp) and os.access(_bp, os.X_OK):
                            available = True
                            break
            except Exception:
                available = False
            services.append({**svc, "tcp": available, "http": None, "status": "running" if available else "stopped"})
        else:
            tcp = tcp_open("127.0.0.1", svc["port"])
            http = None
            if tcp and svc.get("url"):
                http = http_status(svc["url"])
            services.append({**svc, "tcp": tcp, "http": http, "status": "running" if tcp else "stopped"})
    return {"timestamp": datetime.now().isoformat(), "services": services, "env": get_env()}

def get_status_with_providers():
    data = get_status()
    # Fetch providers from 9Router
    try:
        pdata = _r9_fetch("/api/providers") or {}
        all_conns = pdata.get("connections", [])
        nodes_data = _r9_fetch("/api/provider-nodes") or {}
        nodes = nodes_data.get("nodes", [])
        providers = []
        for c in all_conns:
            p = c.get("provider", "")
            if p.startswith("openai-compatible"):
                continue
            psd = c.get("providerSpecificData", {})
            proxy = "Tor SOCKS5" if psd.get("connectionProxyEnabled") else "direct"
            providers.append({
                "name": c.get("name", p),
                "type": p,
                "prefix": "",
                "baseUrl": psd.get("baseUrl", ""),
                "active": c.get("isActive", False),
                "status": c.get("testStatus", "unknown"),
                "proxy": proxy,
                "authType": c.get("authType", "?"),
            })
        for n in nodes:
            providers.append({
                "name": n.get("name", "?"),
                "type": "openai-compatible",
                "prefix": n.get("prefix", ""),
                "baseUrl": n.get("baseUrl", ""),
                "active": True,
                "status": "active",
                "proxy": "via 9router",
                "authType": "node",
            })
        data["_providers"] = providers
    except Exception:
        data["_providers"] = []

    data["_provider_count"] = len(data.get("_providers", []))
    data["_provider_active"] = len([p for p in data.get("_providers", []) if p.get("active") and p.get("status") in ("active", "unknown")])

    _log_status(data)
    return data

# ─── agent conversation store ──────────────────────────────────────────────
AGENT_HISTORY = []
AGENT_HISTORY_LOCK = threading.Lock()
AGENT_HISTORY_FILE = os.path.expanduser("~/.dashboard_agent_history.json")

def load_agent_history():
    try:
        with open(AGENT_HISTORY_FILE) as f:
            return json.load(f)
    except:
        return []

def save_agent_history(h):
    with AGENT_HISTORY_LOCK:
        with open(AGENT_HISTORY_FILE, 'w') as f:
            json.dump(h[-200:], f)

def add_agent_entry(entry):
    h = load_agent_history()
    h.append(entry)
    save_agent_history(h)

# ─── ZES system knowledge prompt ──────────────────────────────────────────
ZES_SYSTEM_PROMPT = """You are ZES Agent — the intelligent assistant for the ZES (Zetta Ecosystem System) control center.

## SYSTEM ARCHITECTURE
ZES runs on Android (Termux) with proot-distro Debian. It manages:
- **9Router** (:20128) — AI provider router with 18 providers
- **Dashboard** (:8083) — This ZES Control Center (Python dashboard_v3.py)
- **Hermes Gateway** (:8787) — Cron scheduler and agent backend
- **zesChrome MCP** (:5901) — Chrome DevTools bridge for browser automation
- **VS Code Server** (:8000) — Browser VS Code (Cline + Continue + Copilot)
- **VS Code Mobile** (:8001) — Mobile-optimized VS Code wrapper
- **Agent UI** (:8084) — OpenClaw-inspired agent chat
- **Agent Dashboard** (:8002-8003) — VSCode Agent Dashboard extension
- **Headless Chrome** (:9222) — Browser automation via CDP
- **ttyd** (:7173) — Web terminal
- **Tor** (:9050/9051) — SOCKS5 proxy + ControlPort for IP rotation
- **Claude Code** — Anthropic AI coding agent (CLI v2.1.207)

## AI PROVIDERS (via 9Router)
Active providers: OpenRouter, Groq, Gemini, Gemini CLI, Cerebras, Mistral AI, Cline, Codex (OpenAI), Kiro, Qoder, Copilot (GitHub), Cloudflare AI
Unavailable: GitHub (model_not_supported), NVIDIA NIM (502 timeout), Anthropic (key issue), DeepSeek (balance)
Cloudflare AI (cf/) — 61+ models, 10000 req/day limit. Account: zescode@gmail.com

## KEY CAPABILITIES
You can help with:
1. Check service status, restart downed services
2. Route AI requests through 9Router to any provider
3. Read system logs and diagnose issues
4. Execute shell commands for system tasks
5. Use MCP browser automation (screenshot, click, type, etc.)
6. Manage IP rotation via Tor
7. Configure and test AI provider connections
8. Schedule recurring tasks via Hermes
9. Launch OAuth flows for service authentication
10. Access VS Code Server and manage extensions

When users ask you to DO something (restart a service, check something, run a command), respond with a JSON action block:
{"action": "service_restart", "params": {"service": "dashboard8083"}}
{"action": "run_command", "params": {"cmd": "ls /data/data/com.termux/files/usr/var/service/"}}
{"action": "check_logs", "params": {"service": "r9", "lines": 20}}
{"action": "check_service", "params": {"service": "r9"}}
For service status use: {"action": "run_command", "params": {"cmd": "sv status /data/data/com.termux/files/usr/var/service/SERVICENAME"}}"""

def build_system_prompt():
    """Build dynamic system prompt with current service status."""
    try:
        status = get_status()
        svc_lines = []
        for s in status.get("services", []):
            svc_lines.append(f"  [{s['status']}] {s['name']} (:{s['port']})")
        svc_block = "\n".join(svc_lines) if svc_lines else "  (unavailable)"
    except:
        svc_block = "  (unavailable)"

    try:
        env = get_env()
        env_block = "\n".join([f"  {k}: {v}" for k, v in env.items()])
    except:
        env_block = "  (unavailable)"

    prompt = ZES_SYSTEM_PROMPT + f"""

## CURRENT SYSTEM STATE ({datetime.now().strftime('%Y-%m-%d %H:%M')})

### Services:
{svc_block}

### Environment:
{env_block}

### Instructions:
- Be concise and helpful. Use actions (JSON blocks) for system tasks.
- Default model is groq/llama-3.3-70b-versatile; Cloudflare models are good fallback.
- All services run under runsv in Termux.
- When asked to fix something, first check the service, then diagnose, then suggest/execute fix.
- You have access to MCP browser tools via :5901 for web tasks."""
    return prompt

# ─── system action tools ──────────────────────────────────────────────────
def tool_service_restart(service):
    """Restart a runsv service."""
    result = run(f"sv force-restart {service} 2>&1")
    time.sleep(1)
    check = run(f"sv status {service} 2>&1")
    return {"action": "service_restart", "service": service, "result": result.strip(), "status": check.strip()}

def tool_run_command(cmd):
    """Run a shell command safely."""
    result = run(cmd)
    if not result:
        # Try with full path
        result = run(f"bash -c '{cmd}' 2>&1")
    return {"action": "run_command", "cmd": cmd[:100], "result": result[:2000] if result else "(empty output)"}

def tool_check_logs(service, lines=20):
    """Check service logs."""
    log_path = f"/data/data/com.termux/files/var/log/{service}/current"
    result = run(f"tail -{lines} {log_path} 2>&1")
    return {"action": "check_logs", "service": service, "lines": lines, "result": result[:2000]}

def tool_check_service(service):
    """Check service status."""
    svc_dir = service if service.startswith("/") else f"/data/data/com.termux/files/usr/var/service/{service}"
    port_map = {"r9":20128,"hermes":8787,"codex":5900,"ttyd":7173,"claude":0,"agent-ui":8084,"vscode-server":8000,"dashboard8083":8083,"agent-dash":8002,"agent-dash-web":8003}
    tcp_port = port_map.get(service, 0)
    if os.path.isdir(svc_dir):
        result = run(f"sv status {svc_dir} 2>&1")
        return {"action": "check_service", "service": service, "result": result.strip()}
    result = run(f"ps aux | grep -i {service} | grep -v grep | head -5")
    tcp = tcp_open("127.0.0.1", tcp_port) if tcp_port else False
    return {"action": "check_service", "service": service, "process": result[:500] if result else "none", "tcp": tcp}

SYSTEM_TOOLS = {
    "service_restart": tool_service_restart,
    "run_command": tool_run_command,
    "check_logs": tool_check_logs,
    "check_service": tool_check_service,
}

# ─── agent chat via 9Router ────────────────────────────────────────────────
def agent_chat(message, history=None, model=None):
    """Send chat to AI via 9Router with ZES system knowledge and tool execution."""
    if history is None:
        history = []
    
    # Build system prompt with current state
    sys_prompt = build_system_prompt()
    
    # If history has a system message, replace it; otherwise prepend
    msgs = []
    has_system = False
    for m in history:
        if m.get("role") == "system":
            msgs.append({"role": "system", "content": sys_prompt})
            has_system = True
        else:
            msgs.append(m)
    if not has_system:
        msgs = [{"role": "system", "content": sys_prompt}] + msgs
    msgs.append({"role": "user", "content": message})

    # Use default model from 9Router or specified
    body = {
        "model": model or "groq/llama-3.3-70b-versatile",
        "messages": msgs,
        "stream": False,
        "max_tokens": 8192,
        "temperature": 0.7,
    }

    try:
        req = urllib.request.Request(
            "http://127.0.0.1:20128/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", **_r9_chat_headers()},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.loads(r.read())
            text = result["choices"][0]["message"]["content"]
            model_used = result.get("model", model)
            usage = result.get("usage", {})
            
            # Check if response contains an action JSON block
                        # Try to find action JSON block (can be inline or in ```json block)
            action_match = None
            # First try inline JSON: {"action": "...", "params": {...}}
            for candidate in re.finditer(r'\{\s*"action"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^}]*\}\s*\}', text, re.DOTALL):
                action_match = candidate
                break
            # If not found, try inside code blocks ```json ... ```
            if not action_match:
                code_match = re.search(r'```(?:json)?\s*\n?(\{.*?"action".*?"params".*?\})\s*\n?```', text, re.DOTALL)
                if code_match:
                    action_match = code_match
            action_result = None
            if action_match:
                try:
                    action_data = json.loads(action_match.group(0))
                    action_name = action_data.get("action")
                    action_params = action_data.get("params", {})
                    if action_name in SYSTEM_TOOLS:
                        action_result = SYSTEM_TOOLS[action_name](**action_params)
                        tool_text = json.dumps(action_result, indent=2)
                        text += f"\n\n**Action Result:**\n```json\n{tool_text}\n```"
                
                except Exception as ex:
                    text += f"\n(*Action parse error: {ex}*)"
                except Exception as ex:
                    text += f"\n(*Action parse error: {ex}*)"
            entry = {
                "timestamp": datetime.now().isoformat(),
                "role": "user",
                "content": message,
            }
            add_agent_entry(entry)
            add_agent_entry({
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": text,
                "model": model_used,
                "usage": usage,
            })
            return {
                "text": text,
                "model": model_used,
                "usage": usage,
                "action": action_result,
            }
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:500]}"}
    except Exception as e:
        return {"error": str(e)}

# ─── HTTP Handler ──────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        if self.path == "/api/status":
            data = get_status_with_providers()
            return self._json(data)
        if self.path == "/api/history":
            return self._json(_load_history() or [])
        if self.path == "/api/agent/history":
            return self._json(load_agent_history() or [])
        if self.path == "/api/agent/system-prompt":
            return self._json({"prompt": build_system_prompt()})
        if self.path == "/api/chat/models":
            return self._json([
                {"id": "cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast", "name": "Cloudflare: Llama 3.3 70B", "provider": "cloudflare"},
                {"id": "cf/@cf/meta/llama-3.2-3b-instruct", "name": "Cloudflare: Llama 3.2 3B", "provider": "cloudflare"},
                {"id": "cf/@cf/qwen/qwen2.5-coder-32b-instruct", "name": "Cloudflare: Qwen 2.5 Coder 32B", "provider": "cloudflare"},
                {"id": "cf/@cf/qwen/qwq-32b", "name": "Cloudflare: QwQ 32B", "provider": "cloudflare"},
                {"id": "cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b", "name": "Cloudflare: DeepSeek R1 32B", "provider": "cloudflare"},
                {"id": "cf/@cf/moonshotai/kimi-k2.7-code", "name": "Cloudflare: Kimi K2.7 Code", "provider": "cloudflare"},
                {"id": "cf/@cf/mistralai/mistral-small-3.1-24b-instruct", "name": "Cloudflare: Mistral Small 24B", "provider": "cloudflare"},
                {"id": "cf/@cf/nvidia/nemotron-3-120b-a12b", "name": "Cloudflare: Nemotron 120B", "provider": "cloudflare"},
                {"id": "groq/@groq/llama-3.3-70b-versatile", "name": "Groq: Llama 3.3 70B", "provider": "groq"},
                {"id": "gemini/@gemini/gemini-2.5-flash", "name": "Gemini: 2.5 Flash", "provider": "gemini"},
                {"id": "deepseek/@deepseek/deepseek-chat", "name": "DeepSeek: Chat", "provider": "deepseek"},
                {"id": "cerebras/@cerebras/llama-3.3-70b", "name": "Cerebras: Llama 3.3 70B", "provider": "cerebras"},
                {"id": "openrouter/@openrouter/anthropic/claude-sonnet-4.6", "name": "OpenRouter: Claude Sonnet 4.6", "provider": "openrouter"},
                {"id": "openrouter/@openrouter/openai/gpt-4o-mini", "name": "OpenRouter: GPT-4o Mini", "provider": "openrouter"},
                {"id": "mistral/@mistralai/mistral-large-2.5", "name": "Mistral: Large 2.5", "provider": "mistral"},
            ])
        if self.path == "/api/agent/tools":
            return self._json({
                "tools": [
                    {"name": "service_restart", "description": "Restart a runsv service", "params": {"service": "string"}},
                    {"name": "run_command", "description": "Run a shell command", "params": {"cmd": "string"}},
                    {"name": "check_logs", "description": "View service logs", "params": {"service": "string", "lines": "number"}},
                    {"name": "check_service", "description": "Check service status", "params": {"service": "string"}},
                ]
            })
        if self.path == "/api/models":
            # Fetch available models from 9Router
            providers = _r9_fetch("/api/providers") or {}
            nodes_data = _r9_fetch("/api/provider-nodes") or {}
            models = []
            for c in providers.get("connections", []):
                models.append({
                    "name": c.get("name", "?"),
                    "provider": c.get("provider", "?"),
                    "status": c.get("testStatus", "unknown"),
                    "active": c.get("isActive", False),
                })
            for n in nodes_data.get("nodes", []):
                models.append({
                    "name": n.get("name", "?"),
                    "provider": "openai-compatible",
                    "prefix": n.get("prefix", ""),
                    "baseUrl": n.get("baseUrl", ""),
                    "status": "active",
                    "active": True,
                })
            return self._json(models)
        if self.path == "/api/services":
            # Check auth/service status
            services = []
            # Composio
            c_out = run("composio list 2>/dev/null | head -30")
            services.append({
                "name": "Composio",
                "status": "available" if "composio" in c_out or c_out else "not found",
                "info": c_out[:300] if c_out else "CLI not configured",
                "icon": "📬",
            })
            # Gmail
            g_out = run("which gmail-tool 2>/dev/null && gmail-tool --version 2>/dev/null || echo 'not installed'")
            services.append({
                "name": "Gmail Tool",
                "status": "installed" if "not" not in g_out else "not found",
                "info": g_out[:200],
                "icon": "✉️",
            })
            # Hermes cron
            hc_out = run("hermes cron list 2>/dev/null || echo 'n/a'")
            services.append({
                "name": "Hermes Cron",
                "status": "available",
                "info": hc_out[:300],
                "icon": "⏰",
            })
            # Swarm orchestrator
            swarm_out = run("curl -s --connect-timeout 2 http://localhost:5030/ 2>/dev/null || echo 'not running'")
            services.append({
                "name": "ZES Swarm",
                "status": "running" if "ZES Swarm" in swarm_out else "stopped",
                "info": "port 5030" if "running" in swarm_out else "not started",
                "icon": "🌀",
            })
            # Tool scanner
            import os as os_mod
            ts_path = os_mod.path.expanduser("~/.zes/discovered_tools.json")
            ts_info = "not scanned"
            if os_mod.path.exists(ts_path):
                try:
                    with open(ts_path) as f:
                        td = json.load(f)
                    ts_info = f"{td.get('tool_count',0)} tools, {td.get('service_count',0)} services"
                except: pass
            services.append({
                "name": "Tool Scanner",
                "status": "available" if os_mod.path.exists(ts_path) else "not scanned",
                "info": ts_info,
                "icon": "🔍",
            })
            # Context feeder
            cf_path = os_mod.path.expanduser("~/.zes/context_state.json")
            cf_status = "watching" if os_mod.path.exists(cf_path) else "not started"
            services.append({
                "name": "Context Feeder",
                "status": cf_status,
                "info": "",
                "icon": "📡",
            })
            return self._json(services)
        if self.path == "/api/rotation":
            rotation_data = {"status": "unknown", "last_rotation": "", "current_country": "", "model_rotation": "", "hermes_model": "groq/llama-3.3-70b-versatile", "hermes_fallback": "openrouter/anthropic/claude-sonnet-4.6"}
            try:
                # Check if Tor control port is responding
                import socket
                s = socket.socket()
                s.settimeout(3)
                s.connect(("127.0.0.1", 9051))
                s.send(b'AUTHENTICATE\r\n')
                r = s.recv(1024)
                if b"250" in r:
                    # Get current exit nodes
                    s.send(b'GETCONF ExitNodes\r\n')
                    r = s.recv(1024)
                    country = r.decode().strip().replace("250-ExitNodes=", "").replace("{", "").replace("}", "").replace("250 OK", "").strip()
                    rotation_data["status"] = "active"
                    rotation_data["current_country"] = country.upper() if country else "random"
                    # Check last circuit time
                    rotation_data["last_rotation"] = "via crontab (*/30 * * * *)"
                s.close()
            except Exception:
                rotation_data["status"] = "inactive"
            # Check if cron job exists
            import subprocess
            cron_out = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=5)
            if "ip-rotation" in cron_out.stdout:
                rotation_data["cron"] = "active"
            else:
                rotation_data["cron"] = "not found"
            if "model-rotation" in cron_out.stdout:
                rotation_data["model_rotation"] = "active"
            else:
                rotation_data["model_rotation"] = "not found"
            return self._json(rotation_data)

        if self.path == "/api/mcp":
            mcp_data = {"status": "unknown", "tools": []}
            try:
                req = urllib.request.Request("http://localhost:5901/health")
                with urllib.request.urlopen(req, timeout=2) as r:
                    mcp_data["status"] = "running"
                    mcp_data["health"] = json.loads(r.read())
                # Try listing tools
                mcp_req = urllib.request.Request(
                    "http://localhost:5901/mcp",
                    data=json.dumps({"method": "mcp.listTools", "params": {}, "id": 1}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(mcp_req, timeout=3) as r2:
                    mcp_result = json.loads(r2.read())
                    mcp_data["tools"] = mcp_result.get("result", {}).get("tools", [])
            except Exception as e:
                mcp_data["status"] = "error"
                mcp_data["error"] = str(e)
            return self._json(mcp_data)
        if self.path == "/api/health" or self.path == "/":
            status_data = get_status_with_providers()
            return self._serve_html(status_data)
        return self._serve_html(get_status_with_providers())

    def do_POST(self):
        if self.path == "/api/agent/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            message = body.get("message", "")
            history = body.get("history", [])
            model = body.get("model", None)
            if not message:
                return self._json({"error": "No message provided"})
            result = agent_chat(message, history, model)
            return self._json(result)
        if self.path == "/api/agent/chat/stream":
            """Streaming chat endpoint — returns SSE stream."""
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            message = body.get("message", "")
            history = body.get("history", [])
            model = body.get("model", None)
            if not message:
                return self._json({"error": "No message provided"})
            
            sys_prompt = build_system_prompt()
            msgs = []
            has_system = False
            for m in history:
                if m.get("role") == "system":
                    msgs.append({"role": "system", "content": sys_prompt})
                    has_system = True
                else:
                    msgs.append(m)
            if not has_system:
                msgs = [{"role": "system", "content": sys_prompt}] + msgs
            msgs.append({"role": "user", "content": message})
            
            body = {
                "model": model or "groq/llama-3.3-70b-versatile",
                "messages": msgs,
                "stream": True,
                "max_tokens": 4096,
                "temperature": 0.7,
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:20128/v1/chat/completions",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json", **_r9_chat_headers()},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=120) as r:
                    full_text = ""
                    for line in r:
                        line = line.decode().strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                self.wfile.write(b"data: [DONE]\n\n")
                                break
                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                chunk_content = delta.get("content", "")
                                if chunk_content:
                                    full_text += chunk_content
                                    payload = json.dumps({"content": chunk_content})
                                    self.wfile.write(f"data: {payload}\n\n".encode())
                            except:
                                pass
                
                add_agent_entry({
                    "timestamp": datetime.now().isoformat(),
                    "role": "user",
                    "content": message,
                })
                add_agent_entry({
                    "timestamp": datetime.now().isoformat(),
                    "role": "assistant",
                    "content": full_text,
                    "model": model,
                })
                
                
                # Try to find action JSON block (can be inline or in ```json block)
                action_match = None
                # First try inline JSON: {"action": "...", "params": {...}}
                for candidate in re.finditer(r'\{\s*"action"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^}]*\}\s*\}', full_text, re.DOTALL):
                    action_match = candidate
                    break
                # If not found, try inside code blocks ```json ... ```
                if not action_match:
                    code_match = re.search(r'```(?:json)?\s*\n?(\{.*?"action".*?"params".*?\})\s*\n?```', full_text, re.DOTALL)
                    if code_match:
                        action_match = code_match
                if action_match:
                    try:
                        action_data = json.loads(action_match.group(0))
                        action_name = action_data.get("action")
                        action_params = action_data.get("params", {})
                        if action_name in SYSTEM_TOOLS:
                            action_result = SYSTEM_TOOLS[action_name](**action_params)
                            payload = json.dumps({"action_result": action_result})
                            self.wfile.write(f"data: {payload}\n\n".encode())
                    except Exception as ex:
                        payload = json.dumps({"action_error": str(ex)})
                        self.wfile.write(f"data: {payload}\n\n".encode())
                
                self.wfile.write(b"data: [COMPLETE]\n\n")
            except Exception as e:
                payload = json.dumps({"error": str(e)})
                self.wfile.write(f"data: {payload}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")
            return
        
        if self.path == "/api/agent/action":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            action = body.get("action", "")
            params = body.get("params", {})
            # Proxy to MCP server
            try:
                mcp_req = urllib.request.Request(
                    "http://localhost:5901/mcp",
                    data=json.dumps({
                        "method": "mcp.callTool",
                        "params": {"name": action, "arguments": params},
                        "id": int(datetime.now().timestamp() * 1000),
                    }).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(mcp_req, timeout=30) as r:
                    result = json.loads(r.read())
                    add_agent_entry({
                        "timestamp": datetime.now().isoformat(),
                        "role": "action",
                        "action": action,
                        "params": params,
                        "result": result.get("result", {}),
                    })
                    return self._json(result.get("result", {}))
            except Exception as e:
                return self._json({"error": str(e)})
        if self.path == "/api/services/auth":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            service = body.get("service", "")
            # Launch OAuth in browser via CDP
            try:
                mcp_req = urllib.request.Request(
                    "http://localhost:5901/mcp",
                    data=json.dumps({
                        "method": "mcp.callTool",
                        "params": {"name": "auth", "arguments": {"service": service}},
                        "id": int(datetime.now().timestamp() * 1000),
                    }).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(mcp_req, timeout=30) as r:
                    result = json.loads(r.read())
                    return self._json({"status": "started", "service": service, "result": result.get("result", {})})
            except Exception as e:
                return self._json({"error": str(e)})
        if self.path == "/api/agent/task":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            task = body.get("task", "")
            schedule = body.get("schedule", "now")
            # Schedule via Hermes cron if available
            if schedule != "now" and tcp_open("127.0.0.1", 8787):
                try:
                    h_req = urllib.request.Request(
                        "http://127.0.0.1:8787/api/tasks",
                        data=json.dumps({
                            "task": task,
                            "schedule": schedule,
                            "source": "dashboard",
                        }).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(h_req, timeout=10) as r:
                        hermes_result = json.loads(r.read())
                    result = {"status": "scheduled", "hermes": hermes_result}
                except Exception as e:
                    result = {"status": "error", "error": str(e)}
            else:
                # Execute immediately via 9Router
                result = agent_chat(
                    f"[SYSTEM TASK] {task}\n\nPlease complete this task and report results.",
                    [],
                    "cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast"
                )
                result["status"] = "completed"
            add_agent_entry({
                "timestamp": datetime.now().isoformat(),
                "role": "task",
                "task": task,
                "schedule": schedule,
                "result": result,
            })
            return self._json(result)
        return self._json({"error": "Not found"})
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass

    def _serve_html(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE.replace("__DATA__", json.dumps(data)).encode())
        self.wfile.write(b"<!-- live reload -->")

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE TEMPLATE — Full Single-Page App
# ══════════════════════════════════════════════════════════════════════════════
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>ZES Control Center v3</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b1121; --surface:#131b2e; --surface2:#1a2540;
  --border:#1e3050; --border2:#2a4068;
  --text:#e2e8f0; --text2:#8899bb; --text3:#5a7aab;
  --green:#22d686; --green-bg:rgba(34,214,134,0.12);
  --red:#ff5470; --red-bg:rgba(255,84,112,0.12);
  --amber:#f5a623; --amber-bg:rgba(245,166,35,0.12);
  --blue:#4a9eff; --blue-bg:rgba(74,158,255,0.10);
  --purple:#a855f7; --purple-bg:rgba(168,85,247,0.12);
  --radius:12px; --radius-sm:8px;
  --drawer-width:260px;
  --header-h:60px;
}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}

/* ─── DRAWER ─── */
.drawer-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:998;opacity:0;pointer-events:none;transition:opacity .3s ease}
.drawer-overlay.open{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;left:0;bottom:0;width:var(--drawer-width);background:var(--surface);border-right:1px solid var(--border);z-index:999;transform:translateX(-100%);transition:transform .3s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column;overflow-y:auto}
.drawer.open{transform:translateX(0)}
.drawer-header{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--border)}
.drawer-logo{display:flex;align-items:center;gap:10px}
.drawer-logo-icon{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,#03a9f4,#f441a5);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#fff}
.drawer-logo-text{font-size:16px;font-weight:700}
.drawer-close{background:none;border:none;color:var(--text3);font-size:22px;cursor:pointer;padding:4px}
.drawer-nav{flex:1;padding:8px 0}
.nav-item{display:flex;align-items:center;gap:12px;padding:10px 16px;color:var(--text2);text-decoration:none;font-size:14px;border-radius:0;transition:all .15s;cursor:pointer;border:none;background:none;width:100%;text-align:left;font-family:inherit}
.nav-item:hover{background:var(--surface2);color:var(--text)}
.nav-item.active{background:var(--surface2);color:var(--text);border-left:3px solid var(--blue)}
.nav-item .nav-icon{font-size:16px;width:24px;text-align:center}
.nav-item .nav-badge{margin-left:auto;background:var(--blue-bg);color:var(--blue);font-size:10px;padding:2px 6px;border-radius:10px;font-weight:600}
.drawer-footer{padding:12px 16px;border-top:1px solid var(--border);font-size:11px;color:var(--text3)}
.drawer-footer .ver{color:var(--text3)}
.drawer-footer a{color:var(--blue);text-decoration:none}

/* ─── HEADER ─── */
.header{position:fixed;top:0;left:0;right:0;height:var(--header-h);background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 16px;z-index:100;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px)}
.header-left{display:flex;align-items:center;gap:12px}
.menu-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text2);width:36px;height:36px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px;transition:all .2s}
.menu-btn:hover{background:var(--border);color:var(--text)}
.z-logo-wrap{position:relative;padding:2px;background:linear-gradient(90deg,#03a9f4,#f441a5);border-radius:0.8em;transition:all 0.4s ease;flex-shrink:0;width:38px;height:38px;display:flex;align-items:center;justify-content:center;cursor:pointer}
.z-logo-wrap::before{content:"";position:absolute;inset:0;margin:auto;border-radius:0.8em;z-index:-10;filter:blur(0);transition:filter 0.4s ease}
.z-logo-wrap:hover::before{background:linear-gradient(90deg,#03a9f4,#f441a5);filter:blur(1.2em)}
.z-logo-btn{font-size:1.2em;padding:0.2em 0.4em;border-radius:0.5em;border:none;background-color:#000;color:#fff;cursor:pointer;box-shadow:2px 2px 3px #000000b4;font-family:"Inter","JetBrains Mono",sans-serif;font-weight:800;line-height:1}
.header h1{font-size:17px;font-weight:700;letter-spacing:-0.3px;white-space:nowrap}
.header h1 span{color:var(--text2);font-weight:400}
.header h1 .zes-accent{background:linear-gradient(90deg,#03a9f4,#f441a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.header-right{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text2);flex-shrink:0}
.status-dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.status-dot.green{background:var(--green);box-shadow:0 0 6px var(--green)}
.status-dot.red{background:var(--red);box-shadow:0 0 6px var(--red)}
.header-time{color:var(--text3);font-size:11px}
.refresh-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text2);border-radius:6px;padding:3px 8px;font-size:11px;cursor:pointer;transition:all .2s;white-space:nowrap}
.refresh-btn:hover{background:var(--border);color:var(--text)}
.refresh-btn:active{transform:scale(0.95)}

/* ─── MAIN CONTENT ─── */
#mainContent{padding-top:calc(var(--header-h) + 16px);padding-left:16px;padding-right:16px;padding-bottom:40px;transition:padding-left .3s ease;max-width:1200px;margin:0 auto}
#mainContent.shifted{padding-left:calc(var(--drawer-width) + 16px)}

/* ─── TAB BAR ─── */
.tab-bar{display:flex;gap:2px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:4px;margin-bottom:20px;overflow-x:auto;-webkit-overflow-scrolling:touch}
.tab-btn{padding:8px 16px;border:none;background:transparent;color:var(--text2);font-size:13px;font-weight:500;cursor:pointer;border-radius:8px;transition:all .2s;white-space:nowrap;font-family:inherit;display:flex;align-items:center;gap:6px}
.tab-btn:hover{background:var(--surface2);color:var(--text)}
.tab-btn.active{background:var(--blue-bg);color:var(--blue)}
.tab-content{display:none}
.tab-content.active{display:block}

/* ─── SUMMARY CARDS ─── */
.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px}
.summary .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;transition:border-color .2s}
.summary .card:hover{border-color:var(--border2)}
.summary .card .num{font-size:26px;font-weight:800;letter-spacing:-0.5px;line-height:1}
.summary .card .label{font-size:11px;color:var(--text2);margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;font-weight:600}
.summary .card .sub{font-size:10px;color:var(--text3);margin-top:1px}

/* ─── SECTION TITLES ─── */
.section-title{font-size:13px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:0.8px;margin:20px 0 10px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:var(--border)}

/* ─── SERVICE GRID ─── */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.service-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;transition:border-color .2s;position:relative;overflow:hidden}
.service-card:hover{border-color:var(--border2)}
.service-card.running{border-left:3px solid var(--green)}
.service-card.stopped{border-left:3px solid var(--red)}
.service-card .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.service-card .icon{font-size:18px;width:30px;height:30px;border-radius:7px;background:var(--surface2);display:flex;align-items:center;justify-content:center}
.service-card .name{font-size:13px;font-weight:600}
.service-card .port{font-size:11px;color:var(--text3);font-family:'JetBrains Mono',monospace;margin-top:1px}
.service-card .desc{font-size:11px;color:var(--text2);margin-top:3px;line-height:1.4}
.service-card .status-badge{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:0.3px}
.service-card .status-badge.running{background:var(--green-bg);color:var(--green)}
.service-card .status-badge.stopped{background:var(--red-bg);color:var(--red)}
.service-card .action-link{display:inline-flex;align-items:center;gap:4px;margin-top:6px;font-size:11px;color:var(--blue);text-decoration:none;font-weight:500}
.service-card .action-link:hover{text-decoration:underline}

/* ─── LINKS BAR ─── */
.links{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.links a{padding:5px 12px;background:var(--surface);border:1px solid var(--border);border-radius:20px;color:var(--text2);text-decoration:none;font-size:12px;transition:all .2s}
.links a:hover{background:var(--surface2);border-color:var(--border2);color:var(--text)}

/* ─── PROVIDER TABLE ─── */
.table-wrap{overflow-x:auto;border-radius:var(--radius);border:1px solid var(--border)}
.provider-table{width:100%;border-collapse:collapse;background:var(--surface);min-width:450px;font-size:13px}
.provider-table th{padding:8px 12px;text-align:left;font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid var(--border);font-weight:600}
.provider-table td{padding:8px 12px;border-bottom:1px solid var(--border)}
.provider-table tr:last-child td{border-bottom:none}
.provider-table tr:hover td{background:var(--surface2)}
.status-tag{display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}
.status-tag.active{background:var(--green-bg);color:var(--green)}
.status-tag.inactive{background:var(--red-bg);color:var(--red)}
.status-tag.unknown{background:var(--amber-bg);color:var(--amber)}

/* ─── ENV GRID ─── */
.env-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.env-item{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px}
.env-item .key{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:2px}
.env-item .val{font-size:13px;color:var(--text);font-family:'JetBrains Mono',monospace;word-break:break-all}

/* ─── CHAT UI ─── */
.chat-container{display:flex;flex-direction:column;height:calc(100vh - var(--header-h) - 120px);min-height:400px}
.chat-messages{flex:1;overflow-y:auto;padding:12px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:10px;display:flex;flex-direction:column;gap:10px}
.chat-msg{max-width:85%;padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.5;animation:fadeIn .2s ease}
.chat-msg.user{background:var(--blue-bg);color:var(--blue);align-self:flex-end;border-bottom-right-radius:4px}
.chat-msg.assistant{background:var(--surface2);color:var(--text);align-self:flex-start;border-bottom-left-radius:4px}
.chat-msg.system{background:var(--amber-bg);color:var(--amber);align-self:center;font-size:11px;text-align:center;max-width:100%}
.chat-msg.action{background:var(--purple-bg);color:var(--purple);align-self:flex-start;font-family:'JetBrains Mono',monospace;font-size:11px}
.chat-msg .msg-time{font-size:9px;color:var(--text3);margin-top:4px;opacity:0.7}
.chat-msg .msg-model{font-size:9px;color:var(--text3);margin-top:2px;opacity:0.5}
.chat-input-area{display:flex;gap:8px}
.chat-input{flex:1;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 14px;color:var(--text);font-size:13px;font-family:inherit;outline:none;transition:border-color .2s}
.chat-input:focus{border-color:var(--blue)}
.chat-send-btn{background:var(--blue);color:#fff;border:none;border-radius:var(--radius-sm);padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;transition:all .2s;white-space:nowrap}
.chat-send-btn:hover{opacity:0.9;transform:translateY(-1px)}
.chat-send-btn:disabled{opacity:0.4;cursor:not-allowed;transform:none}
.chat-model-select{background:var(--surface2);border:1px solid var(--border);color:var(--text2);border-radius:6px;padding:4px 8px;font-size:11px;font-family:inherit}
.chat-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}

/* ─── MODEL CARDS ─── */
.model-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px}
.model-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;transition:border-color .2s}
.model-card:hover{border-color:var(--border2)}
.model-card .model-name{font-size:13px;font-weight:600}
.model-card .model-provider{font-size:11px;color:var(--text3);margin-top:2px}
.model-card .model-status{margin-top:6px}

/* ─── SERVICE AUTH CARDS ─── */
.auth-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.auth-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px}
.auth-card .auth-name{font-size:14px;font-weight:600;display:flex;align-items:center;gap:8px}
.auth-card .auth-status{font-size:12px;margin-top:6px}
.auth-card .auth-info{font-size:11px;color:var(--text3);margin-top:4px;white-space:pre-wrap;font-family:'JetBrains Mono',monospace}
.auth-btn{background:var(--blue);color:#fff;border:none;border-radius:6px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;margin-top:8px;transition:all .2s}
.auth-btn:hover{opacity:0.9}
.auth-btn.secondary{background:var(--surface2);color:var(--text2);border:1px solid var(--border)}
.auth-btn.secondary:hover{background:var(--border)}

/* ─── HERMES CRON ─── */
.cron-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.cron-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px}
.cron-card .cron-title{font-size:13px;font-weight:600;display:flex;align-items:center;gap:8px}
.cron-card .cron-schedule{font-size:11px;color:var(--text3);font-family:'JetBrains Mono',monospace;margin-top:4px}
.cron-card .cron-desc{font-size:12px;color:var(--text2);margin-top:4px}

/* ─── FOOTER ─── */
.footer{text-align:center;padding:16px;color:var(--text3);font-size:11px;margin-top:20px;border-top:1px solid var(--border)}
.footer a{color:var(--blue);text-decoration:none}

/* ─── SPARKLINES ─── */
.history-chart{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px;margin-bottom:16px;overflow-x:auto}

/* ─── RESPONSIVE ─── */
@media(max-width:768px){
  .summary{grid-template-columns:repeat(2,1fr)}
  .summary .card{padding:12px}
  .summary .card .num{font-size:22px}
  .grid{grid-template-columns:1fr}
  .model-grid{grid-template-columns:1fr}
  .auth-grid{grid-template-columns:1fr}
  .cron-grid{grid-template-columns:1fr}
  .env-grid{grid-template-columns:1fr}
  .links a{font-size:11px;padding:4px 10px}
  #mainContent{padding-left:12px;padding-right:12px}
  #mainContent.shifted{padding-left:12px}
  .header h1{font-size:14px}
  .header-right .proot-label{display:none}
  .header-time{display:none}
  .tab-btn{padding:6px 10px;font-size:12px}
  .chat-container{height:calc(100vh - var(--header-h) - 100px);min-height:300px}
  .chat-msg{max-width:92%;font-size:12px}
}
@media(max-width:480px){
  .tab-bar{gap:1px;padding:3px}
  .tab-btn{padding:5px 8px;font-size:11px}
  .summary .card .num{font-size:18px}
}
</style>
</head>
<body>

<!-- ─── DRAWER OVERLAY ─── -->
<div class="drawer-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>

<!-- ─── DRAWER ─── -->
<div class="drawer" id="drawer">
  <div class="drawer-header">
    <div class="drawer-logo">
      <div class="drawer-logo-icon">Z</div>
      <div class="drawer-logo-text">ZES System</div>
    </div>
    <button class="drawer-close" onclick="closeDrawer()">✕</button>
  </div>
  <div class="drawer-nav">
    <button class="nav-item active" data-tab="services" onclick="switchTab('services')">
      <span class="nav-icon">📡</span> Services
      <span class="nav-badge" id="svcBadge">0</span>
    </button>
    <button class="nav-item" data-tab="agent" onclick="switchTab('agent')">
      <span class="nav-icon">🤖</span> Agent Chat
    </button>
    <button class="nav-item" data-tab="models" onclick="switchTab('models')">
      <span class="nav-icon">🔌</span> AI Models
      <span class="nav-badge" id="modelBadge">0</span>
    </button>
    <button class="nav-item" data-tab="auth" onclick="switchTab('auth')">
      <span class="nav-icon">🔑</span> Services Auth
    </button>
    <button class="nav-item" data-tab="cron" onclick="switchTab('cron')">
      <span class="nav-icon">⏰</span> Cron Jobs
    </button>
    <button class="nav-item" data-tab="history" onclick="switchTab('history')">
      <span class="nav-icon">📜</span> Agent History
    </button>
    <button class="nav-item" data-tab="env" onclick="switchTab('env')">
      <span class="nav-icon">⚙</span> Environment
    </button>
    <button class="nav-item" data-tab="settings" onclick="switchTab('settings')">
      <span class="nav-icon">🔧</span> Settings
    </button>
  </div>
  <div class="drawer-footer">
    <div class="ver">ZES Control Center v3</div>
    <div><a href="http://localhost:20128" target="_blank">9Router</a> · <a href="http://localhost:5901/health" target="_blank">MCP</a></div>
  </div>
</div>

<!-- ─── HEADER ─── -->
<header class="header">
  <div class="header-left">
    <button class="menu-btn" onclick="toggleDrawer()">☰</button>
    <div class="z-logo-wrap"><button class="z-logo-btn" onclick="switchTab('services')">Z</button></div>
    <h1><span class="zes-accent">ZES</span> <span>Control</span></h1>
  </div>
  <div class="header-right">
    <span class="proot-label">
      <span class="status-dot green" id="headerDot"></span>
      <span id="headerStatus">OK</span>
    </span>
    <span class="header-time" id="headerTime"></span>
    <select id="refreshRate" onchange="setRefreshRate(this.value)" style="background:var(--surface2);border:1px solid var(--border);color:var(--text2);padding:3px 5px;border-radius:5px;font-size:10px">
      <option value="5000">5s</option>
      <option value="10000" selected>10s</option>
      <option value="30000">30s</option>
      <option value="0">Pause</option>
    </select>
    <button class="refresh-btn" onclick="refreshNow()">⟳</button>
  </div>
</header>

<!-- ─── MAIN CONTENT ─── -->
<div id="mainContent">
  <div id="app"><!-- injected by render() --></div>
</div>

<script>
const DATA = __DATA__;
let drawerOpen = false;
let refreshTimer = null;
let refreshInterval = 10000;
// Restore active tab from localStorage
let activeTab = localStorage.getItem('zesActiveTab') || 'services';

function toggleDrawer() {
  if (drawerOpen) closeDrawer();
  else openDrawer();
}
function openDrawer() {
  drawerOpen = true;
  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawerOverlay').classList.add('open');
}
function closeDrawer() {
  drawerOpen = false;
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('open');
}

function switchTab(tab) {
  activeTab = tab;
  localStorage.setItem('zesActiveTab', tab);
  // Update nav items
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.tab === tab);
  });
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.toggle('active', el.id === 'tab-' + tab);
  });
  closeDrawer();
  if (tab === 'agent') initChat();
  if (tab === 'history') loadAgentHistory();
  if (tab === 'cron') initCron();
  if (tab === 'settings') loadSettings();
}

function render(d) {
  const running = d.services.filter(s => s.status === 'running').length;
  const stopped = d.services.filter(s => s.status === 'stopped').length;
  const total = d.services.length;
  const providers = d._providers || [];
  const activeProv = d._provider_active || providers.filter(p => p.active && (p.status === 'active' || p.status === 'unknown')).length;

  // Update badges
  document.getElementById('svcBadge').textContent = running;
  document.getElementById('modelBadge').textContent = providers.length;

  // Header status
  document.getElementById('headerDot').className = 'status-dot ' + (stopped === 0 ? 'green' : 'red');
  document.getElementById('headerStatus').textContent = stopped === 0 ? 'All OK' : stopped + ' down';
  document.getElementById('headerTime').textContent = new Date(d.timestamp).toLocaleTimeString();

  // Service cards
  let cards = d.services.map(s => {
    const isRun = s.status === 'running';
    const portStr = s.port ? `:${s.port}` : '';
    const linkHtml = (isRun && s.url) ? `<a href="${s.url}" target="_blank" class="action-link">→ Open</a>` : '';
    return `<div class="service-card ${isRun ? 'running' : 'stopped'}">
      <div class="top">
        <div class="icon">${s.icon}</div>
        <div class="status-badge ${isRun ? 'running' : 'stopped'}">${isRun ? '● Up' : '○ Down'}</div>
      </div>
      <div class="name">${s.name}</div>
      <div class="port">${s.id}${portStr}</div>
      <div class="desc">${s.desc || ''}</div>
      ${linkHtml}
    </div>`;
  }).join('');

  // Provider rows
  let provRows = providers.map(p => {
    const statusClass = p.active && (p.status === 'active' || p.status === 'unknown') ? 'active' : 'inactive';
    const statusLabel = p.active && (p.status === 'active' || p.status === 'unknown') ? 'Active' : 'Inactive';
    const endpoint = p.baseUrl || p.prefix || '-';
    return `<tr>
      <td><strong>${p.name}</strong><br><span style="color:var(--text3);font-size:11px">${p.type}</span></td>
      <td style="font-family:'JetBrains Mono',monospace;font-size:12px">${p.prefix || '-'}</td>
      <td style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text3);word-break:break-all">${endpoint}</td>
      <td><span class="status-tag ${statusClass}">${statusLabel}</span></td>
      <td style="font-size:11px;color:var(--text3)">${p.proxy || 'direct'}</td>
    </tr>`;
  }).join('');

  // Env items
  let envItems = Object.entries(d.env || {}).map(([k,v]) =>
    `<div class="env-item"><div class="key">${k}</div><div class="val">${v}</div></div>`
  ).join('');

  // Build tabs
  let html = `
    <div class="tab-bar">
      <button class="tab-btn ${activeTab === 'services' ? 'active' : ''}" onclick="switchTab('services')">📡 Services</button>
      <button class="tab-btn ${activeTab === 'agent' ? 'active' : ''}" onclick="switchTab('agent')">💬 Agent</button>
      <button class="tab-btn ${activeTab === 'models' ? 'active' : ''}" onclick="switchTab('models')">🔌 Models</button>
      <button class="tab-btn ${activeTab === 'auth' ? 'active' : ''}" onclick="switchTab('auth')">🔑 Auth</button>
      <button class="tab-btn ${activeTab === 'history' ? 'active' : ''}" onclick="switchTab('history')">📜 Log</button>
      <button class="tab-btn ${activeTab === 'settings' ? 'active' : ''}" onclick="switchTab('settings')">⚙️ Settings</button>
    </div>

    <!-- TAB: Services -->
    <div class="tab-content ${activeTab === 'services' ? 'active' : ''}" id="tab-services">
      <div class="summary">
        <div class="card"><div class="num" style="color:var(--green)">${running}</div><div class="label">Running</div><div class="sub">services active</div></div>
        <div class="card"><div class="num" style="color:var(--red)">${stopped}</div><div class="label">Stopped</div><div class="sub">need attention</div></div>
        <div class="card"><div class="num" style="color:var(--blue)">${total}</div><div class="label">Total</div><div class="sub">monitored services</div></div>
        <div class="card"><div class="num" style="color:var(--amber)">${activeProv}</div><div class="label">AI Providers</div><div class="sub">via 9Router</div></div>
      </div>

      <div class="links">
        <a href="http://localhost:20128" target="_blank">🌐 9Router</a>
        <a href="http://localhost:8787" target="_blank">🤖 Hermes</a>
        <a href="http://localhost:8000" target="_blank">💻 VS Code</a>
        <a href="#" onclick="alert('Claude\\u2019s a CLI tool - run: claude --help');return false" style="cursor:help">🧠 Claude Code</a>
        <a href="http://localhost:7173" target="_blank">🖥 Terminal</a>
        <a href="http://localhost:5900" target="_blank">⚡ Codex</a>
        <a href="http://localhost:5901" target="_blank">🧩 MCP</a>
      </div>

      <div class="section-title">📡 Services</div>
      <div class="grid">${cards}</div>

      <div class="section-title">📈 Uptime (last 2h)</div>
      <div class="history-chart" id="historyChart">
        <div id="sparklines" style="min-height:60px;display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:12px">Loading…</div>
      </div>

      <div class="section-title">🔌 AI Providers (${providers.length})</div>
      <div class="table-wrap"><table class="provider-table">
        <tr><th>Name</th><th>Prefix</th><th>Endpoint</th><th>Status</th><th>Proxy</th></tr>
        ${provRows}
      </table></div>
    </div>

    <!-- TAB: Agent Chat -->
    <div class="tab-content ${activeTab === 'agent' ? 'active' : ''}" id="tab-agent">
      <div class="chat-container" id="chatContainer">
        <div class="chat-messages" id="chatMessages">
          <div class="chat-msg system">ZES Agent ready. Ask me anything via 9Router AI.</div>
        </div>
        <div class="chat-controls">
          <select class="chat-model-select" id="chatModel">
            <option value="cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast">Cloudflare: Llama 3.3 70B</option>
            <option value="cf/@cf/meta/llama-3.2-3b-instruct">Cloudflare: Llama 3.2 3B</option>
            <option value="cf/@cf/qwen/qwen2.5-coder-32b-instruct">Cloudflare: Qwen 2.5 Coder 32B</option>
            <option value="cf/@cf/qwen/qwq-32b">Cloudflare: QwQ 32B</option>
            <option value="cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b">Cloudflare: DeepSeek R1 32B</option>
            <option value="cf/@cf/moonshotai/kimi-k2.7-code">Cloudflare: Kimi K2.7 Code</option>
            <option value="cf/@cf/mistralai/mistral-small-3.1-24b-instruct">Cloudflare: Mistral Small 24B</option>
            <option value="cf/@cf/nvidia/nemotron-3-120b-a12b">Cloudflare: Nemotron 120B</option>
            <option value="groq/@groq/llama-3.3-70b-versatile">Groq: Llama 3.3 70B</option>
            <option value="gemini/@gemini/gemini-2.5-flash">Gemini: 2.5 Flash</option>
            <option value="deepseek/@deepseek/deepseek-chat">DeepSeek: Chat</option>
            <option value="cerebras/@cerebras/llama-3.3-70b">Cerebras: Llama 3.3 70B</option>
          </select>
          <span id="chatStatus" style="font-size:11px;color:var(--text3)"></span>
        </div>
        <div class="chat-input-area">
          <input class="chat-input" id="chatInput" placeholder="Ask the agent..." onkeydown="if(event.key==='Enter') sendChat()">
          <button class="chat-send-btn" id="chatSendBtn" onclick="sendChat()">Send</button>
        </div>
      </div>
    </div>

    <!-- TAB: Models -->
    <div class="tab-content ${activeTab === 'models' ? 'active' : ''}" id="tab-models">
      <div class="section-title">🔌 AI Models via 9Router</div>
      <div class="model-grid" id="modelGrid">
        <div style="color:var(--text3);font-size:13px;padding:20px;text-align:center">Loading models…</div>
      </div>
    </div>

    <!-- TAB: Auth -->
    <div class="tab-content ${activeTab === 'auth' ? 'active' : ''}" id="tab-auth">
      <div class="section-title">🔑 Service Authentication</div>
      <div class="auth-grid" id="authGrid">
        <div style="color:var(--text3);font-size:13px;padding:20px;text-align:center">Loading services…</div>
      </div>
    </div>

    <!-- TAB: History -->
    <div class="tab-content ${activeTab === 'history' ? 'active' : ''}" id="tab-history">
      <div class="section-title">📜 Agent History</div>
      <div id="historyLog" style="color:var(--text3);font-size:13px;padding:10px">Loading history…</div>
    </div>

    <!-- TAB: Settings -->
    <div class="tab-content ${activeTab === 'settings' ? 'active' : ''}" id="tab-settings">
      <div class="section-title">🔧 Settings & About</div>
      <div class="settings-grid" id="settingsGrid">
        <div style="color:var(--text3);font-size:13px;padding:20px;text-align:center">Loading settings…</div>
      </div>
    </div>

    <div style="margin-top:16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:12px 16px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px">
      <div style="display:flex;align-items:center;gap:8px">
        <span id="rotationIcon" style="font-size:14px">🔄</span>
        <span style="font-size:12px;color:var(--text2)">IP Rotation:</span>
        <span id="rotationStatus" style="font-size:12px;font-weight:600">checking...</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text3)">
        <span id="rotationCountry"></span>
        <span>·</span>
        <span>Cron: <span id="rotationCron">-</span></span>
      </div>
    </div>

    <div class="footer">
      Updated ${new Date(d.timestamp).toLocaleString()} ·
      <a href="https://9router.com" target="_blank">9router.com</a> ·
      ZES v3
    </div>


  `;

  document.getElementById('app').innerHTML = html;

  // Handle drawer shift on desktop
  const mc = document.getElementById('mainContent');
  if (window.innerWidth >= 769) {
    mc.classList.add('shifted');
  } else {
    mc.classList.remove('shifted');
  }
}

// Lightweight status update — only touches data elements, preserves DOM structure
function updateStatus(d) {
  const running = d.services.filter(s => s.status === 'running').length;
  const stopped = d.services.filter(s => s.status === 'stopped').length;
  const total = d.services.length;
  const providers = d._providers || [];
  const activeProv = d._provider_active || providers.filter(p => p.active && (p.status === 'active' || p.status === 'unknown')).length;

  // Badges
  var el = document.getElementById('svcBadge');
  if (el) el.textContent = running;
  el = document.getElementById('modelBadge');
  if (el) el.textContent = providers.length;

  // Header
  el = document.getElementById('headerDot');
  if (el) el.className = 'status-dot ' + (stopped === 0 ? 'green' : 'red');
  el = document.getElementById('headerStatus');
  if (el) el.textContent = stopped === 0 ? 'All OK' : stopped + ' down';
  el = document.getElementById('headerTime');
  if (el) el.textContent = new Date(d.timestamp).toLocaleTimeString();

  // Summary cards
  var nums = document.querySelectorAll('#tab-services .summary .card .num');
  if (nums.length >= 4) {
    nums[0].textContent = running;
    nums[1].textContent = stopped;
    nums[2].textContent = total;
    nums[3].textContent = activeProv;
  }

  // Service cards grid
  var grid = document.querySelector('#tab-services .grid');
  if (grid) {
    grid.innerHTML = d.services.map(function(s) {
      var isRun = s.status === 'running';
      var portStr = s.port ? ':' + s.port : '';
      var linkHtml = (isRun && s.url) ? '<a href="' + s.url + '" target="_blank" class="action-link">→ Open</a>' : '';
      return '<div class="service-card ' + (isRun ? 'running' : 'stopped') + '">' +
        '<div class="top"><div class="icon">' + s.icon + '</div>' +
        '<div class="status-badge ' + (isRun ? 'running' : 'stopped') + '">' + (isRun ? '● Up' : '○ Down') + '</div></div>' +
        '<div class="name">' + s.name + '</div>' +
        '<div class="port">' + s.id + portStr + '</div>' +
        '<div class="desc">' + (s.desc || '') + '</div>' +
        linkHtml + '</div>';
    }).join('');
  }

  // Provider table
  var provTable = document.querySelector('#tab-services .provider-table');
  if (provTable) {
    var rows = providers.map(function(p) {
      var statusClass = p.active && (p.status === 'active' || p.status === 'unknown') ? 'active' : 'inactive';
      var statusLabel = p.active && (p.status === 'active' || p.status === 'unknown') ? 'Active' : 'Inactive';
      var endpoint = p.baseUrl || p.prefix || '-';
      return '<tr><td><strong>' + p.name + '</strong><br><span style="color:var(--text3);font-size:11px">' + p.type + '</span></td>' +
        '<td style="font-family:JetBrains Mono,monospace;font-size:12px">' + (p.prefix || '-') + '</td>' +
        '<td style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--text3);word-break:break-all">' + endpoint + '</td>' +
        '<td><span class="status-tag ' + statusClass + '">' + statusLabel + '</span></td>' +
        '<td style="font-size:11px;color:var(--text3)">' + (p.proxy || 'direct') + '</td></tr>';
    }).join('');
    // Keep header row, replace body rows
    var header = provTable.querySelector('tr');
    provTable.innerHTML = '';
    if (header) provTable.appendChild(header);
    provTable.insertAdjacentHTML('beforeend', rows);
  }

  // Provider count heading
  var provHeading = document.querySelector('#tab-services .section-title');
  if (provHeading && provHeading.textContent.indexOf('AI Providers') !== -1) {
    provHeading.textContent = '🔌 AI Providers (' + providers.length + ')';
  }

  // Footer
  var footers = document.querySelectorAll('.footer');
  if (footers.length > 0) {
    footers[0].innerHTML = 'Updated ' + new Date(d.timestamp).toLocaleString() + ' · <a href="https://9router.com" target="_blank">9router.com</a> · ZES v3';
  }
}

render(DATA);
// Restore the saved tab state after render
setTimeout(() => {
  const savedTab = localStorage.getItem('zesActiveTab');
  if (savedTab && savedTab !== 'services') {
    switchTab(savedTab);
  } else {
    // Even for services tab, restore chat state if it was agent
    restoreChatState();
  }
}, 50);
window.addEventListener('resize', () => {
  const mc = document.getElementById('mainContent');
  if (window.innerWidth >= 769) {
    mc.classList.add('shifted');
  } else {
    mc.classList.remove('shifted');
    if (drawerOpen) closeDrawer();
  }
});

// ─── Refresh ────────────
function setRefreshRate(ms) {
  ms = parseInt(ms);
  refreshInterval = ms;
  localStorage.setItem('dashboardRefresh', ms);
  if (refreshTimer) clearInterval(refreshTimer);
  if (ms > 0) {
    refreshTimer = setInterval(() => fetchStatus(), ms);
  }
}
function refreshNow() { fetchStatus(); }
function fetchStatus() {
  fetch('/api/status').then(r=>r.json()).then(function(d) {
    updateStatus(d);
    fetchHistory();
  }).catch(function(){});
}
function fetchHistory() {
  fetch('/api/history').then(r=>r.json()).then(h=>renderSparklines(h)).catch(()=>{});
}
function renderSparklines(history) {
  if (!history || history.length < 2) {
    document.getElementById('sparklines').innerHTML = '<span style="color:var(--text3);font-size:12px">Not enough data yet</span>';
    return;
  }
  const svcIds = Object.keys(history[0].services || {});
  const relevant = svcIds.filter(id => ['codex','ttyd','socat','hermes','r9','tor','sshd','vscode','browser','agent-ui'].includes(id));
  let html = '<div style="display:flex;flex-wrap:wrap;gap:10px">';
  for (const id of relevant) {
    const svc = (DATA.services || []).find(s => s.id === id);
    if (!svc) continue;
    const values = history.map(h => h.services?.[id]?.tcp ? 1 : 0);
    const width = Math.max(values.length * 3, 60);
    const height = 28;
    const points = values.map((v, i) => `${i * 3},${height - v * height}`).join(' ');
    html += '<div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px;min-width:130px">';
    html += '<div style="font-size:11px;font-weight:600;margin-bottom:3px">' + svc.icon + ' ' + svc.name + '</div>';
    html += '<svg width="' + width + '" height="' + height + '" style="display:block">';
    const areaPoints = '0,' + height + ' ' + points + ' ' + width + ',' + height;
    html += '<polygon points="' + areaPoints + '" fill="' + (values[values.length-1] ? 'rgba(34,214,134,0.15)' : 'rgba(255,84,112,0.15)') + '" />';
    html += '<polyline points="' + points + '" fill="none" stroke="' + (values[values.length-1] ? 'var(--green)' : 'var(--red)') + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />';
    const lastVal = values[values.length-1];
    html += '<circle cx="' + ((values.length-1)*3) + '" cy="' + (height - lastVal*height) + '" r="2.5" fill="' + (lastVal ? 'var(--green)' : 'var(--red)') + '" />';
    html += '</svg>';
    html += '<div style="font-size:10px;color:var(--text3);margin-top:1px">' + (lastVal ? 'Up' : 'Down') + ' · ' + values.filter(v=>v).length + '/' + values.length + ' samples</div>';
    html += '</div>';
  }
  html += '</div>';
  const el = document.getElementById('sparklines');
  if (el) el.innerHTML = html;
}

// ─── Agent Chat ──────────
let chatHistory = [];

function initChat() {
  restoreChatState();
  const input = document.getElementById('chatInput');
  if (input) setTimeout(() => input.focus(), 300);
}
function addChatMessage(role, content, extra) {
  const msgs = document.getElementById('chatMessages');
  if (!msgs) return;
  const div = document.createElement('div');
  div.className = 'chat-msg ' + role;
  div.textContent = content;
  if (extra) {
    const time = document.createElement('div');
    time.className = 'msg-time';
    time.textContent = extra.time || '';
    div.appendChild(time);
    if (extra.model) {
      const m = document.createElement('div');
      m.className = 'msg-model';
      m.textContent = 'Model: ' + extra.model;
      div.appendChild(m);
    }
  }
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function saveChatState() {
  const msgs = document.getElementById('chatMessages');
  if (!msgs) return;
  const state = [];
  msgs.querySelectorAll('.chat-msg').forEach(el => {
    state.push({className: el.className, text: el.textContent});
  });
  localStorage.setItem('zesChatState', JSON.stringify(state));
  localStorage.setItem('zesChatHistory', JSON.stringify(chatHistory));
}

function restoreChatState() {
  const state = localStorage.getItem('zesChatState');
  if (!state) return;
  try {
    const msgs = JSON.parse(state);
    const container = document.getElementById('chatMessages');
    if (!container) return;
    container.innerHTML = '';
    msgs.forEach(m => {
      const div = document.createElement('div');
      div.className = m.className;
      div.textContent = m.text;
      container.appendChild(div);
    });
  } catch(e) {}
  const hist = localStorage.getItem('zesChatHistory');
  if (hist) {
    try { chatHistory = JSON.parse(hist); } catch(e) {}
  }
}

function sendChat() {
  const input = document.getElementById('chatInput');
  const btn = document.getElementById('chatSendBtn');
  const status = document.getElementById('chatStatus');
  const modelSelect = document.getElementById('chatModel');
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  btn.disabled = true;
  status.textContent = 'Thinking…';
  addChatMessage('user', msg, {time: new Date().toLocaleTimeString()});
  saveChatState();

  const model = modelSelect ? modelSelect.value : 'cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast';

  fetch('/api/agent/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg, history: chatHistory, model: model})
  })
  .then(r => r.json())
  .then(data => {
    btn.disabled = false;
    if (data.error) {
      addChatMessage('system', 'Error: ' + data.error, {time: new Date().toLocaleTimeString()});
      status.textContent = 'Error';
      saveChatState();
    } else {
      addChatMessage('assistant', data.text, {
        time: new Date().toLocaleTimeString(),
        model: data.model
      });
      chatHistory.push({role: 'user', content: msg});
      chatHistory.push({role: 'assistant', content: data.text});
      status.textContent = 'OK';
      saveChatState();
    }
  })
  .catch(err => {
    btn.disabled = false;
    addChatMessage('system', 'Network error: ' + err.message, {time: new Date().toLocaleTimeString()});
    status.textContent = 'Error';
  });
}

// ─── Models Tab ─────────
function loadModels() {
  const grid = document.getElementById('modelGrid');
  if (!grid) return;
  fetch('/api/models')
    .then(r => r.json())
    .then(models => {
      if (!models || models.length === 0) {
        grid.innerHTML = '<div style="color:var(--text3);font-size:13px;text-align:center;padding:20px">No models loaded. Check 9Router connection.</div>';
        return;
      }
      grid.innerHTML = models.map(m => {
        const isActive = m.active && (m.status === 'active' || m.status === 'unknown');
        return '<div class="model-card">' +
          '<div class="model-name">' + (m.name || m.provider || '?') + '</div>' +
          '<div class="model-provider">' + (m.provider || m.type || '') + (m.prefix ? ' · ' + m.prefix : '') + '</div>' +
          '<div class="model-status"><span class="status-tag ' + (isActive ? 'active' : 'inactive') + '">' + (isActive ? 'Active' : 'Inactive') + '</span></div>' +
          '</div>';
      }).join('');
    })
    .catch(() => {
      grid.innerHTML = '<div style="color:var(--text3);font-size:13px;text-align:center;padding:20px">Failed to load models.</div>';
    });
}

// ─── Auth Tab ───────────
function loadAuthServices() {
  const grid = document.getElementById('authGrid');
  if (!grid) return;
  fetch('/api/services')
    .then(r => r.json())
    .then(services => {
      if (!services || services.length === 0) {
        grid.innerHTML = '<div style="color:var(--text3);font-size:13px;text-align:center;padding:20px">No services found.</div>';
        return;
      }
      grid.innerHTML = services.map(s => {
        const isOk = s.status && !s.status.includes('not') && s.status !== 'not found';
        return '<div class="auth-card">' +
          '<div class="auth-name">' + (s.icon || '🔌') + ' ' + s.name + '</div>' +
          '<div class="auth-status"><span class="status-tag ' + (isOk ? 'active' : 'inactive') + '">' + s.status + '</span></div>' +
          '<div class="auth-info">' + (s.info || 'No info') + '</div>' +
          '<button class="auth-btn secondary" onclick="triggerAuth(\'' + s.name.toLowerCase().replace(/ /g,'-') + '\')">Re-auth</button>' +
          '</div>';
      }).join('');
    })
    .catch(() => {
      grid.innerHTML = '<div style="color:var(--text3);font-size:13px;text-align:center;padding:20px">Failed to load services.</div>';
    });
}

function triggerAuth(service) {
  fetch('/api/services/auth', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({service: service})
  })
  .then(r => r.json())
  .then(data => {
    alert('Auth flow started for ' + service + '. Check the browser.');
  })
  .catch(err => {
    alert('Error: ' + err.message);
  });
}

// ─── History Tab ────────
function loadAgentHistory() {
  const log = document.getElementById('historyLog');
  if (!log) return;
  fetch('/api/agent/history')
    .then(r => r.json())
    .then(history => {
      if (!history || history.length === 0) {
        log.innerHTML = '<div style="color:var(--text3);padding:10px">No agent history yet. Start chatting with the agent.</div>';
        return;
      }
      // Show latest first, grouped
      const reversed = [...history].reverse().slice(0, 100);
      log.innerHTML = reversed.map(e => {
        const role = e.role || 'event';
        const icon = role === 'user' ? '👤' : role === 'assistant' ? '🤖' : role === 'action' ? '🔧' : role === 'task' ? '📋' : '📌';
        const time = e.timestamp ? new Date(e.timestamp).toLocaleString() : '';
        const content = e.content || e.text || e.action || e.task || JSON.stringify(e);
        return '<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px;margin-bottom:6px">' +
          '<div style="font-size:11px;color:var(--text3);margin-bottom:2px">' + icon + ' ' + role + ' · ' + time + '</div>' +
          '<div style="font-size:12px;color:var(--text);' + (role === 'assistant' ? '' : '') + '">' + content.slice(0, 500) + '</div>' +
          (e.model ? '<div style="font-size:10px;color:var(--text3);margin-top:2px">Model: ' + e.model + '</div>' : '') +
          '</div>';
      }).join('');
    })
    .catch(() => {
      log.innerHTML = '<div style="color:var(--text3);padding:10px">Failed to load history.</div>';
    });
}

// ─── Cron Tab ───────────
function initCron() {
  const cronHtml = '<div class="cron-grid">' +
    '<div class="cron-card"><div class="cron-title">⏰ Daily Health Check</div><div class="cron-schedule">0 6 * * *</div><div class="cron-desc">Check all services and report status</div></div>' +
    '<div class="cron-card"><div class="cron-title">🔄 Model Rotation</div><div class="cron-schedule">0 0 * * 0</div><div class="cron-desc">Rotate AI provider models weekly</div></div>' +
    '<div class="cron-card"><div class="cron-title">🧹 Log Cleanup</div><div class="cron-schedule">0 3 * * *</div><div class="cron-desc">Clean old logs and history files</div></div>' +
    '<div class="cron-card"><div class="cron-title">📊 Dashboard Snapshot</div><div class="cron-schedule">*/5 * * * *</div><div class="cron-desc">Save 5-min service snapshots</div></div>' +
    '</div>' +
    '<div style="margin-top:12px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px">' +
    '<div style="font-size:12px;color:var(--text2);margin-bottom:6px">⚡ Hermes Gateway</div>' +
    '<div style="font-size:11px;color:var(--text3)">Cron managed via Hermes. Configure at <code>~/.hermes/config.yaml</code></div>' +
    '</div>';
  const el = document.getElementById('tab-cron');
  if (el && !el.querySelector('.cron-grid')) {
    const section = el.querySelector('.section-title');
    if (section) {
      section.insertAdjacentHTML('afterend', cronHtml);
    }
  }
}

// ─── IP Rotation Status ───
function checkRotation() {
  fetch('/api/rotation').then(r=>r.json()).then(data => {
    const icon = document.getElementById('rotationIcon');
    const status = document.getElementById('rotationStatus');
    const country = document.getElementById('rotationCountry');
    const cron = document.getElementById('rotationCron');
    if (!icon) return;
    if (data.status === 'active') {
      icon.textContent = '🟢';
      status.textContent = 'Active';
      status.style.color = 'var(--green)';
      country.textContent = 'Exit: ' + (data.current_country || 'random');
      cron.textContent = data.cron || 'active';
    } else {
      icon.textContent = '🔴';
      status.textContent = 'Inactive';
      status.style.color = 'var(--red)';
      country.textContent = 'Tor ControlPort not responding';
      cron.textContent = data.cron || 'n/a';
    }
  }).catch(() => {
    const el = document.getElementById('rotationStatus');
    if (el) el.textContent = 'unavailable';
  });
}

// ─── Init ───────────────
setTimeout(() => {
  const sel = document.getElementById('refreshRate');
  if (sel) {
    const saved = localStorage.getItem('dashboardRefresh');
    if (saved) sel.value = saved;
    setRefreshRate(sel.value);
  }
  fetchHistory();
  // Load models and auth in background
  setTimeout(loadModels, 500);
  setTimeout(loadAuthServices, 800);
  setTimeout(checkRotation, 500);
}, 100);

function loadSettings() {
  const grid = document.getElementById('settingsGrid');
  if (!grid) return;
  grid.innerHTML = `
    <div class="service-card">
      <div class="top"><div class="icon">ℹ️</div></div>
      <div class="name">ZES Control Center v3</div>
      <div class="desc">9Router Dashboard · Hermes Cron · IP Rotation</div>
      <div class="port">Updated ${new Date().toLocaleString()}</div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">⚡</div></div>
      <div class="name">Extension</div>
      <div class="desc">zesChrome gear icon opens this tab</div>
      <div class="port">Port closure fix applied</div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">📡</div></div>
      <div class="name">Refresh Rate</div>
      <div class="desc">Status auto-refresh interval</div>
      <div class="port">
        <select id="settingsRefreshRate" onchange="setRefreshRate(this.value)" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:5px;font-size:12px;margin-top:4px">
          <option value="5000">5s</option>
          <option value="10000" selected>10s</option>
          <option value="30000">30s</option>
          <option value="60000">60s</option>
          <option value="300000">5min</option>
        </select>
        <button onclick="setRefreshRate(0)" style="background:var(--red-bg);color:var(--red);border:none;border-radius:4px;padding:2px 8px;font-size:11px;margin-left:4px;cursor:pointer">Pause</button>
      </div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">🔒</div></div>
      <div class="name">Tor IP Rotation</div>
      <div class="desc">Rotates exit node every 30 min</div>
      <div class="port">Countries: US, DE, FR, NL, CA, GB, JP, SG, CH, SE, NO, AU, KR, IE, FI</div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">🌀</div></div>
      <div class="name">ZES Swarm</div>
      <div class="desc">Multi-agent orchestrator — 5 agents via 9Router</div>
      <div class="port"><code style="font-size:10px">python3 services/zes_swarm.py --port 5030</code></div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">🔍</div></div>
      <div class="name">Tool Scanner</div>
      <div class="desc">Discover executables + runsv services</div>
      <div class="port"><code style="font-size:10px">python3 services/tool_scanner.py</code></div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">📡</div></div>
      <div class="name">Context Feeder</div>
      <div class="desc">Watches workspace, feeds context to agents</div>
      <div class="port"><code style="font-size:10px">python3 services/context_feeder.py &</code></div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">⚙️</div></div>
      <div class="name">ZES Config</div>
      <div class="desc">3 agents · 9Router-native · fallback chains</div>
      <div class="port"><code style="font-size:10px">~/.openclaw/openclaw.json</code></div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">📬</div></div>
      <div class="name">Composio Gmail</div>
      <div class="desc">OAuth: arfaxtrade@gmail.com</div>
      <div class="port"><a href="http://localhost:8083/auth/gmail" style="color:var(--blue)">Reconnect</a></div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">🤖</div></div>
      <div class="name">Hermes Model</div>
      <div class="desc">Claude Sonnet 4.6 via 9Router (GitHub Copilot)</div>
      <div class="port">Fallback: OpenRouter Claude Sonnet 4.6</div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">🔄</div></div>
      <div class="name">Model IP Rotation</div>
      <div class="desc">deepseek-v4-flash · Tor exit rotates every 30min</div>
      <div class="port">Countries: US, DE, FR, NL, CA, GB, JP, SG, CH, SE, NO, AU, KR, IE, FI</div>
    </div>
    <div class="service-card">
      <div class="top"><div class="icon">📖</div></div>
      <div class="name">Quick Links</div>
      <div class="desc" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px">
        <a href="http://localhost:20128/" target="_blank" style="color:var(--blue);font-size:11px">9Router</a>
        <a href="http://localhost:8000/" target="_blank" style="color:var(--blue);font-size:11px">VS Code</a>
        <span style="color:var(--text3);font-size:11px">🧠 Claude Code</span>
        <a href="http://localhost:7173/" target="_blank" style="color:var(--blue);font-size:11px">ttyd</a>
      </div>
    </div>
  `;
  // Sync the refresh rate select with current value
  const sel = document.getElementById('settingsRefreshRate');
  const current = localStorage.getItem('dashboardRefresh') || '10000';
  if (sel) sel.value = current;
}

if (refreshTimer) clearInterval(refreshTimer);
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"🚀 ZES Control Center v3 → http://{HOST}:{PORT}")
    print(f"   API: http://{HOST}:{PORT}/api/status")
    print(f"   Chat: http://{HOST}:{PORT}/api/agent/chat")
    print(f"   Models: http://{HOST}:{PORT}/api/models")
    print(f"   MCP: http://{HOST}:{PORT}/api/mcp")
    srv.serve_forever()
