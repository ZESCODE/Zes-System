#!/usr/bin/env python3
"""ZES Control Center — System Dashboard — http://localhost:8083"""
import http.server
import json
import os
import socket
import subprocess
import threading
import urllib.request
from datetime import datetime, timedelta

HOST = "127.0.0.1"
PORT = 8083
HISTORY_FILE = os.path.expanduser("~/.dashboard_history.json")
HISTORY_LOCK = threading.Lock()
MAX_HISTORY = 120  # 2 hours at 60s intervals

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
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
        return r.stdout.strip()
    except Exception:
        return ""

# ─── current services ───────────────────────────────────────────────────────
SERVICES = [
    {"id":"codex","name":"Codex App Server","port":5900,"url":"http://127.0.0.1:5900/","desc":"AI API Proxy + Zen Gateway","icon":"⚡"},
    {"id":"ttyd","name":"Web Terminal","port":7173,"url":"http://127.0.0.1:7173/","desc":"Browser-based terminal (ttyd)","icon":"🖥"},
    {"id":"socat","name":"Socat Bridge","port":8090,"desc":"TCP bridge 8090 → 54321","icon":"🔗"},
    {"id":"hermes","name":"Hermes WebUI","port":8787,"url":"http://127.0.0.1:8787/","desc":"AI Agent dashboard","icon":"🤖"},
    {"id":"r9","name":"9Router","port":20128,"url":"http://127.0.0.1:20128/","desc":"AI Router · 17 providers","icon":"🌐"},
    {"id":"tor","name":"Tor SOCKS5","port":9050,"desc":"Anonymizing proxy pool","icon":"🔒"},
    {"id":"sshd","name":"SSH Server","port":8022,"desc":"Remote shell access","icon":"🔑"},
    {"id":"opencode","name":"OpenCode Server","port":9876,"url":"http://127.0.0.1:9876/","desc":"OpenCode 2.0 AI coding agent","icon":"🔮"},
    {"id":"composio","name":"Composio CLI","bin":"composio","desc":"Gmail + 1000+ API integrations","icon":"📬","url":"https://composio.dev"},
    {"id":"gmail","name":"Gmail Tool","bin":"gmail-tool","desc":"IMAP/SMTP email client","icon":"✉️","url":"http://localhost:8083/"},
    {"id":"browser","name":"Browser CDP","port":9222,"url":"","desc":"Headless Chromium for web auth","icon":"🌍"},
    {"id":"vscode","name":"VS Code Server","port":8000,"url":"http://127.0.0.1:8000/","desc":"Web VS Code (Cline + Continue ready)","icon":"💻"},
    {"id":"vscode-mobile","name":"VS Code Mobile","port":8001,"url":"http://127.0.0.1:8001/","desc":"Mobile-optimized VS Code panel (touch zoom, toolbar)","icon":"📱"},
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
    """Append current status snapshot to rolling history file."""
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
                import importlib.metadata as md; md.version(svc["pkg"])
                available = True
            except Exception:
                available = False
            services.append({
                **svc,
                "tcp": available,
                "http": None,
                "status": "running" if available else "stopped",
            })
        elif "bin" in svc:
            try:
                import subprocess, shutil
                available = shutil.which(svc["bin"]) is not None
                if not available:
                    for _home_bin in [os.path.expanduser("~/.local/bin"), os.path.expanduser("~/bin")]:
                        _bp = os.path.join(_home_bin, svc["bin"])
                        if os.path.isfile(_bp) and os.access(_bp, os.X_OK):
                            available = True
                            break
            except Exception:
                available = False
            services.append({
                **svc,
                "tcp": available,
                "http": None,
                "status": "running" if available else "stopped",
            })
        else:
            tcp = tcp_open("127.0.0.1", svc["port"])
            http = None
            if tcp and svc.get("url"):
                http = http_status(svc["url"])
            services.append({
                **svc,
                "tcp": tcp,
                "http": http,
                "status": "running" if tcp else "stopped",
            })
        # pkg/bin services: append already set up in the if/elif blocks above
    return {
        "timestamp": datetime.now().isoformat(),
        "services": services,
        "env": get_env(),
    }

# ─── render ─────────────────────────────────────────────────────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>ZES Control Center</title>
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
  --radius:12px; --radius-sm:8px;
  --drawer-width:280px;
  --header-h:64px;
}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}

/* ─── DRAWER ─── */
.drawer-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.6);z-index:998;opacity:0;pointer-events:none;transition:opacity .3s ease}
.drawer-overlay.open{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;left:0;bottom:0;width:var(--drawer-width);background:var(--surface);border-right:1px solid var(--border);z-index:999;transform:translateX(-100%);transition:transform .3s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column;overflow-y:auto}
.drawer.open{transform:translateX(0)}
.drawer-header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid var(--border)}
.drawer-logo{display:flex;align-items:center;gap:10px}
.drawer-logo-icon{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,#03a9f4,#f441a5);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#fff}
.drawer-logo-text{font-size:16px;font-weight:700}
.drawer-close{background:var(--surface2);border:1px solid var(--border);color:var(--text2);width:32px;height:32px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px;transition:all .2s}
.drawer-close:hover{background:var(--border);color:var(--text)}
.drawer-nav{padding:12px 0;flex:1}
.drawer-section-title{padding:12px 18px 6px;font-size:10px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:1px}
.drawer-link{display:flex;align-items:center;gap:12px;padding:10px 18px;font-size:14px;color:var(--text2);text-decoration:none;transition:all .15s;border-left:3px solid transparent}
.drawer-link:hover{background:var(--surface2);color:var(--text);border-left-color:var(--blue)}
.drawer-link .dl-icon{font-size:18px;width:24px;text-align:center}
.drawer-footer{padding:14px 18px;border-top:1px solid var(--border);font-size:11px;color:var(--text3)}
.drawer-footer .df-row{display:flex;justify-content:space-between;padding:3px 0}
.drawer-footer .df-val{font-family:'JetBrains Mono',monospace;color:var(--text2)}

/* ─── MAIN LAYOUT ─── */
.main-content{transition:margin-left .3s cubic-bezier(.4,0,.2,1);min-height:100vh}
.container{max-width:1100px;margin:0 auto;padding:0 20px 60px}

/* header */
.header{display:flex;align-items:center;justify-content:space-between;padding:0 0 16px;height:var(--header-h);border-bottom:1px solid var(--border);margin-bottom:24px;position:sticky;top:0;background:var(--bg);z-index:100}
.header-left{display:flex;align-items:center;gap:12px}
.menu-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text2);width:38px;height:38px;border-radius:8px;cursor:pointer;display:none;align-items:center;justify-content:center;font-size:20px;transition:all .2s;flex-shrink:0}
.menu-btn:hover{background:var(--border);color:var(--text)}
.z-logo-wrap{position:relative;padding:3px;background:linear-gradient(90deg,#03a9f4,#f441a5);border-radius:0.9em;transition:all 0.4s ease;flex-shrink:0;width:44px;height:44px;display:flex;align-items:center;justify-content:center;cursor:pointer}
.z-logo-wrap::before{content:"";position:absolute;inset:0;margin:auto;border-radius:0.9em;z-index:-10;filter:blur(0);transition:filter 0.4s ease}
.z-logo-wrap:hover::before{background:linear-gradient(90deg,#03a9f4,#f441a5);filter:blur(1.2em)}
.z-logo-wrap:active::before{filter:blur(0.2em)}
.z-logo-btn{font-size:1.4em;padding:0.3em 0.5em;border-radius:0.5em;border:none;background-color:#000;color:#fff;cursor:pointer;box-shadow:2px 2px 3px #000000b4;font-family:"Inter","JetBrains Mono",sans-serif;font-weight:800;line-height:1}
.header h1{font-size:20px;font-weight:700;letter-spacing:-0.3px;white-space:nowrap}
.header h1 span{color:var(--text2);font-weight:400}.header h1 .zes-accent{background:linear-gradient(90deg,#03a9f4,#f441a5);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.header-right{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--text2);flex-shrink:0}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.status-dot.green{background:var(--green);box-shadow:0 0 8px var(--green)}
.status-dot.red{background:var(--red);box-shadow:0 0 8px var(--red)}
.header-right .proot-label{display:inline-flex;align-items:center;gap:5px}
.header-time{color:var(--text3)}
.refresh-btn{background:var(--surface2);border:1px solid var(--border);color:var(--text2);border-radius:6px;padding:4px 10px;font-size:12px;cursor:pointer;transition:all .2s;white-space:nowrap}
.refresh-btn:hover{background:var(--border);color:var(--text)}
.refresh-btn:active{transform:scale(0.95)}

/* summary cards */
.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}
.summary .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;transition:border-color .2s}
.summary .card:hover{border-color:var(--border2)}
.summary .card .num{font-size:28px;font-weight:800;letter-spacing:-0.5px;line-height:1}
.summary .card .label{font-size:11px;color:var(--text2);margin-top:5px;text-transform:uppercase;letter-spacing:0.5px;font-weight:600}
.summary .card .sub{font-size:10px;color:var(--text3);margin-top:1px}

/* section headings */
.section-title{font-size:14px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:0.8px;margin:24px 0 12px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:var(--border)}

/* service grid */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.service-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;transition:border-color .2s,box-shadow .2s;position:relative;overflow:hidden}
.service-card:hover{border-color:var(--border2)}
.service-card.running{border-left:3px solid var(--green)}
.service-card.stopped{border-left:3px solid var(--red)}
.service-card .top{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.service-card .icon{font-size:20px;width:34px;height:34px;border-radius:8px;background:var(--surface2);display:flex;align-items:center;justify-content:center}
.service-card .name{font-size:14px;font-weight:600}
.service-card .port{font-size:11px;color:var(--text3);font-family:'JetBrains Mono',monospace;margin-top:1px}
.service-card .desc{font-size:12px;color:var(--text2);margin-top:4px;line-height:1.4}
.service-card .status-badge{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:3px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:0.3px}
.service-card .status-badge.running{background:var(--green-bg);color:var(--green)}
.service-card .status-badge.stopped{background:var(--red-bg);color:var(--red)}
.service-card .action-link{display:inline-flex;align-items:center;gap:4px;margin-top:8px;font-size:12px;color:var(--blue);text-decoration:none;font-weight:500}
.service-card .action-link:hover{text-decoration:underline}

/* provider table */
.table-wrap{overflow-x:auto;border-radius:var(--radius);border:1px solid var(--border)}
.provider-table{width:100%;border-collapse:collapse;background:var(--surface);min-width:500px}
.provider-table th{padding:10px 14px;text-align:left;font-size:10px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:0.8px;background:var(--surface2);border-bottom:1px solid var(--border)}
.provider-table td{padding:10px 14px;font-size:13px;border-bottom:1px solid var(--border)}
.provider-table tr:last-child td{border-bottom:none}
.provider-table tr:hover td{background:rgba(255,255,255,0.02)}
.provider-table .mono{font-family:'JetBrains Mono',monospace;font-size:12px}

/* status badge reused */
.status-badge{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:600;padding:3px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:0.3px}
.status-badge.running{background:var(--green-bg);color:var(--green)}
.status-badge.stopped{background:var(--red-bg);color:var(--red)}

/* env grid */
.env-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px}
.env-item{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 14px;font-size:12px;transition:border-color .2s}
.env-item:hover{border-color:var(--border2)}
.env-item .key{color:var(--text3);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:0.3px;margin-bottom:2px}
.env-item .val{color:var(--text);font-family:'JetBrains Mono',monospace;font-size:11px;word-break:break-all}

/* quick links */
.links{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 6px}
.links a{display:inline-flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px 14px;font-size:13px;color:var(--text);text-decoration:none;transition:all .2s}
.links a:hover{background:var(--surface2);border-color:var(--blue);color:var(--blue);transform:translateY(-1px)}

/* footer */
.footer{text-align:center;padding:32px 0 0;font-size:12px;color:var(--text3)}
.footer a{color:var(--blue);text-decoration:none}
.footer a:hover{text-decoration:underline}

/* ─── RESPONSIVE ─── */
@media(min-width:769px){
  .menu-btn{display:flex}
  .drawer-overlay{display:none}
  .drawer{transform:translateX(0);box-shadow:none!important}
  .drawer-close{display:none}
  .main-content.shifted{margin-left:var(--drawer-width)}
}
@media(max-width:768px){
  .menu-btn{display:flex}
  .drawer{box-shadow:4px 0 40px rgba(0,0,0,0.4)}
  .drawer.open{transform:translateX(0)}
  .main-content.shifted{margin-left:0}
  .summary{grid-template-columns:repeat(2,1fr)}
  .header h1{font-size:16px}
  .header h1 span{display:none}
  .header-right .proot-label{display:none}
  .header-time{margin-right:4px}
  .refresh-btn{padding:4px 8px;font-size:11px}
  .container{padding:0 14px 40px}
  .grid{grid-template-columns:1fr}
  .env-grid{grid-template-columns:1fr 1fr}
  .links a{font-size:12px;padding:6px 10px}
}
@media(max-width:480px){
  .summary{grid-template-columns:repeat(2,1fr);gap:8px}
  .summary .card{padding:12px 14px}
  .summary .card .num{font-size:22px}
  .header{padding:0 0 12px;height:56px}
  .header-right{gap:6px}
  .env-grid{grid-template-columns:1fr}
  .provider-table{min-width:auto;font-size:12px}
  .provider-table th,.provider-table td{padding:8px 10px}
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
      <div class="drawer-logo-icon">◉</div>
      <span class="drawer-logo-text">ZES System</span>
    </div>
    <button class="drawer-close" onclick="closeDrawer()">✕</button>
  </div>
  <nav class="drawer-nav" id="drawerNav">
    <div class="drawer-section-title">Quick Links</div>
    <a class="drawer-link" href="http://localhost:20128" target="_blank"><span class="dl-icon">🌐</span> 9Router Dashboard</a>
    <a class="drawer-link" href="http://localhost:8787" target="_blank"><span class="dl-icon">🤖</span> Hermes WebUI</a>
    <a class="drawer-link" href="http://localhost:5900" target="_blank"><span class="dl-icon">⚡</span> Codex Server</a>
    <a class="drawer-link" href="http://localhost:7173" target="_blank"><span class="dl-icon">🖥</span> Web Terminal</a>
    <a class="drawer-link" href="https://cmdop.com" target="_blank"><span class="dl-icon">🦀</span> OpenClaw Docs</a>
    <a class="drawer-link" href="http://localhost:9876" target="_blank"><span class="dl-icon">🔮</span> OpenCode Server</a>
    <a class="drawer-link" href="https://cmdop.com" target="_blank"><span class="dl-icon">📡</span> CMDOP Fleet</a>
    <a class="drawer-link" href="https://composio.dev" target="_blank"><span class="dl-icon">📬</span> Composio Gmail</a>
    <a class="drawer-link" href="#" onclick="document.getElementById('gmail-status').scrollIntoView();closeDrawer();return false"><span class="dl-icon">✉️</span> Gmail Tool</a>
    <a class="drawer-link" href="#" onclick="document.getElementById('services').scrollIntoView();closeDrawer();return false"><span class="dl-icon">🌍</span> Browser CDP</a>
    <div class="drawer-section-title">Services</div>
    <a class="drawer-link" href="#" onclick="scrollToSection('services');closeDrawer();return false"><span class="dl-icon">📡</span> All Services</a>
    <a class="drawer-link" href="#" onclick="scrollToSection('providers');closeDrawer();return false"><span class="dl-icon">🔌</span> 9Router Providers</a>
    <a class="drawer-link" href="#" onclick="scrollToSection('env');closeDrawer();return false"><span class="dl-icon">⚙</span> Environment</a>
  </nav>
  <div class="drawer-footer" id="drawerFooter">
    <div class="df-row"><span>Version</span><span class="df-val">v2.0</span></div>
    <div class="df-row" id="dfUptime"><span>Uptime</span><span class="df-val">—</span></div>
  </div>
</div>

<!-- ─── MAIN CONTENT ─── -->
<div class="main-content" id="mainContent">
<div class="container">
  <header class="header">
    <div class="header-left">
      <button class="menu-btn" onclick="toggleDrawer()" aria-label="Toggle menu">☰</button>
      <div class="z-logo-wrap"><button class="z-logo-btn">Z</button></div>
      <h1><span class="zes-accent">ZES</span> <span>Control Center</span></h1>
    </div>
    <div class="header-right">
      <span class="proot-label"><span class="status-dot" id="prootDot"></span><span id="prootName">—</span></span>
      <span class="header-time" id="headerTime"></span>
      <button class="refresh-btn" onclick="location.reload()">↻</button>
    </div>
  </header>

  <div id="app"><!-- injected by JS --></div>
</div>
</div>

<script>
const DATA = __DATA__;

let drawerOpen = false;

function toggleDrawer() {
  drawerOpen ? closeDrawer() : openDrawer();
}
function openDrawer() {
  drawerOpen = true;
  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawerOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeDrawer() {
  drawerOpen = false;
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('open');
  document.body.style.overflow = '';
}
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({behavior:'smooth', block:'start'});
}

function render(d) {
  const running = d.services.filter(s=>s.status==='running').length;
  const total = d.services.length;
  const stopped = total - running;

  // header info
  document.getElementById('prootDot').className = 'status-dot ' + (d.env.proot_distro && d.env.proot_distro !== 'none' ? 'green' : 'red');
  document.getElementById('prootName').textContent = (d.env.proot_distro && d.env.proot_distro !== 'none') ? d.env.proot_distro : 'no proot';
  document.getElementById('headerTime').textContent = new Date(d.timestamp).toLocaleTimeString();

  // drawer footer
  const dfu = document.getElementById('dfUptime');
  if (dfu) dfu.querySelector('.df-val').textContent = d.env.uptime || '—';

  // service cards
  let cards = d.services.map(s => {
    const cls = s.status === 'running' ? 'running' : 'stopped';
    const http = s.http ? `<span style="font-size:11px;color:var(--text3);font-family:'JetBrains Mono',monospace">HTTP ${s.http}</span>` : '';
    const link = s.url ? `<a href="${s.url}" target="_blank" class="action-link">Open →</a>` : '';
    return `<div class="service-card ${cls}">
      <div class="top">
        <div class="icon">${s.icon}</div>
        <span class="status-badge ${cls}">● ${s.status}</span>
      </div>
      <div class="name">${s.name}</div>
      <div class="port">:${s.port} ${http}</div>
      <div class="desc">${s.desc}</div>
      ${link}
    </div>`;
  }).join('');

  let providers = d._providers || [];
  let provRows = providers.map(p => {
    const isRunning = p.active && (p.status === 'active' || p.status === 'unknown');
    const typeLabel = p.type;
    const prefix = p.prefix || '-';
    const url = p.baseUrl || '-';
    const shortUrl = url.length > 50 ? url.substring(0, 47)+'...' : url;
    return `<tr><td style="font-weight:600">${p.name}<br><span style="font-size:11px;color:var(--text3)">${typeLabel}</span></td><td style="color:var(--text3);font-family:'JetBrains Mono',monospace;font-size:12px">${prefix}</td><td class="mono" style="color:var(--text3);font-size:12px" title="${url}">${shortUrl}</td><td><span class="status-badge ${isRunning?'running':'stopped'}">● ${isRunning?'active':p.status}</span></td><td style="font-size:12px;color:var(--text2)">${p.proxy || 'direct'}</td></tr>`;
  }).join('');
  provRows = provRows || '<tr><td colspan="5" style="text-align:center;color:var(--text3);padding:20px">No custom providers configured</td></tr>';

  let envItems = Object.entries(d.env || {}).map(([k,v]) => `<div class="env-item"><div class="key">${k}</div><div class="val">${v}</div></div>`).join('');

  document.getElementById('app').innerHTML = `
    <div class="summary">
      <div class="card"><div class="num" style="color:var(--green)">${running}</div><div class="label">Running</div><div class="sub">services active</div></div>
      <div class="card"><div class="num" style="color:var(--red)">${stopped}</div><div class="label">Stopped</div><div class="sub">need attention</div></div>
      <div class="card"><div class="num" style="color:var(--blue)">${total}</div><div class="label">Total</div><div class="sub">monitored services</div></div>
      <div class="card"><div class="num" style="color:var(--amber)">${d._provider_active || providers.filter(p => p.active && (p.status === "active" || p.status === "unknown")).length}</div><div class="label">Providers</div><div class="sub">${d._provider_count || providers.length} total in 9router</div></div>
    </div>

    <div class="links">
      <a href="http://localhost:20128" target="_blank">🌐 9Router Dashboard</a>
      <a href="http://localhost:8787" target="_blank">🤖 Hermes WebUI</a>
      <a href="http://localhost:5900" target="_blank">⚡ Codex Server</a>
      <a href="http://localhost:7173" target="_blank">🖥 Terminal</a>
      <a href="https://cmdop.com" target="_blank">🦀 OpenClaw</a>
      <a href="http://localhost:9876" target="_blank">🔮 OpenCode</a>
      <a href="https://cmdop.com" target="_blank">📡 CMDOP</a>
      <a href="https://composio.dev" target="_blank">📬 Composio</a>
      <a href="https://cmdop.com" target="_blank">☁️ CMDOP Cloud</a>
      <a href="https://freellm.net" target="_blank">🆓 Free APIs</a>
    </div>

    <div class="section-title" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
      <span>📡 Services</span>
      <div class="refresh-controls" style="display:flex;align-items:center;gap:8px;font-size:13px">
        <span class="refresh-indicator" id="refreshIndicator" style="color:var(--text3);font-size:11px"></span>
        <button onclick="refreshNow()" style="background:var(--surface2);border:1px solid var(--border);color:var(--text2);padding:4px 10px;border-radius:6px;cursor:pointer;font-size:12px">⟳ Refresh</button>
        <select id="refreshRate" onchange="setRefreshRate(this.value)" style="background:var(--surface2);border:1px solid var(--border);color:var(--text2);padding:4px 6px;border-radius:6px;font-size:12px">
          <option value="5000">5s</option>
          <option value="10000" selected>10s</option>
          <option value="30000">30s</option>
          <option value="60000">60s</option>
          <option value="0">Pause</option>
        </select>
      </div>
    </div>
    <div class="section-title" id="services">📡 Services</div>
    <div class="grid">${cards}</div>

    <div class="section-title" id="uptime">📈 Uptime History (last 2h)</div>
    <div class="history-chart" id="historyChart" style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;margin-bottom:20px;overflow-x:auto">
      <div id="sparklines" style="min-height:80px;display:flex;align-items:center;justify-content:center;color:var(--text3);font-size:13px">Loading history…</div>
    </div>

    <div class="section-title" id="providers">🔌 AI Providers</div>
    <div class="table-wrap"><table class="provider-table">
      <tr><th>Name</th><th>Prefix</th><th>Endpoint</th><th>Status</th><th>Proxy</th></tr>
      ${provRows}
    </table></div>

    <div class="section-title" id="env">⚙ Environment</div>
    <div class="env-grid">${envItems}</div>

    <div class="footer">
      Updated ${new Date(d.timestamp).toLocaleString()} ·
      <a href="https://9router.com" target="_blank">9router.com</a> ·
      Hermes Agent · OpenCode Zen
    </div>
  `;

  // handle drawer shift on desktop
  const mc = document.getElementById('mainContent');
  if (window.innerWidth >= 769) {
    mc.classList.add('shifted');
  } else {
    mc.classList.remove('shifted');
  }
}

render(DATA);
window.addEventListener('resize', () => {
  const mc = document.getElementById('mainContent');
  if (window.innerWidth >= 769) {
    mc.classList.add('shifted');
  } else {
    mc.classList.remove('shifted');
    if (drawerOpen) closeDrawer();
  }
});

// Refresh controls
let refreshTimer = null;
let refreshInterval = parseInt(localStorage.getItem('dashboardRefresh') || '10000');

function setRefreshRate(ms) {
  ms = parseInt(ms);
  refreshInterval = ms;
  localStorage.setItem('dashboardRefresh', ms);
  if (refreshTimer) clearInterval(refreshTimer);
  if (ms > 0) {
    refreshTimer = setInterval(() => fetchStatus(), ms);
    document.getElementById('refreshIndicator').textContent = 'Auto: ' + (ms/1000) + 's';
  } else {
    document.getElementById('refreshIndicator').textContent = 'Paused';
  }
}

function refreshNow() {
  fetchStatus();
}

function fetchStatus() {
  fetch('/api/status').then(r=>r.json()).then(d=>{render(d);fetchHistory();}).catch(()=>{});
}

function fetchHistory() {
  fetch('/api/history').then(r=>r.json()).then(h=>renderSparklines(h)).catch(()=>{});
}

function renderSparklines(history) {
  if (!history || history.length < 2) {
    document.getElementById('sparklines').innerHTML = '<span style="color:var(--text3);font-size:13px">Not enough data yet</span>';
    return;
  }
  // Identify services that exist in history
  const svcIds = Object.keys(history[0].services || {});
  // Filter to port-based services only (skip pkg/bin ones)
  const relevant = svcIds.filter(id => ['codex','ttyd','socat','hermes','r9','tor','sshd','opencode'].includes(id));
  
  let html = '<div style="display:flex;flex-wrap:wrap;gap:12px">';
  for (const id of relevant) {
    const svc = (DATA.services || []).find(s => s.id === id);
    if (!svc) continue;
    const values = history.map(h => h.services?.[id]?.tcp ? 1 : 0);
    const width = Math.max(values.length * 3, 60);
    const height = 30;
    const points = values.map((v, i) => `${i * 3},${height - v * height}`).join(' ');
    html += `<div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px;min-width:140px">`;
    html += `<div style="font-size:12px;font-weight:600;margin-bottom:4px">${svc.icon} ${svc.name}</div>`;
    html += `<svg width="${width}" height="${height}" style="display:block">`;
    // Fill area under line
    const areaPoints = `0,${height} ${points} ${width},${height}`;
    html += `<polygon points="${areaPoints}" fill="${values[values.length-1] ? 'rgba(34,214,134,0.15)' : 'rgba(255,84,112,0.15)'}" />`;
    html += `<polyline points="${points}" fill="none" stroke="${values[values.length-1] ? 'var(--green)' : 'var(--red)'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />`;
    // Status dot
    const lastVal = values[values.length-1];
    html += `<circle cx="${(values.length-1)*3}" cy="${height - lastVal*height}" r="2.5" fill="${lastVal ? 'var(--green)' : 'var(--red)'}" />`;
    html += `</svg>`;
    html += `<div style="font-size:10px;color:var(--text3);margin-top:2px">${lastVal ? 'Up' : 'Down'} · ${values.filter(v=>v).length}/${values.length} samples</div>`;
    html += `</div>`;
  }
  html += '</div>';
  document.getElementById('sparklines').innerHTML = html;
}

// Init refresh rate from localStorage
setTimeout(() => {
  const sel = document.getElementById('refreshRate');
  if (sel) {
    const saved = localStorage.getItem('dashboardRefresh');
    if (saved) { sel.value = saved; }
    setRefreshRate(sel.value);
  }
  fetchHistory();
}, 100);

// Override the default interval
if (refreshTimer) clearInterval(refreshTimer);
</script>
</body>
</html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            data = get_status_with_providers()
            _log_status(data)
            return self._json(data)
        if self.path == "/api/history":
            return self._json(_load_history() or [])
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        data = get_status_with_providers()

        # Fetch provider info from 9router (all connections + openai-compatible nodes)
        try:
            req = urllib.request.Request("http://localhost:20128/api/providers")
            req.add_header("x-9r-cli-token", _cli_token())
            with urllib.request.urlopen(req, timeout=3) as r:
                pdata = json.loads(r.read())
                all_conns = pdata.get("connections", [])
            req2 = urllib.request.Request("http://localhost:20128/api/provider-nodes")
            req2.add_header("x-9r-cli-token", _cli_token())
            with urllib.request.urlopen(req2, timeout=3) as r2:
                nodes = json.loads(r2.read()).get("nodes", [])
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
        # Derive counts
        data["_provider_count"] = len(data.get("_providers", []))
        data["_provider_active"] = len([p for p in data.get("_providers", []) if p.get("active") and p.get("status") in ("active", "unknown")])

        self.wfile.write(PAGE.replace("__DATA__", json.dumps(data)).encode())
        self.wfile.write(b"<!-- live reload -->")

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

def _cli_token():
    try:
        d = os.path.expanduser("~/.9router")
        mid = open(d + "/machine-id").read().strip()
        sec = open(d + "/auth/cli-secret").read().strip()
        import hashlib
        return hashlib.sha256((mid + "9r-cli-auth" + sec).encode()).hexdigest()[:16]
    except Exception:
        return ""

def get_status_with_providers():
    services = []
    for svc in SERVICES:
        if "pkg" in svc:
            try:
                import importlib.metadata as md; md.version(svc["pkg"])
                available = True
            except Exception:
                available = False
            services.append({**svc, "tcp": available, "http": None, "status": "running" if available else "stopped"})
        elif "bin" in svc:
            try:
                import subprocess, shutil
                available = shutil.which(svc["bin"]) is not None
                if not available:
                    for _home_bin in [os.path.expanduser("~/.local/bin"), os.path.expanduser("~/bin")]:
                        _bp = os.path.join(_home_bin, svc["bin"])
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

if __name__ == "__main__":
    srv = http.server.HTTPServer((HOST, PORT), Handler)
    print(f"🚀 ZES Control Center → http://{HOST}:{PORT}")
    print(f"   API: http://{HOST}:{PORT}/api/status")
    srv.serve_forever()
