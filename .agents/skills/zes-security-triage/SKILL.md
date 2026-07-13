---
name: zes-security-triage
description: "Security triage for ZES System: API keys, credentials, port exposure, service vulnerabilities."
---

# ZES Security Triage

Use when reviewing ZES System security posture, auditing credential handling, or investigating potential vulnerabilities.

## Credential Audit

Check for these credential types across the ZES codebase:

1. **API Keys**: 9Router tokens, OpenAI keys, provider API keys
2. **Auth Secrets**: `.9router/auth/` files, OAuth tokens, session cookies
3. **SSH Keys**: Private keys in accessible locations
4. **Service Tokens**: MCP auth tokens, dashboard passwords

## Service Exposure Audit

ZES services should only bind to `127.0.0.1` unless explicitly designed for network access.

```bash
# Check what's listening on all interfaces
ss -tlnp | grep -v '127.0.0.1\|::1\|0.0.0.0'
```

### Port Exposure Rules

| Port | Service | Should Be | Notes |
|------|---------|-----------|-------|
| 20128 | 9Router | 127.0.0.1 | API key auth via CLI token |
| 8000 | VS Code | 127.0.0.1 | No auth token by default |
| 8001 | VS Code Mobile | 127.0.0.1 | Proxy - inherits target exposure |
| 8083 | Dashboard | 127.0.0.1 | System control panel |
| 5901 | MCP Server | 127.0.0.1 | Browser control API |
| 9222 | Chrome CDP | 127.0.0.1 | Full browser access |
| 9050 | Tor SOCKS | 127.0.0.1 | Anonymizing proxy |
| 7173 | ttyd | 127.0.0.1 | Web terminal |

## Vulnerability Patterns to Check

### Code Injection
- `eval()`, `exec()`, `Function()` calls with user input
- Shell command construction with string concatenation
- Dynamic `require()`/`import()` with user-controlled paths
- Template injection in dashboard HTML

### Path Traversal
- Static file serving with unvalidated paths
- File read operations with user-controlled paths
- Symlink following in archive extraction

### Auth / Secrets
- Hardcoded credentials or tokens in source code
- Secrets in git history or commit messages
- `.env` files committed to repo
- API keys exposed in error messages or logs
- OAuth tokens stored without encryption

### Network
- Services exposed to WAN without auth
- Missing CORS restrictions on APIs
- WebSocket endpoints without origin validation
- Proxy forwarding without host validation

## Quick Audit Commands

```bash
# Scan for hardcoded secrets in staged changes
git diff --cached | grep -iE 'api.?key|secret|token|password|sk-|ghp_'

# Check for exposed ports
ss -tlnp

# Check file permissions on sensitive dirs
ls -la ~/.9router/
ls -la ~/.ssh/
ls -la ~/.codex/

# Check for world-readable secrets
find ~/.9router -perm /o+r -type f 2>/dev/null
find ~/.ssh -perm /o+r -type f 2>/dev/null
```
