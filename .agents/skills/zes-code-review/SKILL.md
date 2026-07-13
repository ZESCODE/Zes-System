---
name: zes-code-review
description: Full code quality, security pattern, and maintainability review for ZES system — Python, JavaScript, shell scripts, and configs.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Code Review

Systematic code review for ZES infrastructure: dashboard, agent UI, MCP servers, shell scripts, 9Router configs.

## When to Activate

- Before merging changes to ZES-System repo
- After modifying dashboard_v4.py or agent-server.js
- When adding new MCP tools or service run scripts
- Reviewing security-related changes (ports, keys, tunnels)

## Review Checklist

### 1. ZES-Specific Security
- [ ] No hardcoded API keys in source files
- [ ] Port bindings restricted to 127.0.0.1 (not 0.0.0.0)
- [ ] runit service files have proper permissions
- [ ] Cloudflare tunnel config doesn't expose admin ports
- [ ] 9Router tokens not logged or printed

### 2. Code Quality
- [ ] Error handling for all subprocess/HTTP calls
- [ ] Timeout values on all external requests
- [ ] SSE/RACE-safe threading (use locks for shared state)
- [ ] JSON serialization handles edge cases
- [ ] Log messages don't contain secrets

### 3. ZES Service Patterns
- Python services: use BaseHTTPRequestHandler, daemon threads for SSE
- Node services: Express/HTTP with proper error middleware
- Shell scripts: set -euo pipefail, trap for cleanup
- MCP servers: stdio transport, proper JSON-RPC response format

## Deliverables
- List of issues found with severity (critical/major/minor)
- Suggested fix for each issue
- All clear if no issues found

