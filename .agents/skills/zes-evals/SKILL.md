---
name: zes-evals
description: Formal evaluation framework for ZES system — define pass/fail criteria, measure 9Router/Hermes/Dashboard reliability, track regressions.
---

# ZES Eval Harness

Eval-driven quality assurance for ZES infrastructure. Define pass/fail criteria for service reliability, measure agent task completion, and track regressions.

## When to Activate

- Setting up quality gates for ZES deployments
- Defining what "healthy" means for each service
- Measuring agent task completion reliability
- Creating regression tests for ZES system changes
- Benchmarking service performance

## Philosophy

Evals are the "unit tests of system reliability":
- Define expected behavior BEFORE making changes
- Run evals continuously via Hermes cron
- Track regressions with each change
- Use pass@k metrics for reliability measurement

## ZES Service Evals

### Service Health Eval

```yaml
eval: service-health
schedule: every 30m via Hermes cron
criteria:
  - service: r9
    check: port 20128 open
    pass: tcp_open("127.0.0.1", 20128)
  - service: hermes
    check: binary exists and responds
    pass: "hermes --version returns 0"
  - service: dashboard
    check: HTTP 200 on /api/status
    pass: http_status("http://localhost:8083/api/status") == 200
  - service: tor
    check: SOCKS5 proxy responding
    pass: tcp_open("127.0.0.1", 9050)
```

### Provider Availability Eval

```yaml
eval: 9router-providers
schedule: hourly
criteria:
  - provider: groq
    check: status is "active"
    pass: provider_status("groq") in ("active", "unknown")
  - provider: cerebras
    check: status is "active"
    pass: provider_status("cerebras") in ("active", "unknown")
  - provider: mistral
    check: status is "active"
    pass: provider_status("mistral") in ("active", "unknown")
  - metric: active_providers
    check: at least 10 of 18 active
    pass: count_active_providers() >= 10
```

## Eval Result Format

```json
{
  "eval": "service-health",
  "timestamp": "2026-07-11T13:00:00Z",
  "results": [
    {"service": "r9", "pass": true, "latency_ms": 2},
    {"service": "hermes", "pass": true, "latency_ms": 5},
    {"service": "dashboard", "pass": true, "latency_ms": 15},
    {"service": "tor", "pass": true, "latency_ms": 1}
  ],
  "summary": {"pass": 4, "fail": 0, "total": 4, "pass_rate": 1.0}
}
```

## Hermes Cron Integration

```bash
# Run evals via Hermes cron job
hermes cron add eval-service-health --schedule "*/30 * * * *" --command '
  python3 /data/data/com.termux/files/home/Zes-System/scripts/run-evals.py \
    --eval service-health \
    --output /data/data/com.termux/files/home/.zes/evals/service-health.json
'
```

## Eval Script Template

```python
#!/usr/bin/env python3
"""ZES eval runner — run evals and output JSON results."""
import json, socket, subprocess, sys, os
from datetime import datetime

def tcp_open(host, port, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except: return False

def http_status(url, timeout=3):
    import urllib.request
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return r.status
    except Exception as e:
        return getattr(e, "code", None)

def run_eval(name, checks):
    results = []
    for c in checks:
        try:
            passed = c["check"]()
        except Exception as e:
            passed = False
        results.append({"name": c["name"], "pass": passed})
    passed = sum(1 for r in results if r["pass"])
    return {
        "eval": name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": results,
        "summary": {"pass": passed, "fail": len(results) - passed, "total": len(results)}
    }

if __name__ == "__main__":
    evals = {
        "service-health": [
            {"name": "9Router", "check": lambda: tcp_open("127.0.0.1", 20128)},
            {"name": "Dashboard", "check": lambda: http_status("http://localhost:8083/api/status") == 200},
            {"name": "Tor SOCKS5", "check": lambda: tcp_open("127.0.0.1", 9050)},
        ]
    }
    eval_name = sys.argv[1] if len(sys.argv) > 1 else "service-health"
    result = run_eval(eval_name, evals.get(eval_name, []))
    print(json.dumps(result, indent=2))
```

## Continuous Evaluation

- **30 min**: Service health evals (via Hermes `dashboard-snapshot`)
- **60 min**: Provider availability evals
- **Daily**: Full system eval (all services + providers + latency)
- **On change**: Run relevant evals before declaring a change done

## Best Practices

1. **Define evals BEFORE making changes** — know what "done" looks like
2. **One criterion per eval item** — focused, measurable checks
3. **Track pass rate over time** — look for regression trends
4. **Alert on critical failures** — Hermes cron can trigger notifications
5. **Store history** — eval results in `~/.zes/evals/` for trend analysis

**Remember**: If you can't measure it, you can't improve it. Evals make ZES reliability measurable.
