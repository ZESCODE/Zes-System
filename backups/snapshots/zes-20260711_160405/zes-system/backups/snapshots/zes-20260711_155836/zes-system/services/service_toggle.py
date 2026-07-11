#!/usr/bin/env python3
"""ZES Service Toggle — runsv-aware service management with health checks.
Usage: python3 service_toggle.py list|start|stop|restart|status [service_name]
"""
import json, os, subprocess, sys, time
from pathlib import Path

SVDIR = Path("/data/data/com.termux/files/usr/var/service")

SERVICES = {
    "dashboard": {"name": "ZES Dashboard", "port": 8083, "service": "dashboard8083"},
    "hermes": {"name": "Hermes Gateway", "port": 8787, "service": "hermes-gateway"},
    "opencode": {"name": "OpenCode", "port": 9876, "service": "opencode"},
    "vscode": {"name": "VS Code Server", "port": 8000, "service": "vscode-server"},
    "tor": {"name": "Tor Proxy", "port": 9050, "service": "tor"},
    "chromium": {"name": "Chrome CDP", "port": 9222, "service": "chromium-cdp"},
    "socat": {"name": "Socat Bridge", "port": 8090, "service": "socat"},
    "ttyd": {"name": "Web Terminal", "port": 7173, "service": "ttyd"},
    "zeschrome": {"name": "zesChrome MCP", "port": 5901, "service": "zeschrome-mcp"},
    "sshd": {"name": "SSH Server", "port": 8022, "service": "sshd"},
}

def sv_cmd(service, action):
    sv_path = SVDIR / service
    if not sv_path.exists():
        return f"Service {service} not found"
    result = subprocess.run(["sv", action, str(sv_path)], capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()

def check_port(port, timeout=1):
    import socket
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def list_services():
    results = []
    for sid, info in SERVICES.items():
        svc_path = SVDIR / info["service"]
        status = "down"
        if svc_path.exists():
            r = subprocess.run(["sv", "status", str(svc_path)], capture_output=True, text=True)
            if "run:" in r.stdout:
                status = "running"
        port_open = check_port(info["port"])
        results.append({"id": sid, "name": info["name"], "port": info["port"], "status": status, "port_open": port_open})
    return results

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    target = sys.argv[2] if len(sys.argv) > 2 else None
    
    if cmd == "list":
        for s in list_services():
            icon = "🟢" if s["status"] == "running" else "🔴"
            port_str = f":{s['port']}" if s["port_open"] else ""
            print(f"{icon} {s['name']:20s} {s['status']:8s} {port_str}")
    
    elif cmd in ("start", "stop", "restart"):
        for sid, info in SERVICES.items():
            if target and sid != target:
                continue
            print(f"{cmd} {info['name']}... ", end="")
            result = sv_cmd(info["service"], cmd)
            print(result)
    
    elif cmd == "status":
        for s in list_services():
            print(f"{s['status']:8s} | {s['name']:20s} | port {s['port']}")
    
    else:
        print(f"Usage: {sys.argv[0]} list|start|stop|restart|status [service_name]")
