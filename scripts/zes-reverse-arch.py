#!/usr/bin/env python3
"""
ZES Reverse-Architecture Tool
Analyzes ZES repos and generates architecture documentation.
Usage: python3 zes-reverse-arch.py [--output FILE] [--repo PATH]
"""
import os
import json
import sys
import subprocess
import re
from datetime import datetime

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
REPOS = {
    "Zes-System": os.path.join(HOME, "Zes-System"),
    "9router": os.path.join(HOME, "9router"),
    "zes-chrome": os.path.join(HOME, "Zes-System", "zes-chrome"),
}
OUTPUT_FILE = os.path.join(HOME, "Zes-System", "docs", "architecture.json")

def run(cmd, cwd=None):
    try:
        return subprocess.check_output(cmd, shell=True, cwd=cwd or HOME, 
                                        encoding="utf8", stderr=subprocess.STDOUT,
                                        timeout=30).strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output[:200]}"
    except Exception as e:
        return f"ERROR: {e}"

def analyze_service(service_dir, name):
    """Extract architecture from a service directory"""
    info = {
        "name": name,
        "path": service_dir,
        "language": "unknown",
        "entry_point": None,
        "dependencies": [],
        "endpoints": [],
        "components": [],
        "technologies": [],
    }
    
    # Detect language and entry point
    for entry in ["server.js", "index.js", "app.js", "main.py", "server.py", "app.py", "index.html"]:
        if os.path.isfile(os.path.join(service_dir, entry)):
            info["entry_point"] = entry
            info["language"] = "javascript" if entry.endswith(".js") else "python" if entry.endswith(".py") else "html"
            break
    
    # Read package.json or requirements
    pkg = os.path.join(service_dir, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg) as f:
                data = json.load(f)
            info["dependencies"] = list(data.get("dependencies", {}).keys())[:20]
            info["technologies"].extend(["node", "express"] if "express" in str(data) else ["node"])
        except: pass
    
    # Scan for port definitions
    for root, dirs, files in os.walk(service_dir):
        for fname in files:
            if fname.endswith((".js", ".py", ".ts")):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "rb") as f:
                        content = f.read().decode("utf8", errors="replace")
                    # Find PORT assignments
                    for m in re.finditer(r'PORT\s*=\s*(\d+)', content):
                        info["endpoints"].append({"file": fname, "port": int(m.group(1))})
                    # Find express route definitions
                    for m in re.finditer(r'\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content):
                        info["endpoints"].append({"method": m.group(1).upper(), "path": m.group(2), "file": fname})
                except: pass
    
    return info

def scan_all_services():
    """Scan all ZES services for architecture"""
    services = {}
    
    # Scan Zes-System services
    services_dir = os.path.join(HOME, "Zes-System", "services")
    if os.path.isdir(services_dir):
        for name in sorted(os.listdir(services_dir)):
            path = os.path.join(services_dir, name)
            if os.path.isdir(path):
                # Check if it has code files
                has_code = any(f.endswith((".js", ".py", ".ts", ".html")) 
                              for f in os.listdir(path))
                if has_code:
                    services[name] = analyze_service(path, name)
    
    # Scan runsv services
    sv_dir = "/data/data/com.termux/files/usr/var/service"
    if os.path.isdir(sv_dir):
        for name in sorted(os.listdir(sv_dir)):
            run_file = os.path.join(sv_dir, name, "run")
            if os.path.isfile(run_file):
                if name not in services:
                    try:
                        with open(run_file) as f:
                            content = f.read(500)
                        services[name] = {
                            "name": name,
                            "path": run_file,
                            "type": "runsv",
                            "command": content.strip()[:200],
                        }
                    except: pass
    
    return services

def build_architecture_doc(services):
    """Build the architecture document"""
    # Group services
    system = {"name": "ZES System", "version": "4.0", "services": [], "dataFlow": []}
    
    for name, info in sorted(services.items()):
        entry = {
            "id": name,
            "name": name.replace("-", " ").title(),
            "type": info.get("type", "service"),
            "language": info.get("language", "unknown"),
            "entry_point": info.get("entry_point", "N/A"),
            "port": info.get("port"),
            "technologies": info.get("technologies", []),
            "endpoints": info.get("endpoints", []),
        }
        system["services"].append(entry)
    
    # Add data flow based on port mappings
    port_map = {}
    for svc in system["services"]:
        for ep in svc.get("endpoints", []):
            if "port" in ep:
                port_map[ep["port"]] = svc["id"]
    
    # Reverse engineer data flows from run scripts
    sv_dir = "/data/data/com.termux/files/usr/var/service"
    if os.path.isdir(sv_dir):
        for name in sorted(os.listdir(sv_dir)):
            run_file = os.path.join(sv_dir, name, "run")
            if os.path.isfile(run_file):
                try:
                    with open(run_file) as f:
                        content = f.read()
                    # Find localhost references
                    for m in re.finditer(r'127\.0\.0\.1:(\d+)', content):
                        target_port = int(m.group(1))
                        if target_port in port_map:
                            system["dataFlow"].append({
                                "from": name,
                                "to": port_map[target_port],
                                "type": "http",
                                "via": f"localhost:{target_port}"
                            })
                except: pass
    
    # Add known flows
    known_flows = [
        ("dashboard8083", "r9", "http", "API calls to 9Router for provider status"),
        ("hermes-webui", "r9", "http", "Chat completion requests via 9Router"),
        ("agent-ui", "r9", "http", "AI chat via 9Router"),
        ("claude-proxy", "r9", "http", "Claude Code proxy to 9Router"),
        ("claude-dashboard", "r9", "http", "Team dashboard data via 9Router"),
        ("zes-router-proxy", "r9", "http", "Provider-specific proxy routing"),
    ]
    for frm, to, typ, desc in known_flows:
        if any(s["id"] == frm for s in system["services"]):
            system["dataFlow"].append({
                "from": frm, "to": to, "type": typ, "description": desc
            })
    
    # Add metadata
    system["generatedAt"] = datetime.now().isoformat()
    system["totalServices"] = len(system["services"])
    system["totalDataFlows"] = len(system["dataFlow"])
    
    return system

def generate_markdown(doc):
    """Generate markdown doc from architecture"""
    lines = [
        f"# ZES System Architecture (v{doc['version']})",
        f"",
        f"*Generated: {doc['generatedAt']}*",
        f"",
        f"## Overview",
        f"",
        f"- **{doc['totalServices']} services** across {len(REPOS)} repos",
        f"- **{doc['totalDataFlows']} data flows** between services",
        f"",
        f"## Services",
        f"",
        f"| Service | Type | Language | Entry Point |",
        f"|---------|------|----------|-------------|",
    ]
    for s in doc["services"]:
        lines.append(f"| {s['id']} | {s['type']} | {s['language']} | {s['entry_point']} |")
    
    lines.extend(["", "## Data Flow", ""])
    for d in doc["dataFlow"]:
        desc = d.get("description", d.get("via", ""))
        lines.append(f"- **{d['from']}** → **{d['to']}** ({d['type']}): {desc}")
    
    return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ZES Reverse-Architecture Tool")
    parser.add_argument("--output", "-o", default=OUTPUT_FILE, help="Output file path")
    parser.add_argument("--markdown", "-m", action="store_true", help="Also generate markdown")
    args = parser.parse_args()
    
    print("🔍 Scanning ZES services...")
    services = scan_all_services()
    print(f"   Found {len(services)} services")
    
    print("📐 Building architecture document...")
    doc = build_architecture_doc(services)
    
    # Save JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(doc, f, indent=2)
    print(f"   Saved: {args.output}")
    
    # Save markdown
    if args.markdown:
        md = generate_markdown(doc)
        md_file = args.output.replace(".json", ".md")
        with open(md_file, "w") as f:
            f.write(md)
        print(f"   Saved: {md_file}")
    
    print(f"\n📊 Summary:")
    print(f"   Services: {doc['totalServices']}")
    print(f"   Data Flows: {doc['totalDataFlows']}")
    print(f"   Repos scanned: {len(REPOS)}")
    
    return doc

if __name__ == "__main__":
    main()
