---
name: zes-dev-patterns
description: Combined coding standards, backend patterns, and API design for ZES services — Python dashboards, REST APIs, shell scripts, and service architecture.
---

# ZES Development Patterns

Coding standards, backend architecture, and API design patterns for ZES system services.

## When to Activate

- Writing or reviewing ZES service code (dashboard, agents, scripts)
- Designing new API endpoints for the dashboard or 9Router
- Refactoring existing code for maintainability
- Establishing coding conventions across ZES services

## Coding Standards

### Naming Conventions

```python
# PASS: Descriptive names
def get_service_status(service_id: str) -> dict: ...
SERVICE_PORT_MAP = {"r9": 20128, "hermes": 8787}
is_running = True

# FAIL: Unclear names
def proc(s): ...
d = {"r9": 20128}
flag = True
```

### Function Structure

```python
# PASS: Single responsibility, clear inputs/outputs
def check_service_health(service_name: str) -> dict:
    """Check if a runsv service is running and its port is open.
    Returns {"name": ..., "status": "running"|"stopped", "port": ...}
    """
    import subprocess, socket
    
    # 1. Check runsv
    result = subprocess.run(
        ["sv", "status", f"/data/data/com.termux/files/usr/var/service/{service_name}"],
        capture_output=True, text=True
    )
    running = "run:" in result.stdout
    
    # 2. Return structured result
    return {"name": service_name, "status": "running" if running else "stopped"}
```

### Shell Script Standards

```bash
# PASS: Guard clauses, error handling
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SERVICE_NAME="${1:-}"
if [ -z "$SERVICE_NAME" ]; then
  echo "Usage: $0 <service-name>" >&2
  exit 1
fi

sv status "/data/data/com.termux/files/usr/var/service/$SERVICE_NAME"
```

## API Design (Dashboard :8083)

### Endpoint Structure

```
GET    /api/status          # Full system status
POST   /api/agent/chat      # Chat with AI via 9Router
POST   /api/agent/action    # Execute browser action via MCP
POST   /api/agent/task      # Schedule or run a task
GET    /api/history         # Uptime history
GET    /api/models          # Available models from 9Router
GET    /api/services        # Service auth status
GET    /api/mcp             # MCP server health + tools
GET    /api/rotation        # IP rotation status
```

### Response Format

```python
# PASS: Consistent JSON structure
{
  "timestamp": "2026-07-11T13:00:00.000000",
  "services": [
    {"id": "codex", "name": "Codex", "status": "running", "port": 5900, "tcp": true}
  ],
  "env": {"uptime": "5 days", "python": "3.13.13"}
}
```

### Error Handling

```python
# PASS: Structured error responses
def error_response(status: int, message: str):
    return (json.dumps({
        "error": True,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }), status, {"Content-Type": "application/json"})
```

## Backend Patterns for ZES

### Service Check Pattern

```python
def tcp_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a TCP port is accepting connections."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except Exception:
        return False
```

### HTTP Health Check Pattern

```python
def http_status(url: str, timeout: int = 2) -> int | None:
    """Check if an HTTP endpoint responds."""
    import urllib.request
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return r.status
    except Exception as e:
        return getattr(e, "code", None)
```

### Configuration Pattern

```python
# Use constants at module level, never hardcode in functions
SERVICE_REGISTRY = {
    "r9": {"port": 20128, "desc": "9Router AI Gateway"},
    "hermes": {"port": 8787, "desc": "Hermes Cron/Scheduler"},
    "codex": {"port": 5900, "desc": "AI API Proxy"},
    "ttyd": {"port": 7173, "desc": "Web Terminal"},
}

SERVICE_DIR = "/data/data/com.termux/files/usr/var/service"
```

## Best Practices

1. **Readability first** — code is read more than written
2. **KISS** — simplest solution that works
3. **DRY** — extract common patterns (e.g. `tcp_open()`, `run()`)
4. **YAGNI** — don't add features before they're needed
5. **Immutability** — prefer constants over mutable globals
6. **Structured data** — use dicts/JSON, not string concatenation
7. **Error handling** — never expose stack traces to API consumers
8. **Type hints** — Python type annotations for all functions

**Remember**: ZES services run unattended on Android. Code clarity and error resilience are paramount.
