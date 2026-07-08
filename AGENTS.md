# ZES System — Agent Guide (v3)

## Core Stack

```
You (NL) → Codex (superpowers) → 9Router (:20128) → 18 AI Providers
                                        ↘
           ┌──────────────────────────────────────────────────┐
           │ ZES Control Center Dashboard (:8083)             │
           │  • Services · Agent Chat · Models · Auth · Cron  │
           │  • IP Rotation Status · Event History            │
           └──────────────────────────────────────────────────┘
                                        ↘
           ┌─────────── MCP Layer (:5901) ─────────────┐
           │ zesChrome — browse, screenshot, click,     │
           │ type, extract, wait, auth, run_task         │
           └────────────────────────────────────────────┘
                                        ↘
     Hermes (5 cron jobs) · VS Code (:8000) · OpenCode (:9876)
```

## Services

| Service | Port | Runsv | Purpose |
|---------|------|-------|---------|
| **9Router** | 20128 | — | AI provider router, 18 providers |
| **Dashboard v3** | 8083 | `dashboard8083` | ZES Control Center — services, chat, models, auth, cron, history |
| **Hermes Gateway** | — | `hermes-gateway` | Cron, scheduler, agent backend |
| **zesChrome MCP** | 5901 | `zeschrome-mcp` | Codex ↔ Chrome bridge via CDP, 8 tools |
| **OpenCode** | 9876 | `opencode` | AI coding agent |
| **VS Code Server** | 8000 | `vscode-server` | Browser VS Code (Cline + Continue) |
| **Codex Server** | 5900 | — | AI API proxy + Zen gateway |
| **Headless Chrome** | 9222 | `chromium-cdp` | Browser automation (CDP) |
| **ttyd** | 7173 | `ttyd` | Web terminal |
| **Tor** | 9050/9051 | `tor` | SOCKS5 proxy + ControlPort for IP rotation |
| **SSH** | 8022 | — | Remote access |

## Dashboard API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Full system status with providers |
| `/api/history` | GET | 2h uptime history |
| `/api/agent/chat` | POST | Chat with AI via 9Router |
| `/api/agent/action` | POST | Execute browser action via MCP |
| `/api/agent/task` | POST | Schedule or run a task |
| `/api/agent/history` | GET | Agent conversation history |
| `/api/models` | GET | Available models from 9Router |
| `/api/services` | GET | Service auth status |
| `/api/mcp` | GET | MCP server health + tools |
| `/api/rotation` | GET | IP rotation status (Tor exit country) |

## IP Rotation — Tor Exit Node Cycling

**Every 30 minutes** via Hermes cron (`ip-rotation` job):
1. `SIGNAL NEWNYM` — Tor creates new circuit
2. `SETCONF ExitNodes={XX}` — Random country from: US, DE, FR, NL, CA, GB, JP, SG, CH, SE, NO, AU, KR, IE, FI
3. New exit IP verified

**Affected providers:**
- **DeepSeek** — routes through Tor SOCKS5 (`proxyEnabled=true`)
- **Zen OpenCode (Tor)** — routes through Tor
- **OpenClaw Proxy** — routes through Tor

**Tor config:** ControlPort 9051 (auth: none, localhost only)

## Hermes Cron Jobs (5 active)

| Job | Schedule | Purpose |
|-----|----------|---------|
| `daily-health-check` | every 360m | Check all services, report issues |
| `log-cleanup` | every 1440m | Clean stale logs and history |
| `model-rotation` | weekly Sun 00:00 | Check all provider health |
| `dashboard-snapshot` | every 30 min | Save service status snapshot |
| `ip-rotation` | every 30 min | Rotate Tor exit IP/country |

## Dashboard Persistence
- Active tab saved to `localStorage` (`zesActiveTab`)
- Chat history saved to `localStorage` (`zesChatHistory`, `zesChatState`)
- Refresh rate saved to `localStorage` (`dashboardRefresh`)

## Quick Reference

```bash
# Service management
sv status /data/data/com.termux/files/usr/var/service/*
sv restart <name>

# 9Router CLI token
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")

# Dashboard
curl -s http://localhost:8083/api/status
curl -s http://localhost:8083/api/rotation

# Tor IP rotation (manual)
python3 -c "import socket;s=socket.socket();s.connect(('127.0.0.1',9051));s.send(b'AUTHENTICATE\r\nSIGNAL NEWNYM\r\n');print(s.recv(1024).decode());s.close()"

# Hermes cron
hermes cron list
```
