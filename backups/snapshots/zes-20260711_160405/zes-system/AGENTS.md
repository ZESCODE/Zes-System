# ZES System — Complete Agent Guide

## System Architecture

```
You → Codex / Claude Code → 9Router (:20128) → 18 AI Providers
                             ↘
  Dashboard (:8083) · Hermes · VS Code · Chrome MCP (:5901)
                             ↘
  Tor (:9050) · ttyd (:7173) · SSH (:8022)
```

## Services Status (23 total, 17 running)

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **9Router** | 20128 | ✅ | AI router — 18 providers (13 active) |
| **Dashboard v3** | 8083 | ✅ | ZES Control Center |
| **Hermes Gateway** | — | ✅ | Cron, scheduler, agent backend |
| **Claude Code** | CLI | ✅ | Anthropic AI agent v2.1.207 |
| **Codex** | 5900 | ✅ | AI API proxy + Zen gateway |
| **VS Code Server** | 8000 | ✅ | Browser VS Code |
| **Chrome CDP** | 9222 | ✅ | Browser automation |
| **zeschrome MCP** | 5901 | ✅ | 18 browser + system tools |
| **ZES Bridge MCP** | stdio | ✅ | 10 system API tools |
| **ttyd** | 7173 | ✅ | Web terminal |
| **Tor** | 9050 | ✅ | SOCKS5 proxy |
| **ZES Swarm** | 5030 | ✅ | Multi-agent orchestrator |
| **Agent UI** | 8084 | ✅ | Chat dashboard |

## MCP Layer — 6 Servers

| Server | Type | Tools |
|--------|------|-------|
| `zeschrome` | Node stdio (:5901) | 18 tools — browse, screenshot, click, type, auth, system check |
| `zes-bridge` | Node stdio | 10 tools — dashboard API, 9Router, services, Tor, evals |
| `chrome-devtools` | npx | Chrome DevTools protocol via CDP |
| `filesystem` | npx | File read/write/search on workspace |
| `memory` | npx | Persistent memory across sessions |
| `sequential-thinking` | npx | Chain-of-thought reasoning |

## Security Hooks (3 active)

| Hook | Trigger | Purpose |
|------|---------|---------|
| `mcp-health-check` | Pre Bash/Write/Edit | Verify MCP servers healthy |
| `gateguard-fact-force` | Pre Bash | Security gate — dangerous commands |
| `config-protection` | Pre Write/Edit | Block config file tampering |

## Skills — 26 total

### ZES-Native (21)
`zes-testing`, `zes-autoreview`, `zes-security-review`, `zes-bugfix-sweep`, `zes-dev-patterns`, `zes-tdd-workflow`, `zes-mcp-patterns`, `zes-agent-debugging`, `zes-verification`, `zes-evals`, `zes-research`, `zes-changelog`, `zes-heap-leaks`, `zes-performance`, `zes-transcript`, `openclaw-debugging`, `technical-documentation`, `gitcrawl-z`, `gitcrawl-zes`, `zes-refactor-docs`, `zes-security-triage`

### Imported from ECC (5)
`zes-plan-canvas`, `zes-coding-standards`, `zes-backend-patterns`, `zes-documentation-lookup`, `zes-frontend-patterns`

### Agents (10)
`planner`, `code-reviewer`, `tdd-guide`, `security-reviewer`, `python-reviewer`, `typescript-reviewer`, `architect`, `build-error-resolver`, `spec-miner`, `harness-optimizer`

All agents auto-discoverable by Claude Code from `~/.claude/projects/zes-cwd/`.

## Quick Reference

```bash
# Service management
sv status /data/data/com.termux/files/usr/var/service/*
sv restart <name>

# Health checks (8/8 passing)
python3 ~/Zes-System/scripts/run-evals.py

# Dashboard API
curl -s http://localhost:8083/api/status | python3 -m json.tool

# Claude Code
claude --version
claude "your prompt"

# 9Router providers
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers

# MCP tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | node ~/Zes-System/zes-chrome/zes-bridge-mcp/server.js
```
