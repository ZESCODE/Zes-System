---
name: zes-testing
description: "Test, verify, and debug ZES System services, proxy configurations, and API endpoints."
---

# ZES Testing

Use when validating changes to ZES services, testing proxy configurations, or debugging service failures.

## Default Rule

Prove the changed surface first. Do not reflexively test everything.

1. Inspect the diff and classify the change:
   - **Dashboard change**: Restart and check `/api/status` returns valid JSON
   - **Proxy/server change**: Verify target reachable, proxy returns 200, wrapper injection works
   - **Service config change** (run script): Restart service, check `sv status`, check port is listening
   - **Documentation only**: Verify format with a quick scan

## Service Verification

```bash
# 1. Check service is running
sv status /data/data/com.termux/files/usr/var/service/<name>

# 2. Check port is listening
ss -tlnp 2>/dev/null | grep <port>

# 3. Check HTTP health endpoint (if available)
curl -s http://localhost:<port>/health

# 4. Check service logs for errors
tail -10 /data/data/com.termux/files/var/log/<name>/current
```

## Proxy Verification (VS Code Mobile)

```bash
# Health endpoint
curl -s http://localhost:8001/health

# Proxy test - should return 200 (VS Code behind proxy)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/

# Verify wrapper injection
curl -s http://localhost:8001/ | grep -c 'zes-mobile-bar'

# WebSocket proxy test
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/ | grep 200
```

## API Endpoint Testing

```bash
# Dashboard status
curl -s http://localhost:8083/api/status | python3 -m json.tool

# 9Router provider check
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
curl -s -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Providers: {len(d.get(\"connections\",[]))}')"

# MCP server health
curl -s http://localhost:5901/health
```

## Debugging Common Issues

### Service won't start
1. Check run script syntax: `bash -n /path/to/run`
2. Check run script permissions: `ls -la /path/to/run`
3. Check for port conflicts: `ss -tlnp | grep <port>`
4. View full log: `cat /data/data/com.termux/files/var/log/<name>/current`

### Proxy returning errors
1. Check target service is running
2. Check proxy logs for error messages
3. Test target directly with curl
4. Check for WebSocket upgrade failures

### Wrapper not injecting
1. Check that HTML response contains `</body>` tag
2. Check that wrapper-head.html and wrapper-foot.html exist
3. Check content-type is text/html
4. Test with curl and grep for injected elements
