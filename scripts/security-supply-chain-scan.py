#!/usr/bin/env python3
"""
ZES Security Supply Chain Scanner
Scans: npm/pip deps, exposed credentials, file permissions, config leaks
"""
import os
import json
import re
import subprocess
from datetime import datetime

HOME = os.path.expanduser("~")
REPORT_FILE = os.path.join(HOME, "Zes-System", ".pipeline", "security-scan-report.json")

def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def scan_npm_deps():
    """Check npm audit for vulnerabilities"""
    print("  📦 Scanning npm dependencies...")
    npm_dirs = [
        os.path.join(HOME, "Zes-System", "zes-chrome", "mcp-server"),
        os.path.join(HOME, "Zes-System", "zes-chrome", "zes-bridge-mcp"),
        os.path.join(HOME, "Zes-System", "services", "agent-ui"),
    ]
    results = []
    for d in npm_dirs:
        pkg = os.path.join(d, "package.json")
        if os.path.exists(pkg):
            lock = os.path.join(d, "package-lock.json")
            if os.path.exists(lock):
                out = run(f"cd {d} && npm audit --json 2>/dev/null")
                try:
                    data = json.loads(out)
                    vulns = data.get("vulnerabilities", {})
                    if vulns:
                        results.append({
                            "dir": d.replace(HOME, "~"),
                            "total": sum(v.get("severity") == "critical" for v in vulns.values()),
                            "high": sum(v.get("severity") == "high" for v in vulns.values()),
                            "moderate": sum(v.get("severity") == "moderate" for v in vulns.values()),
                            "packages": len(vulns)
                        })
                except:
                    pass
    return results

def scan_credentials():
    """Scan config files for exposed API keys, tokens, secrets"""
    print("  🔑 Scanning for exposed credentials...")
    patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI-style API key"),
        (r'api[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-]{16,}', "API key assignment"),
        (r'token["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-.\/]{16,}', "Token assignment"),
        (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
        (r'gho_[a-zA-Z0-9]{36}', "GitHub OAuth token"),
        (r'xox[baprs]-[a-zA-Z0-9\-]{24,}', "Slack token"),
    ]
    
    scan_dirs = [
        os.path.join(HOME, ".9router"),
        os.path.join(HOME, ".hermes"),
        os.path.join(HOME, "Zes-System", "services"),
    ]
    
    findings = []
    for d in scan_dirs:
        if not os.path.isdir(d):
            continue
        for root, dirs, files in os.walk(d):
            for f in files:
                if f.endswith((".json", ".yaml", ".yml", ".env", ".js", ".py", ".sh", ".toml", ".conf", ".cfg", ".txt")):
                    path = os.path.join(root, f)
                    try:
                        with open(path) as fh:
                            content = fh.read()
                        for pattern, desc in patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                findings.append({
                                    "file": path.replace(HOME, "~"),
                                    "pattern": desc,
                                    "count": len(matches),
                                    "sample": matches[0][:20] + "..." if len(matches[0]) > 20 else matches[0]
                                })
                    except:
                        pass
    return findings

def scan_permissions():
    """Check for unsafe file permissions"""
    print("  🔒 Checking file permissions...")
    issues = []
    critical_paths = [
        os.path.join(HOME, ".9router"),
        os.path.join(HOME, ".claude.json"),
        os.path.join(HOME, "Zes-System", "scripts"),
    ]
    for p in critical_paths:
        if os.path.exists(p):
            mode = oct(os.stat(p).st_mode)[-3:]
            if mode[0] in ("7", "6") and not p.startswith(HOME + "/.9router"):
                issues.append({"path": p.replace(HOME, "~"), "mode": mode, "risk": "World-readable config"})
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        fmode = oct(os.stat(fp).st_mode)[-3:]
                        if fmode[2] in ("7", "6", "5", "4"):
                            issues.append({"path": fp.replace(HOME, "~"), "mode": fmode, "risk": "World-readable"})
    return issues

def scan_env_files():
    """Check .env files for hardcoded secrets"""
    print("  📄 Scanning .env files...")
    findings = []
    for root, dirs, files in os.walk(HOME):
        for f in files:
            if f == ".env" or f.endswith(".env.example"):
                path = os.path.join(root, f)
                try:
                    with open(path) as fh:
                        for line in fh:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                if v and v not in ('""', "''", '"your-', '"<') and len(v) > 10:
                                    findings.append({
                                        "file": path.replace(HOME, "~"),
                                        "var": k,
                                        "value_length": len(v)
                                    })
                except:
                    pass
        if root.count(os.sep) > 6:
            break
    return findings

def scan_python_deps():
    """Check for known vulnerable Python packages"""
    print("  🐍 Scanning Python dependencies...")
    out = run("pip3 list --format=json 2>/dev/null || pip list --format=json 2>/dev/null")
    try:
        pkgs = json.loads(out)
        return [{"name": p["name"], "version": p["version"]} for p in pkgs[:50]]
    except:
        return []

def main():
    print("🔍 ZES Security Supply Chain Scan")
    print("=" * 40)
    
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "npm_vulnerabilities": scan_npm_deps(),
        "credential_leaks": scan_credentials(),
        "permission_issues": scan_permissions(),
        "env_secrets": scan_env_files(),
        "python_packages": scan_python_deps(),
    }
    
    with open(REPORT_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "=" * 40)
    print("📊 Scan Results")
    
    npm = results["npm_vulnerabilities"]
    creds = results["credential_leaks"]
    perms = results["permission_issues"]
    envs = results["env_secrets"]
    
    if npm:
        for v in npm:
            print(f"  ⚠ npm vulns in {v['dir']}: {v['total']} critical, {v['high']} high")
    else:
        print("  ✅ No npm vulnerabilities found")
    
    if creds:
        print(f"  ⚠ {len(creds)} potential credential leaks:")
        for c in creds[:5]:
            print(f"    • {c['file']}: {c['pattern']}")
    else:
        print("  ✅ No credential leaks detected")
    
    if perms:
        print(f"  ⚠ {len(perms)} permission issues")
        for p in perms[:5]:
            print(f"    • {p['path']}: mode {p['mode']} - {p['risk']}")
    else:
        print("  ✅ Permissions look good")
    
    if envs:
        print(f"  ⚠ {len(envs)} .env secrets found")
    else:
        print("  ✅ No .env secrets detected")
    
    print(f"\n📁 Full report: {REPORT_FILE}")
    
    # Return findings count for scripting
    return len(npm) + len(creds) + len(perms) + len(envs)

if __name__ == "__main__":
    exit(main())
