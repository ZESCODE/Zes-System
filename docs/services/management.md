# Service Management

## Overview

All services run under **runit** supervision via `runsv`. The service directory is at `/data/data/com.termux/files/usr/var/service/`.

## Service Commands

```bash
# All services status (25 running)
sv status /data/data/com.termux/files/usr/var/service/*

# Individual service
sv status <name>
sv restart <name>
sv start <name>
sv stop <name>
sv force-stop <name>       # Force stop (SIGKILL)

# Start/stop all services
./start.sh                  # Start all 25 services
./stop.sh                   # Stop all services gracefully
./stop.sh --force           # Force stop all

# Via ZES CLI
zes status                  # Service overview
zes start                   # Start all
zes stop                    # Stop all
zes restart <svc>           # Restart single service
zes menu                    # Interactive TUI menu
```

## Core Services

### 9Router (port 20128)
- **Service:** `r9` (runsv managed)
- **Proxy:** `9router-proxy` (:8082 → :20128)
- **Binary:** `/data/data/com.termux/files/usr/bin/9router`
- **Config:** `~/.9router/`
- **DB:** `~/.9router/db/data.sqlite`
- **Auth:** CLI token in `~/.9router/auth/cli-secret`
- **API keys:** Stored in `apiKeys` table for proxy access

### Dashboard (port 8083)
- **Service:** `dashboard8083`
- **Source:** `~/dashboard_v2.py`
- **Features:** Mobile-responsive, drawer nav, sparkline history, provider table, auto-refresh

### Claude Code Proxy (port 5905)
- **Service:** `claude-proxy`
- **Source:** `~/Zes-System/scripts/claude-9router-proxy.js`
- **Purpose:** Routes Claude Code API calls through 9Router to AI providers
- **ANTHROPIC_BASE_URL:** `http://127.0.0.1:5905`

### Hermes Web Dashboard (port 8787)
- **Service:** `hermes-webui`
- **Run:** `hermes dashboard --port 8787 --host 127.0.0.1`
- **Source:** Built into hermes-agent CLI (`hermes_cli/web_dist/`)
- **Purpose:** Web UI for managing config, API keys, sessions, and chatting with the agent
- **Auth:** Uses session tokens, auto-generated on start
- **Note:** First start builds the web UI (via Vite); subsequent starts use cached build

### Hermes Gateway
- **Service:** `hermes-gateway`
- **Config:** `~/.hermes/config.yaml`
- **Cron jobs:**
  - `daily-health-check` — Every 6 hours
  - `log-cleanup` — Every 24 hours (no-agent script)
- **Commands:**
  ```bash
  hermes cron list           # List scheduled jobs
  hermes gateway run         # Start gateway
  ```

### ZES Chrome MCP (port 5901)
- **Service:** `zeschrome-mcp`
- **Source:** `~/Zes-System/zes-chrome/mcp-server/`
- **18 tools** — browse, screenshot, click, auth, system tools

### VS Code Server (port 8000)
- **Service:** `vscode-server`
- **Web VS Code** with Cline + Continue extensions

### Tor SOCKS5 (port 9050)
- **Service:** `tor`
- Provides anonymizing proxy for 9Router providers
- IP rotation: `sv restart tor` or control port command

### Headless Chrome (port 9222)
- **Service:** `chromium-cdp`
- Browser automation engine
- Used by zesChrome MCP for web tasks

### ttyd (port 7173)
- **Service:** `ttyd`
- Web terminal

### Cloudflare Tunnel
- **Service:** `cloudflare-tunnel`
- **9Router Tunnel:** `zes-9router-tunnel` (separate service)
- Provides external access through Cloudflare

### Agent Services
- **Agent UI** (:8084) — `agent-ui` — AI chat dashboard with 9Router model selection
  - **Left drawer** (☰): Actions (Context, Clear, Copy), System Tools (Status, Health, Providers, Security, Memory), Slash Commands (/plan, /tdd, /code-review, /build-fix, /verify, /help), Quick Links (Dashboard, VS Code, ttyd, Claude Proxy, 9Router)
  - Source: `~/Zes-System/services/agent-ui/agent-server.js`
  - Frontend: `~/Zes-System/services/agent-ui/index.html`
  - Endpoints: `/health`, `/api/models`, `/api/chat`, `/api/zes/execute`, `/api/zes/memory`
- **Agent Dash** — `agent-dash` — Agent monitoring REST API
- **Agent Dash Web** — `agent-dash-web` — Agent dashboard frontend

## Startup Scripts

```bash
# Start everything
~/startall.sh

# Stop everything
~/stopall.sh
```

Both scripts manage runsv services and verify port availability after startup.


## Orchestrator Management

The orchestrator skill (`~/.codex/skills/zes-orchestrator/`) provides service-aware automation:

### Service Health Dashboard

The dashboard at `http://localhost:8083` now includes:
- **Services tab** — 25 services with status icons
- **Cron tab** — 6 Hermes cron jobs with results
- **Providers tab** — 18 9Router AI providers
- **MCP tab** — 6 MCP servers
- **Audit Log tab** — Hook event feed
- **Terminal tab** — Embedded ttyd

### Automated Health Checks

The system runs 5 cron jobs every 30 minutes (script-based) and 1 health check every 360 minutes (AI-powered):

| Job | Schedule | Type |
|-----|----------|------|
| daily-health-check | every 360m | AI agent (curl checks) |
| model-rotation | */30 * * * * | Script |
| dashboard-snapshot | */30 * * * * | Script |
| ip-rotation | */30 * * * * | Script |
| eval-service-health | */30 * * * * | Script |

### Service Restart via Dashboard API

```bash
# Restart any service via API
curl http://localhost:8083/api/service/restart/dashboard8083
curl http://localhost:8083/api/service/restart/hermes-gateway
```
