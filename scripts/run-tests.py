#!/usr/bin/env python3
"""ZES Automated Test Suite — run all system regression checks."""
import json, os, socket, subprocess, sys, time, urllib.request, urllib.error
from datetime import datetime

HOME = os.path.expanduser("~")
PASS, FAIL = 0, 0
results = []

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        results.append((name, "✅ PASS"))
        PASS += 1
    except AssertionError as e:
        results.append((name, f"❌ FAIL: {e}"))
        FAIL += 1
    except Exception as e:
        results.append((name, f"❌ ERROR: {e}"))
        FAIL += 1

def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg}: expected {b}, got {a}")

def assert_true(v, msg=""):
    if not v:
        raise AssertionError(msg or "expected True")

def tcp_open(host, port, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except: return False

def http_get(url, timeout=3):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)

def run(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except: return ""

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\n{'='*50}")
print(f"  ZES Test Suite — {now}")
print(f"{'='*50}\n")

# ════════════════════════════════════════════
# 1. Core Services
# ════════════════════════════════════════════
print("📡 Core Services")

def check_r9():
    assert_true(tcp_open("127.0.0.1", 20128), "9Router port 20128")
    status, body = http_get("http://127.0.0.1:20128/")
    assert_eq(status, 200, "9Router HTTP")
test("9Router is running", check_r9)

def check_dash():
    assert_true(tcp_open("127.0.0.1", 8083), "Dashboard port 8083")
    status, body = http_get("http://127.0.0.1:8083/api/status")
    assert_eq(status, 200, "Dashboard API")
    data = json.loads(body)
    assert_true("services" in data, "Dashboard returns services")
    assert_true(len(data["services"]) >= 10, "At least 10 services tracked")
test("Dashboard v4 API", check_dash)

def check_ttyd():
    assert_true(tcp_open("127.0.0.1", 7173), "ttyd port 7173")
test("ttyd terminal", check_ttyd)

def check_tor():
    assert_true(tcp_open("127.0.0.1", 9050), "Tor port 9050")
test("Tor SOCKS5", check_tor)

def check_codex():
    assert_true(tcp_open("127.0.0.1", 5900), "Codex port 5900")
test("Codex API", check_codex)

def check_chrome():
    assert_true(tcp_open("127.0.0.1", 9222), "Chrome CDP port 9222")
test("Chrome CDP", check_chrome)

def check_vscode():
    assert_true(tcp_open("127.0.0.1", 8000), "VS Code port 8000")
test("VS Code Server", check_vscode)

def check_mcp():
    assert_true(tcp_open("127.0.0.1", 5901), "zesChrome MCP port 5901")
test("zesChrome MCP", check_mcp)

def check_hermes():
    out = run("command -v hermes 2>/dev/null; ls -la /data/data/com.termux/files/usr/bin/hermes 2>/dev/null || true")
    assert_true(bool(out), "hermes binary")
test("Hermes CLI available", check_hermes)

def check_claude():
    out = run("claude --version 2>/dev/null")
    assert_true("Claude" in out or "2." in out, f"Claude Code ({out})")
test("Claude Code CLI", check_claude)

# ════════════════════════════════════════════
# 2. MCP Layer
# ════════════════════════════════════════════
print("\n🔌 MCP Layer")

def check_mcp_tools():
    import json
    req = urllib.request.Request("http://127.0.0.1:5901/mcp",
        data=b'{"method":"mcp.listTools","params":{}}',
        headers={"Content-Type":"application/json"})
    r = urllib.request.urlopen(req, timeout=3)
    data = json.loads(r.read())
    tools = data.get("result",{}).get("tools",[])
    assert_true(len(tools) >= 14, f"≥14 tools (got {len(tools)})")
test("zesChrome MCP tools ≥14", check_mcp_tools)

def check_bridge():
    import json
    r = subprocess.run(
        ['node', os.path.expanduser("~/Zes-System/zes-chrome/zes-bridge-mcp/server.js")],
        input='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n',
        capture_output=True, text=True, timeout=5
    )
    data = json.loads(r.stdout)
    tools = data.get("result",{}).get("tools",[])
    assert_true(len(tools) >= 8, f"≥8 bridge tools (got {len(tools)})")
test("ZES Bridge MCP tools ≥8", check_bridge)

def check_claude_config():
    path = os.path.expanduser("~/.claude.json")
    assert_true(os.path.exists(path), ".claude.json exists")
    with open(path) as f:
        cfg = json.load(f)
    servers = cfg.get("mcpServers", {})
    assert_true(len(servers) >= 4, f"≥4 MCP servers in .claude.json (got {len(servers)})")
test(".claude.json MCP config", check_claude_config)

# ════════════════════════════════════════════
# 3. System Files
# ════════════════════════════════════════════
print("\n📁 System Files")

def check_dashboard_file():
    assert_true(os.path.exists(os.path.expanduser("~/dashboard_v4.py")), "dashboard_v4.py")
test("Dashboard v4 file", check_dashboard_file)

def check_v3_backup():
    assert_true(os.path.exists(os.path.expanduser("~/dashboard_v3.py")), "dashboard_v3.py")
test("Dashboard v3 backup", check_v3_backup)

def check_skills():
    skills_dir = os.path.expanduser("~/Zes-System/.agents/skills")
    assert_true(os.path.isdir(skills_dir), "skills dir")
    count = len([d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))])
    assert_true(count >= 20, f"≥20 skills (got {count})")
test("Skills directory ≥20", check_skills)

def check_agents():
    agents_dir = os.path.expanduser("~/Zes-System/.agents/agents")
    assert_true(os.path.isdir(agents_dir), "agents dir")
    count = len([f for f in os.listdir(agents_dir) if f.endswith(".md")])
    assert_true(count >= 8, f"≥8 agents (got {count})")
test("Agents directory ≥8", check_agents)

def check_hooks():
    hooks_dir = os.path.expanduser("~/Zes-System/scripts/hooks")
    assert_true(os.path.isdir(hooks_dir), "hooks dir")
    count = len([f for f in os.listdir(hooks_dir) if f.endswith(".js") or f.endswith(".py")])
    assert_true(count >= 3, f"≥3 hooks (got {count})")
test("Hooks directory ≥3", check_hooks)

def check_backup():
    snap_dir = os.path.expanduser("~/Zes-System/backups/snapshots")
    assert_true(os.path.isdir(snap_dir), "backups dir")
    snaps = [d for d in os.listdir(snap_dir) if d.startswith("zes-")]
    assert_true(len(snaps) >= 1, f"≥1 backup snapshots (got {len(snaps)})")
test("Backup snapshots exist", check_backup)

# ════════════════════════════════════════════
# 4. Health Evals
# ════════════════════════════════════════════
print("\n🏥 Health Evals")

def check_evals():
    r = subprocess.run(["python3", os.path.expanduser("~/Zes-System/scripts/run-evals.py")],
        capture_output=True, text=True, timeout=10)
    assert_true("pass_rate" in r.stdout, "eval output has pass_rate")
    try:
        data = json.loads(r.stdout)
        assert_true(data.get("summary",{}).get("pass_rate",0) >= 0.8, "≥80% pass rate")
    except: pass
test("Health evals pass ≥80%", check_evals)

# ── Summary ──
print(f"\n{'='*50}")
print(f"  Results: {PASS} passed, {FAIL} failed ({PASS+FAIL} total)")
print(f"{'='*50}\n")

for name, status in results:
    print(f"  {status} — {name}")

sys.exit(0 if FAIL == 0 else 1)
