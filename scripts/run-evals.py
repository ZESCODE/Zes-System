#!/usr/bin/env python3
"""ZES eval runner — run evals and output JSON results."""
import json, socket, subprocess, sys, os
from datetime import datetime, timezone

EVALS_DIR = os.path.expanduser("~/.zes/evals")
os.makedirs(EVALS_DIR, exist_ok=True)

def tcp_open(host, port, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except:
        return False

def http_status(url, timeout=3):
    import urllib.request
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        return r.status
    except Exception as e:
        if hasattr(e, "code"):
            return e.code
        return None

def svc_running(name):
    svc_dir = f"/data/data/com.termux/files/usr/var/service/{name}"
    if not os.path.isdir(svc_dir):
        return False
    try:
        r = subprocess.run(["sv", "status", svc_dir], capture_output=True, text=True, timeout=5)
        return "run:" in r.stdout
    except:
        return False

EVALS = {
    "service-health": [
        {"name": "9Router", "check": lambda: tcp_open("127.0.0.1", 20128)},
        {"name": "Dashboard", "check": lambda: http_status("http://localhost:8083/api/status") == 200},
        {"name": "Tor SOCKS5", "check": lambda: tcp_open("127.0.0.1", 9050)},
        {"name": "Codex", "check": lambda: tcp_open("127.0.0.1", 5900)},
        {"name": "ttyd", "check": lambda: tcp_open("127.0.0.1", 7173)},
        {"name": "Chrome CDP", "check": lambda: tcp_open("127.0.0.1", 9222)},
        {"name": "MCP Server", "check": lambda: tcp_open("127.0.0.1", 5901)},
        {"name": "Hermes", "check": lambda: svc_running("hermes-gateway")},
    ],
}

def run_eval(name):
    checks = EVALS.get(name, [])
    results = []
    for c in checks:
        try:
            passed = c["check"]()
        except Exception:
            passed = False
        results.append({"name": c["name"], "pass": passed})

    passed_count = sum(1 for r in results if r["pass"])
    return {
        "eval": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "summary": {
            "pass": passed_count,
            "fail": len(results) - passed_count,
            "total": len(results),
            "pass_rate": round(passed_count / len(results), 2) if results else 0
        }
    }

if __name__ == "__main__":
    eval_name = sys.argv[1] if len(sys.argv) > 1 else "service-health"
    output = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    result = run_eval(eval_name)

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Results written to {output}")
    else:
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["summary"]["fail"] == 0 else 1)
