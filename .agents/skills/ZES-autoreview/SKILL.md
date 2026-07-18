---
category: Review

name: zes-autoreview
description: "Code review closeout for ZES System changes. Runs structured review before shipping code in any ZES repo or service."
---


# ZES Auto Review

Run a structured review as closeout check before shipping changes to any ZES System component: Dashboard, MCP Server, VS Code Mobile Panel, services, or documentation.

## When to Use

- After non-trivial edits to ZES services, scripts, or docs
- Before committing changes to the Zes-System repo
- Before restarting or deploying any service
- When user asks for review before shipping

## Contract

- Treat review output as advisory. Always verify findings by reading real code paths.
- Reject speculative risks, unrealistic edge cases, or refactors that over-complicate the codebase.
- Keep going until no actionable findings remain or accepted findings are documented.
- If review triggers a fix, rerun the service test (curl health endpoint) and rerun review.
- Never override the requested review model. Retry on capacity errors.

## Review Checklist

### Code Changes
1. Does the code handle errors gracefully? Check try/catch patterns, promise rejections.
2. Are config values validated? API keys, ports, URLs should have sensible defaults or error messages.
3. Are there any hardcoded credentials, tokens, or secrets?
4. Does the change respect the existing code style (ES modules, async patterns)?
5. Are there race conditions in async code? Check promise chains, WebSocket handlers.
6. For proxy code (server.js): are timeouts set? Are errors forwarded to the client?

### Service Changes
1. Does the new service have a runsv run script?
2. Is the port documented in AGENTS.md and README.md?
3. Is the service added to the Dashboard SERVICES list?
4. Does the service restart cleanly? Test: `sv restart <name> && sleep 1 && sv status <name>`
5. Are there log files configured? runsv log/run should exist.

### Documentation Changes
1. Are new ports, endpoints, and services documented?
2. Is the AGENTS.md updated with any new architecture or commands?
3. Are environment variables or dependencies documented?

## Quick Commands

```bash
# Test service health
curl -s http://localhost:<port>/health
# Test proxy targets
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/
# Check service status
sv status /data/data/com.termux/files/usr/var/service/*
# View service logs
tail -5 /data/data/com.termux/files/var/log/<service>/current
```
