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
├── OpenCode                — AI coding agent (:9876)
├── VS Code Server          — Web VS Code with Cline/Continue (:8000)
├── VS Code Mobile Panel    — Mobile-optimized VS Code wrapper (:8001)
├── Agent Dashboard API     — Agent monitoring REST API (:8002)
├── Agent Dashboard Web     — Agent dashboard frontend (:8003)
├── Codex Server            — AI API proxy + Zen gateway (:5900)
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
| **Dashboard v3** | 8083 | `dashboard8083` | ✅ running | ZES Control Center |
| **VS Code Server** | 8000 | `vscode-server` | ✅ running | Web VS Code (Cline + Continue + Copilot) |
| **VS Code Mobile** | 8001 | `vscode-mobile` | ✅ running | Mobile-optimized VS Code with touch zoom, toolbar, 2-col split |
| **Hermes Gateway** | 8787 | `hermes-gateway` | ✅ running | Cron, scheduler, agent backend |
| **Agent Dashboard API** | 8002 | `agent-dash` | ✅ running | Agent monitoring REST API |
| **Agent Dashboard Web** | 8003 | `agent-dash-web` | ✅ running | Agent dashboard frontend |
| **zesChrome MCP** | 5901 | `zeschrome-mcp` | ✅ running | Codex ↔ Chrome bridge (14 tools) |
| **OpenCode** | 9876 | `opencode` | ✅ running | AI coding agent |
| **Headless Chrome** | 9222 | `chromium-cdp` | ✅ running | Browser automation (CDP) |
| **ttyd** | 7173 | `ttyd` | ✅ running | Web terminal |
| **Tor** | 9050 | `tor` | ✅ running | SOCKS5 proxy + ControlPort (9051) |
| **Codex Server** | 5900 | — | ✅ running | AI API proxy + Zen gateway |
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
└── .9router/                 — 9Router database and config
```

## Links

- **Dashboard**: http://localhost:8083
- **VS Code**: http://localhost:8000
- **VS Code (Mobile)**: http://localhost:8001
- **Agent Dashboard**: http://localhost:8003
- **ttyd (Terminal)**: http://localhost:7173
- **OpenCode**: http://localhost:9876
