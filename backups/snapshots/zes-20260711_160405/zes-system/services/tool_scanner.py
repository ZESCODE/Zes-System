#!/usr/bin/env python3
"""ZES Tool Scanner — discover executables and runsv services."""
from __future__ import annotations
import json, os, stat, subprocess, sys
from pathlib import Path

BIN_DIRS = [
    Path("/data/data/com.termux/files/usr/bin"),
    Path.home() / ".local" / "bin",
]
OUTPUT = Path.home() / ".zes" / "discovered_tools.json"

def is_executable(path):
    try:
        return stat.S_ISREG(path.stat().st_mode) and (path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except: return False

def scan():
    tools = {}
    for d in BIN_DIRS:
        if not d.exists(): continue
        for f in d.iterdir():
            if is_executable(f):
                tools[f.name] = str(f)
    return tools

def scan_services():
    sv_dir = Path("/data/data/com.termux/files/usr/var/service")
    services = {}
    if sv_dir.exists():
        for sv in sv_dir.iterdir():
            if sv.is_dir() and not sv.name == "log":
                services[sv.name] = "sv" if (sv / "run").exists() else "unknown"
    return services

if __name__ == "__main__":
    tools = scan()
    services = scan_services()
    os.makedirs(OUTPUT.parent, exist_ok=True)
    data = {"tools": tools, "services": services, "tool_count": len(tools), "service_count": len(services)}
    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Scanned {len(tools)} tools, {len(services)} services → {OUTPUT}")
