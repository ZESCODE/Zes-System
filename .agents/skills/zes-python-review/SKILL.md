---
name: zes-python-review
description: Python review for ZES — PEP 8, type hints, error handling, security patterns for dashboard and service scripts.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Python Review

Python code review focused on ZES services: dashboard_v4.py, service scripts, eval/test runners.

## When to Activate

- Reviewing changes to dashboard_v4.py
- Reviewing new Python service scripts
- Reviewing test/eval infrastructure code

## Checklist

### 1. PEP 8 Compliance
- 4-space indentation, 88 char line limit
- Imports: stdlib → third-party → local (alphabetical within groups)
- Snake case for functions/variables, PascalCase for classes

### 2. ZES Python Patterns

```python
# ✅ Good: proper error handling with timeouts
def run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout.strip() or r.stderr.strip() or "")[:2000]
    except subprocess.TimeoutExpired:
        return "(timeout)"

# ✅ Good: SSE thread safety
with sse_lock:
    for q in sse_clients[:]:
        try:
            q.put_nowait(msg)
        except Exception:
            sse_clients.remove(q)
```

### 3. Security
- No eval() or exec() on user input
- All subprocess calls use timeout
- File paths use os.path.expanduser()
- JSON parsing wrapped in try/except

### 4. Performance
- SSE broadcasts are non-blocking (daemon thread)
- Service scanning uses short timeouts (1-2s)
- Polling intervals balanced (3s for dashboard)

