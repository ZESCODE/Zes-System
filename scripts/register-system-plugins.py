#!/usr/bin/env python3
"""Auto-register all ZES system plugins with dashboard on startup"""
import json
import urllib.request
import time
import socket

API = "http://127.0.0.1:8083/api/plugins/register"
PLUGINS = [
    {
        "name": "Agent Orchestration Pipeline",
        "version": "1.0",
        "description": "Runs tasks through Planner→Architect→Coder→Reviewer→Tester stages",
        "widgets": [{"id": "run", "name": "Run Pipeline"}, {"id": "status", "name": "Pipeline Status"}],
        "endpoints": {}
    },
    {
        "name": "Security Supply Chain Scanner",
        "version": "1.0",
        "description": "Scans npm/pip deps, credentials, permissions, config leaks",
        "widgets": [{"id": "scan", "name": "Run Scan"}, {"id": "report", "name": "View Report"}],
        "endpoints": {}
    },
    {
        "name": "Session Kanban",
        "version": "1.0",
        "description": "Persistent task board linked to agent conversations",
        "widgets": [{"id": "board", "name": "Kanban Board"}],
        "endpoints": {"board": "http://127.0.0.1:8084/api/kanban/tasks"}
    },
    {
        "name": "Cross-Harness Deployer",
        "version": "1.0",
        "description": "Export ZES agents to Cursor, Gemini, CodeBuddy formats",
        "widgets": [{"id": "deploy", "name": "Deploy Agents"}],
        "endpoints": {}
    }
]

def register(plugin):
    data = json.dumps(plugin).encode()
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=5)
        result = json.loads(r.read())
        print(f"  ✅ {plugin['name']} → {result.get('id', 'ok')}")
        return True
    except Exception as e:
        print(f"  ❌ {plugin['name']}: {e}")
        return False

def main():
    print("🔌 Registering ZES system plugins...")
    # Wait for dashboard to be ready
    for i in range(10):
        try:
            urllib.request.urlopen("http://127.0.0.1:8083/api/plugins/ping", timeout=2)
            break
        except:
            time.sleep(1)
    else:
        print("  Dashboard not available, skipping plugin registration")
        return
    
    for plugin in PLUGINS:
        register(plugin)
    print("Done")

if __name__ == "__main__":
    main()
