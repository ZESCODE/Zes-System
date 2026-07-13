---
name: zes-e2e
description: End-to-end testing for ZES services — verify dashboard renders, APIs respond, Claude Code runs, and 9Router routes.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES End-to-End Testing

Full-stack integration tests for ZES system. Verifies all services work together.

## When to Activate

- After deploying system-wide changes
- After restarting multiple services
- Before claiming a task is complete
- When debugging connectivity issues

## Test Suite

### 1. Dashboard API
```bash
# Verify all API endpoints
curl -s http://localhost:8083/api/status | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'Services: {len(d["services"])}, Providers: {len(d["providers"])}')"
curl -s http://localhost:8083/api/status/logs | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'Log entries: {len(d)}')"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/events
```

### 2. Agent UI
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8084/
curl -s http://localhost:8084/api/kanban/tasks | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'Kanban columns: {len(d)}')"
```

### 3. Claude Code
```bash
claude --version
curl -s -o /dev/null -w "%{http_code}" http://localhost:5905/v1/me
```

### 4. 9Router
```bash
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
curl -s -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'Providers: {len(d.get("connections",[]))}')"
```

### 5. Core Services
```bash
for svc in dashboard8083 agent-ui agent-dash-web ttyd tor chromium-cdp vscode-server zeschrome-mcp; do
    sv check /data/data/com.termux/files/usr/var/service/$svc
done
```

