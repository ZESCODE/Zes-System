# ZES System — Complete System Documentation

## Quick Reference

```bash
zes status          # all services + health
zes health          # run 20 test suite  
zes mcp list        # list MCP bridge tools
zes backup          # snapshot configs
zes restore         # restore from backup
zes restart <svc>   # restart service
zes logs <svc>      # tail logs (20 lines)
zes dashboard       # show dashboard URL
zes-scan            # security hardening scan
zes-backup list     # list snapshots
```

## System Status (20/20 tests passing, 8/8 health evals — 100%)

| Service | Port | Status | Details |
|---------|------|--------|---------|
| **9Router** | 20128 | ✅ | 18 providers (9 active) — routes to GitHub Copilot, Groq, Cerebras, Mistral, OpenRouter, Cloudflare, Gemini, DeepSeek, NVIDIA NIM, Anthropic |
| **Dashboard v4** | 8083 | ✅ | SSE real-time · Drawer nav · Provider model names · MCP panel · Audit log · Terminal iframe · Mobile-optimized (responsive 768px/480px) |
| **Hermes** | — | ✅ | Gateway · 10 cron jobs · MCP layer |
| **Claude Code** | CLI/:5905 | ✅ | v2.1.207 via proot-distro Debian — 6 MCP servers, 31 skills, 16 agents, 9 hooks · 9Router proxy |
| **Claude Proxy** | 5905 | ✅ | 9Router-proxied endpoint for Claude Code API |
| **Codex** | 5900 | ✅ | AI API proxy |
| **VS Code Server** | 8000 | ✅ | Web VS Code with Cline + Continue |
| **VS Code Mobile** | 8001 | ✅ | Mobile-optimized VS Code |
| **ttyd** | 7173 | ✅ | Web terminal |
| **Tor** | 9050 | ✅ | SOCKS5 proxy pool |
| **zesChrome MCP** | 5901 | ✅ | 18 tools — browser automation + ZES system tools |
| **ZES Bridge MCP** | stdio | ✅ | 10 tools — dashboard, 9Router, services, Tor control |
| **Agent UI** | 8084 | ✅ | ZES-aware chat · 12 tools · persistent memory · system knowledge base |
| **Swarm** | 5030 | ✅ | Multi-agent orchestrator |
| **Agent Dashboard API** | 8002 | ✅ | REST API |
| **Agent Dashboard Web** | 8003 | ✅ | Frontend |
| **Cloudflare Tunnel** | — | ✅ | Remote access |
| **Composio CLI** | — | ✅ | Gmail + 1000+ API integrations |

## MCP Layer — 6 Servers

Configured in `~/.claude.json`:

| Server | Tools | Type | Description |
|--------|-------|------|-------------|
| **zeschrome** | 18 | Node stdio (:5901) | Browser automation via CDP + system tools |
| **zes-bridge** | 10 | Node stdio | Dashboard, 9Router, services, Tor control |
| **chrome-devtools** | 8 | npx | Browser debugging protocol |
| **filesystem** | 5 | npx | File operations on workspace |
| **memory** | 3 | npx | Persistent session memory |
| **sequential-thinking** | 2 | npx | Chain-of-thought reasoning |

## Security Hooks — 9 Active

| Hook | File | Purpose |
|------|------|---------|
| config-protection | `hooks/config-protection.js` | Prevents unauthorized config edits |
| gateguard-fact-force | `hooks/gateguard-fact-force.js` | Security gate enforcement |
| mcp-health-check | `hooks/mcp-health-check.js` | MCP server health verification |
| governance-capture | `hooks/governance-capture.js` | Audit trail capture |
| insaits-security-monitor | `hooks/insaits-security-monitor.py` | Python-based security monitoring |
| insaits-security-wrapper | `hooks/insaits-security-wrapper.js` | JS security wrapper |

## Skills — 31

**Core (21):** zes-testing, zes-autoreview, zes-security-review, zes-bugfix-sweep, zes-dev-patterns, zes-tdd-workflow, zes-mcp-patterns, zes-agent-debugging, zes-verification, zes-evals, zes-research, zes-changelog, zes-heap-leaks, zes-performance, zes-transcript, openclaw-debugging, technical-documentation, gitcrawl-z, gitcrawl-zes, zes-refactor-docs, zes-security-triage

**ECC-imported (10):** zes-plan-canvas, zes-coding-standards, zes-backend-patterns, zes-documentation-lookup, zes-frontend-patterns, zes-e2e-testing, zes-benchmark-methodology, zes-strategic-compact, zes-product-capability, zes-agent-introspection-debugging

## Agents — 16

planner, architect, code-reviewer, tdd-guide, security-reviewer, spec-miner, python-reviewer, typescript-reviewer, build-error-resolver, harness-optimizer, e2e-runner, performance-optimizer, loop-operator, code-architect, silent-failure-hunter, doc-updater

## Backup System

- `zes-backup snapshot` — snapshots `.9router/`, `.claude.json`, `.hermes/`, `dashboard_v4.py`, `Zes-System/` repo
- `zes-backup list` — lists all snapshots
- `zes-backup restore` — restore from latest snapshot
- Auto-committed to Zes-System git, Hermes cron daily at 04:00

## Dashboard v4 Features

![Dashboard on :8083]
- **Real-time SSE push**: services (3s), MCP (5s), providers (10s), env stats
- **Left drawer nav**: service status dots · quick links (9Router, VS Code, ttyd, Codex, Agent UI) · system actions (Claude Code terminal, Tor rotate, health evals)
- **Provider heat map**: active/unavailable/error status dots · model info from `modelLock_*` keys · auth type + proxy info
- **MCP server status panel**: alive/dead indicators · tool counts · command display
- **Hook audit log**: auto-refresh 5s · governance event feed
- **ttyd terminal iframe**: embedded web terminal
- **Mobile-optimized**: 480px + 768px breakpoints · swipe gestures · single-column grids · compact cards

## 9Router — 18 Providers

**OAuth**: GitHub Copilot, Cline, Codex (OpenAI), Gemini CLI, Qoder, Kiro
**API Key**: NVIDIA NIM, Groq, Gemini, DeepSeek, Cerebras, OpenRouter, Anthropic, Cloudflare AI, Mistral AI

### OpenAI-Compatible Nodes
| Prefix | Endpoint | Proxy |
|--------|----------|-------|
| `gm` | generativelanguage.googleapis.com/v1beta/openai | Direct |
| `nv` | integrate.api.nvidia.com/v1 | Direct |
| `he` | :8787 | Tor |
| `oc` | :4040/v1 | Tor |

## Claude Code Config

- **6 MCP servers**: zeschrome, zes-bridge, chrome-devtools, filesystem, memory, sequential-thinking
- **3 hooks**: config-protection, gateguard-fact-force, mcp-health-check
- **31 skills** in `~/.claude/plugins/ecc/skills/`
- **API key**: cleared (uses 9Router routing)

## Agent UI (:8084) — Control Panel

- **12 ZES system tools**: get_system_status, run_health_evals, run_backup, get_providers, run_security_scan, check_service, list_services, restart_service, get_service_logs, get_mcp_status, rotate_tor, get_claude_code_info
- **Persistent memory**: stores conversation summaries, learned facts, user preferences
- **ZES knowledge base**: full system architecture documentation served to LLM
- **Toolbar**: 6 quick-action buttons (Status, Health, Backup, Providers, Security, Memory)
- **Mobile-optimized**: toolbar integrated into `#app` flex container for visibility

## New Tools (v4.1)

| Tool | Command | Description |
|------|---------|-------------|
| **Agent Orchestration Pipeline** | `zes pipeline` | Runs tasks through Planner→Architect→Coder→Reviewer→Tester with status tracking |
| **Security Supply Chain Scanner** | `zes scan` | Scans npm/pip deps, credentials, permissions, config leaks |
| **Session Kanban** | `zes kanban` | Persistent task board linked to agent conversations via REST API |
| **Cross-Harness Deployer** | `zes deploy` | Export ZES agents to Cursor, Gemini, CodeBuddy formats |
| **Dashboard Plugin Framework** | `zes plugins` | MCP servers register widgets via POST `/api/plugins/register` |

## Dashboard Plugin Framework

Any MCP server can register itself as a dashboard plugin:

```bash
python3 ~/Zes-System/scripts/zes-plugin-register \
  "My Plugin" "1.0" "Description" \
  '[{"id":"main","name":"My Widget"}]' \
  '{"main":"http://localhost:8083/"}'
```

Auto-registered on dashboard startup:
- Agent Orchestration Pipeline (2 widgets)
- Security Supply Chain Scanner (2 widgets)
- Session Kanban (1 widget)
- Cross-Harness Deployer (1 widget)

## Kanban REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/kanban/tasks` | List all tasks grouped by column |
| POST | `/api/kanban/tasks` | Create task `{title, description, source, conversationId}` |
| POST | `/api/kanban/tasks/:id/move` | Move task `{column: backlog\|in-progress\|review\|done}` |
| POST | `/api/kanban/tasks/:id/link` | Link conversation `{conversationId}` |

## File Structure (Updated)

```
~/
├── dashboard_v4.py              — Dashboard v4 (SSE + REST + Plugin Framework)
├── Zes-System/
│   ├── AGENTS.md                — This file
│   ├── scripts/
│   │   ├── orchestrate-pipeline.js  — [NEW] Agent pipeline runner
│   │   ├── security-supply-chain-scan.py — [NEW] Supply chain security scanner
│   │   ├── deploy-agent.js          — [NEW] Cross-harness agent deployer
│   │   ├── register-system-plugins.py — [NEW] Auto-register plugins
│   │   └── zes-cli.sh               — [UPDATED] New commands: pipeline, scan, kanban, deploy, plugins
│   ├── services/agent-ui/
│   │   ├── kanban-store.js          — [NEW] Persistent kanban task store
│   │   └── agent-server.js          — [UPDATED] Kanban API routes
│   └── scripts/zes-plugin-register  — [NEW] Plugin registration helper
```

## Architecture (Updated)

```
You (NL) → Codex (superpowers) → 9Router (:20128) → Models
                                        ↘
                              Hermes · VS Code · Agent UI (:8084) · Dashboard (:8083)
                                        ↘             ↓
                              zesChrome MCP (:5901) · ZES Bridge MCP (stdio)
                                        ↘             ↓
                              Headless Chrome (:9222) → Browser Control
                                                         ↓
                              ┌── Dashboard Plugin Framework ──────┐
                              │ → Orchestration Pipeline (zes pipeline)
                              │ → Security Scanner (zes scan)
                              │ → Session Kanban (zes kanban)
                              │ → Cross-Harness Deployer (zes deploy)
                              └────────────────────────────────────┘
```

## Architecture

```
You (NL) → Codex (superpowers) → 9Router (:20128) → Models
                                        ↘
                              Hermes · VS Code (Cline/Zed) · Agent UI (:8084)
                                        ↘
                              zesChrome MCP (:5901) · ZES Bridge MCP (stdio)
                                        ↘
                              Headless Chrome (:9222) → Browser Control
```

## Common Commands

```bash
# Service management
sv status /data/data/com.termux/files/usr/var/service/*
sv restart <name>

# 9Router API
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers

# Dashboard
curl -s http://localhost:8083/api/status

# Health checks
zes health
zes-scan
```

## File Structure

```
~/
├── dashboard_v4.py              — Dashboard v4 (SSE + REST, 876 lines)
├── dashboard_v3.py              — v3 backup
├── .claude.json                 — 6 MCP servers + 3 hooks
├── .claude/                     — Claude Code local data
├── .9router/                    — 9Router config + auth
├── .hermes/                     — Hermes gateway config
├── Zes-System/                  — System repo
│   ├── AGENTS.md                — This file
│   ├── README.md
│   ├── scripts/
│   │   ├── zes-cli.sh           — ZES CLI entry
│   │   ├── run-tests.py         — 20-test suite
│   │   ├── run-evals.py         — 8 health evals
│   │   ├── health-check.sh
│   │   ├── security-scan.sh
│   │   └── hooks/               — 6 security hooks
│   ├── services/
│   │   └── agent-ui/            — Agent control panel
│   │       ├── agent-server.js  — Server (12 tools)
│   │       ├── index.html       — Chat UI (toolbar in #app)
│   │       ├── memory-store.js  — Persistent memory
│   │       └── zes-knowledge.json — System knowledge base
│   ├── zes-chrome/
│   │   ├── mcp-server/          — zeschrome MCP (18 tools)
│   │   ├── zes-bridge-mcp/      — ZES Bridge MCP (10 tools)
│   │   └── ...                  — Chrome extension
│   ├── docs/
│   │   ├── infrastructure/
│   │   ├── services/
│   │   ├── providers/
│   │   ├── agents/
│   │   └── guides/
│   ├── .agents/
│   │   ├── skills/              — 31 skills
│   │   └── agents/              — 16 agents
│   └── backups/
│       ├── scripts/             — Backup/restore scripts
│       └── snapshots/           — Timestamped config snapshots
├── .config/claude/claude.json — Claude Code config (archived)
├── .ecc/                        — ECC cross-harness config (imported agents/skills)
├── .nimbalyst/                  — Nimbalyst monorepo (reference)
└── .local/bin/zes               → Zes-System/scripts/zes-cli.sh
```

## Recent Fixes (2026-07-11)

### :8084 — ZES Tool Bar moved to Drawer
- **Problem**: `.zes-tool-bar` div was a standalone bar rendering System Tools buttons (📊 🏥 💾 🔌 🛡️ 🧠) between the toolbar and sessions panel, duplicating what was already in the left drawer nav.
- **Fix**: Removed the duplicate standalone bar. All System Tools are now exclusively in the left drawer under "System Tools" section.
- **Files changed**: `services/agent-ui/index.html` (removed CSS, HTML, updated badge JS)
- **Old server.js**: Removed (hardcoded API key, replaced by agent-server.js)

---

## Codex Orchestrator Layer

Codex is the **NL orchestrator** for ZES. It understands user intent and delegates to the right backend.

```
Codex (NL Orchestrator) ──┬── proot-distro → Claude Code (deep coding)
                           ├── hermes CLI → Hermes Gateway (cron, messaging)
                           ├── sv → runsv services (system control)
                           └── curl → Dashboard + 9Router API (monitoring)
```

### Quick Reference for Codex

| Action | Command |
|--------|---------|
| Delegate coding to Claude Code | `proot-distro login debian -- bash -c 'ANTHROPIC_BASE_URL=http://127.0.0.1:5905 ANTHROPIC_API_KEY=sk-ant-anything claude -p "task" --bare --allowedTools "Bash,Read,Write,Edit"` |
| Schedule Hermes cron | `hermes cron create --name "job" --prompt "..." --schedule "every 60m"` |
| Check services | `sv status /data/data/com.termux/files/usr/var/service/*` |
| Restart service | `sv restart /data/data/com.termux/files/usr/var/service/<name>` |
| 9Router providers | `curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers` |

### Skills

- `~/.codex/skills/zes-orchestrator/` — Full orchestrator skill with delegation scripts
- `~/.codex/skills/zes-system/` — ZES system operational knowledge
