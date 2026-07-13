---
name: zes-tdd
description: Test-driven development for ZES — write tests before implementation. Covers dashboard Python, agent Node.js, and shell scripts.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES TDD Workflow

Apply test-driven development to ZES system: dashboard_v4.py, agent-server.js, MCP servers, backup scripts.

## When to Activate

- Adding features to dashboard or agent UI
- Creating new MCP tools or API endpoints
- Modifying service management scripts
- Refactoring existing ZES code

## Workflow

### Step 1: Write Test First
```python
# Example: test dashboard API
def test_api_status_returns_services():
    response = http_get("http://localhost:8083/api/status")
    assert response.status == 200
    data = json.loads(response.body)
    assert "services" in data
    assert "providers" in data
```

### Step 2: Run Tests (should fail)
```bash
python3 ~/Zes-System/scripts/run-tests.py
```

### Step 3: Implement
```python
class ZESHandler:
    def _send_json(self, data, code=200):
        # Minimal implementation to pass test
        ...
```

### Step 4: Verify
```bash
python3 ~/Zes-System/scripts/run-tests.py  # Should pass
python3 ~/Zes-System/scripts/run-evals.py  # Health check
```

## Coverage Targets
- Python services: 80%+ line coverage
- JavaScript/Node: 70%+ line coverage
- Shell scripts: manual test for each exit path
- Critical paths: 100% (service restart, API auth, backup/restore)

