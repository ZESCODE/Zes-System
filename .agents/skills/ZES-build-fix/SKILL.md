---
category: Review

name: zes-build-fix
description: Detect and fix build/startup errors in ZES services — dashboard, agent UI, MCP servers, Claude Code proxy.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---


# ZES Build Fix

Diagnose and resolve service start failures, import errors, port conflicts, and config issues.

## When to Activate

- Service fails to start (sv status shows down)
- ImportError or ModuleNotFoundError in Python/Node
- Port already in use errors
- runit supervision failures

## Diagnosis Steps

### 1. Check Service Status
```bash
sv status /data/data/com.termux/files/usr/var/service/<name>
```

### 2. Read Service Logs
```bash
tail -30 /data/data/com.termux/files/home/.svlog/<name>/current
```

### 3. Common ZES Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: No module named 'x'` | Missing pip/npm dependency | `pip install x` or `npm install x` |
| `Address already in use` | Port conflict | `lsof -i :PORT` then kill or change port |
| `SyntaxError` in dashboard | Bad Python merge | Check recent edits to dashboard_v4.py |
| Node `ERR_MODULE_NOT_FOUND` | Missing import path | Check relative imports in server.js |
| `sv: warning: unable to open supervise/ok` | New service, needs restart | `sv restart <name>` |

### 4. Fix and Verify
```bash
# Fix the issue, then:
sv restart <service>
sleep 2
sv status <service>
curl -s http://localhost:<port>/  # Verify response
```

