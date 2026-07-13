---
name: zes-tdd-workflow
description: Test-driven development for ZES services — dashboard, 9Router, Hermes, MCP scripts. Write tests first, then implement.
---

# ZES TDD Workflow

Apply test-driven development to ZES system services: dashboard Python code, shell scripts, MCP servers, and 9Router configs.

## When to Activate

- Writing or modifying ZES service code
- Adding API endpoints to dashboard
- Creating new scripts or cron jobs
- Refactoring existing ZES infrastructure code

## Core Principles

### 1. Tests BEFORE Code
Write the test first, then implement the code to make it pass.

### 2. Coverage Requirements
- Minimum 80% coverage for Python/TypeScript code
- All edge cases covered
- Error scenarios tested

### 3. Test Types for ZES

#### Unit Tests
```python
# Test dashboard service card rendering
def test_service_card_running():
    svc = {"id": "codex", "name": "Codex", "status": "running", "port": 5900}
    card = render_service_card(svc)
    assert "● Up" in card
    assert "5900" in card
```

#### Integration Tests
```bash
# Test 9Router API responds
response=$(curl -s http://localhost:20128/api/providers)
echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['connections']) > 0"
```

#### Health Check Tests
```bash
# Test all ZES services respond
for svc in r9 hermes codex; do
  port_map="r9:20128 hermes:8787 codex:5900"
  port=$(echo $port_map | grep -o "$svc:[0-9]*" | cut -d: -f2)
  if curl -s http://localhost:$port > /dev/null 2>&1; then
    echo "PASS: $svc on :$port"
  else
    echo "FAIL: $svc on :$port"
  fi
done
```

## TDD Workflow

### Step 1: Write the Failing Test
```python
# tests/test_dashboard_api.py
def test_status_endpoint():
    import urllib.request
    resp = urllib.request.urlopen("http://localhost:8083/api/status")
    assert resp.status == 200
    data = json.loads(resp.read())
    assert "services" in data
```

### Step 2: Run — It Should Fail
```bash
pytest tests/test_dashboard_api.py -v
# Expected: FAIL (endpoint not implemented yet)
```

### Step 3: Implement
```python
# dashboard_v3.py
class DashboardHandler:
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.wfile.write(json.dumps(get_status()).encode())
```

### Step 4: Run — It Should Pass
```bash
pytest tests/test_dashboard_api.py -v
# Expected: PASS
```

## ZES-Specific Testing Patterns

### Testing Shell Scripts
```bash
# Unit test for a shell function
test_port_check() {
  local result=$(ss -tlnp 2>/dev/null | grep -c ":5900")
  if [ "$result" -eq 1 ]; then
    echo "PASS: port 5900 is listening"
  else
    echo "FAIL: port 5900 not found"
  fi
}
```

### Testing MCP Tools
```python
def test_mcp_tool_call():
    import subprocess
    result = subprocess.run(
        ["sv", "status", "zeschrome-mcp"],
        capture_output=True, text=True
    )
    assert "run:" in result.stdout
```

## Best Practices

1. **Test what users/agents see**, not internal state
2. **One assertion per test** — focus on single behavior
3. **Mock external services** — don't depend on live 9Router in unit tests
4. **Test error paths** — what happens when a service is down?
5. **Keep tests fast** — health check tests < 5s
6. **CI gate** — run tests before deploying dashboard changes

## Common ZES Mistakes to Avoid

```python
# FAIL: Testing implementation details
assert dashboard._services_cache[0]["id"] == "codex"

# PASS: Testing user-visible behavior
resp = client.get("/api/status")
assert resp.json["services"][0]["id"] == "codex"
```

**Remember**: Tests are the safety net that lets you refactor ZES services confidently.
