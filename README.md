# ZES System

> **ZES Control Center** — Self-hosted AI infrastructure: provider router, agent orchestration, and service management on Android/Termux.

## Dashboard

**URL:** http://localhost:8083

The ZES Control Center shows all services, AI provider status, system environment, and sparkline history — with a mobile-responsive left drawer nav and custom **Z** logo with gradient border.

## Architecture

```
Termux (Android aarch64) + Debian proot
├── 9Router v0.5.20         — AI provider router (:20128, 18 providers)
├── Hermes Gateway          — AI agent cron, scheduler, automation
├── Claude Code              — AI coding agent (:5905/5900)
├── VS Code Server          — Web VS Code with Cline/Continue (:8000)
├── VS Code Mobile Panel    — Mobile-optimized VS Code wrapper (:8001)
├── Agent Dashboard API     — Agent monitoring REST API (:8002)
├── Agent Dashboard Web     — Agent dashboard frontend (:8003)
├── Codex Server            — AI API proxy (:5900)
├── zesChrome MCP           — Chrome CDP bridge for browser automation (:5901)
├── Headless Chrome         — Browser automation engine (:9222)
├── ttyd                    — Web terminal (:7173)
├── Tor                     — SOCKS5 proxy for IP rotation (:9050)
└── Socat                   — TCP bridge (:8090)
```

## Services

| Service | Port | Runsv | Status | Description |
|---------|------|-------|--------|-------------|
| **9Router** | 20128 | `r9` | ✅ running | AI provider router — 18 providers |
| **Dashboard v4** | 8083 | `dashboard8083` | ✅ running | ZES Control Center (SSE, drawer nav, provider models, mobile) |
| **VS Code Server** | 8000 | `vscode-server` | ✅ running | Web VS Code (Cline + Continue + Copilot) |
| **VS Code Mobile** | 8001 | `vscode-mobile` | ✅ running | Mobile-optimized VS Code with touch zoom, toolbar, 2-col split |
| **Hermes Gateway** | 8787 | `hermes-gateway` | ✅ running | Cron, scheduler, agent backend |
| **Agent Dashboard API** | 8002 | `agent-dash` | ✅ running | Agent monitoring REST API |
| **Agent Dashboard Web** | 8003 | `agent-dash-web` | ✅ running | Agent dashboard frontend |
| **zesChrome MCP** | 5901 | `zeschrome-mcp` | ✅ running | Codex ↔ Chrome bridge (14 tools) |
| **Claude Code** | 5905 | `claude` | ✅ installed | AI coding agent via 9Router |
| **Headless Chrome** | 9222 | `chromium-cdp` | ✅ running | Browser automation (CDP) |
| **ttyd** | 7173 | `ttyd` | ✅ running | Web terminal |
| **Tor** | 9050 | `tor` | ✅ running | SOCKS5 proxy + ControlPort (9051) |
| **Codex Server** | 5900 | — | ✅ running | AI API proxy |
| **Socat** | 8090 | — | ✅ running | TCP bridge |
| **SSH** | 8022 | — | ⬇️ stopped | Remote access |

## AI Providers (via 9Router)

| Provider | Status | Auth | Notes |
|----------|--------|------|-------|
| **OpenRouter** | ✅ active | API key | 5 routed models |
| **Groq** | ✅ active | API key | Fast inference |
| **Gemini** | ✅ active | API key | Google models |
| **Cerebras** | ✅ active | API key | Fast CS-3 |
| **Mistral AI** | ✅ active | API key | Mistral models |
| **Cloudflare AI** | ✅ active | API key | 61+ models, verified working |
| **GitHub Copilot** | ✅ active | OAuth | Copilot Free plan |
| **Cline** | ✅ active | OAuth | Cline provider |
| **Kiro** | ✅ active | OAuth | 18 models routed |
| **NVIDIA NIM** | ❌ unavailable | API key | 502 timeout, needs re-config |

## Quick Start

```bash
# Check all services
sv status /data/data/com.termux/files/usr/var/service/*

# Restart a service
sv restart r9        # 9Router
sv restart dashboard8083
sv restart vscode-mobile

# Dashboard
curl -s http://localhost:8083/api/status | python3 -m json.tool

# AI test (via 9Router/Cloudflare)
curl -s -H "Authorization: Bearer sk-d25ec2e336a68df0-trhjvq-621c9b41" \
  http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"cf/@cf/qwen/qwen2.5-coder-32b-instruct","messages":[{"role":"user","content":"hi"}]}'
```

## File Structure

```
~/
├── AGENTS.md                 — Main system guide (v5)
├── dashboard_v3.py           — Python dashboard serving :8083
├── Zes-System/               — System repo
│   ├── README.md             — This file
│   ├── AGENTS.md             — System agents guide
│   ├── docs/                 — Documentation
│   └── services/
│       └── vscode-mobile/    — Mobile VS Code wrapper
│           ├── server.js     — Node.js proxy server
│           └── wrapper.html  — Mobile HTML wrapper
├── Documents/Codex/          — Codex sessions


## Codex Orchestrator Layer

Codex acts as the **NL orchestrator** for the ZES system, understanding user intent and delegating to the right backend.

```
Codex (NL Orchestrator) ──┬── proot-distro → Claude Code (deep coding)
                           ├── hermes CLI → Hermes Gateway (cron, messaging)
                           ├── sv → runsv services (system control)
                           └── curl → Dashboard + 9Router API (monitoring)
```

### Quick Commands

```bash
zes start              # Start all 25 services
zes stop               # Stop all services
zes menu               # Interactive TUI menu
zes status             # Show all services + health
zes restart <svc>      # Restart a service
```

### Orchestrator Skill

A dedicated skill at `~/.codex/skills/zes-orchestrator/` provides 6 scripts:

| Script | Purpose |
|--------|---------|
| `claude-code-exec.sh` | Delegate coding tasks to Claude Code (proot) |
| `claude-session-reader.sh` | Interact with running Claude Code session |
| `9router-switch-model.sh` | List, switch, test AI models from 18 providers |
| `hermes-cron-manager.sh` | Schedule/manage Hermes cron jobs |
| `hermes-cron-notify.sh` | Report cron results to dashboard/Telegram |
| `system-health.sh` | Comprehensive health check |

### Delegating to Claude Code

```bash
# Send a coding task to Claude Code (returns result)
ANTHROPIC_BASE_URL=http://127.0.0.1:5905 ANTHROPIC_API_KEY=sk-ant-anything \
  proot-distro login debian -- claude -p "Find and fix the bug" --bare --allowedTools "Bash,Read,Write,Edit"

# Or use the helper script
bash ~/.codex/skills/zes-orchestrator/scripts/claude-code-exec.sh "Fix the login bug"
```

### Model Switching

```bash
# List all 694 models from 18 providers
bash ~/.codex/skills/zes-orchestrator/scripts/9router-switch-model.sh list

# Switch Claude Code's default model
bash ~/.codex/skills/zes-orchestrator/scripts/9router-switch-model.sh switch gh/claude-sonnet-4.6

# Switch and restart Claude Code
bash ~/.codex/skills/zes-orchestrator/scripts/9router-switch-model.sh switch gh/claude-sonnet-4.6 --restart

# Smart model suggestion for task type
bash ~/.codex/skills/zes-orchestrator/scripts/9router-switch-model.sh smart coding
```

### Cron Job Management

```bash
# View all cron jobs
hermes cron list

# Create a new cron job
hermes cron create "every 60m" "Check disk space and memory" --name "health-check"

# Use the manager script
bash ~/.codex/skills/zes-orchestrator/scripts/hermes-cron-manager.sh list
bash ~/.codex/skills/zes-orchestrator/scripts/hermes-cron-manager.sh create "my-job" "Do something" "every 60m"

└── .9router/                 — 9Router database and config
```

## Links

- **Dashboard**: http://localhost:8083
- **VS Code**: http://localhost:8000
- **VS Code (Mobile)**: http://localhost:8001
- **Agent Dashboard**: http://localhost:8003
- **ttyd (Terminal)**: http://localhost:7173
- **Claude Code**: CLI via `claude` command · Proxy http://localhost:5905
