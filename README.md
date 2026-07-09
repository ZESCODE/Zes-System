# ZES System

> **ZES Control Center** — Self-hosted AI infrastructure: provider router, agent orchestration, and service management on Android/Termux.

## Dashboard

**URL:** http://localhost:8083

The ZES Control Center shows all services, AI provider status, system environment, and sparkline history — with a mobile-responsive left drawer nav and custom **Z** logo with gradient border.

## Architecture

```
Termux (Android aarch64) + Debian proot
├── 9Router v0.5.20       — AI provider router (:20128, 18 providers)
├── Hermes Gateway        — AI agent cron, scheduler, automation
├── OpenCode              — AI coding agent (:9876)
├── VS Code Server        — Web VS Code with Cline/Continue (:8000)
├── Codex App Server      — AI API proxy + Zen gateway (:5900)
├── Dashboard             — ZES Control Center (:8083)
├── runit (runsv)         — Service supervision
├── Tor                   — Anonymizing proxy (:9050)
├── Headless Chromium     — Browser automation (:9222)
└── ttyd                  — Web terminal (:7173)
```

## 9Router — 18 Providers

### OAuth
- **GitHub Copilot** — `arfaXdev`, free Copilot tier
- **Cline** — `arfaxtrade@gmail.com` via WorkOS
- **Codex (OpenAI)** — `arfaxtrade@gmail.com` free tier
- **Gemini CLI** — Google Cloud OAuth
- **Qoder** — Device auth, 30-day session
- **Kiro** — ⚠️ AWS Builder ID OAuth expired, needs re-auth

### API Key
- NVIDIA NIM, Groq, Gemini, DeepSeek, Cerebras, OpenRouter, Anthropic, Cloudflare AI, **Mistral AI**

### OpenAI-Compatible Nodes
| Prefix | Name | Endpoint | Proxy |
|--------|------|----------|-------|
| `oz` | Zen OpenCode | :5900/codex-api/zen-proxy/v1 | Direct |
| `he` | Hermes AI | :8787 | Tor SOCKS5 |
| `oc` | OpenClaw Proxy | :4040/v1 | Tor SOCKS5 |

## Codex Configuration

Codex routes through 9Router for all AI calls:

```toml
model = "groq/llama-3.3-70b-versatile"       # Fast, direct routing
model_provider = "9router"
[agents.subagent]
model = "gh/gpt-5.4-mini-free-auto"           # GitHub Copilot free tier
```

Uses OpenAI Responses API wire format. `OPENAI_API_KEY` env var cleared to prevent routing conflicts.

## Installed Skills (7 personal + superpowers)

### Custom Skills
- **service-management** — runsv service control, proot access, port checks
- **9router-provider-check** — CLI token gen, provider status, model routing
- **spec-driven-development** — Write spec before code (*from addyosmani/agent-skills*)
- **incremental-implementation** — Build in testable slices (*from addyosmani/agent-skills*)
- **source-driven-development** — Understand code before changing (*from addyosmani/agent-skills*)
- **code-simplification** — Reduce complexity, clarify logic (*from addyosmani/agent-skills*)
- **ci-cd-and-automation** — Automate builds, services, deployments (*from addyosmani/agent-skills*)

### Superpowers (loaded via plugin)
- brainstorming, dispatching-parallel-agents, executing-plans, writing-plans
- test-driven-development, systematic-debugging
- requesting-code-review, receiving-code-review, finishing-a-development-branch
- verification-before-completion, subagent-driven-development

## Services

| Service | Port | Runsv | Purpose |
|---------|------|-------|---------|
| Dashboard | 8083 | `dashboard8083` | ZES Control Center |
| 9Router | 20128 | — | AI provider router |
| Codex Server | 5900 | — | AI API proxy + Zen gateway |
| Hermes Gateway | — | `hermes-gateway` | Cron, scheduler, agent backend |
| OpenCode | 9876 | `opencode` | AI coding agent |
| VS Code Server | 8000 | `vscode-server` | Web VS Code |
| ttyd | 7173 | `ttyd` | Web terminal |
| Headless Chrome | 9222 | `chromium-cdp` | Browser automation |
| Tor | 9050 | `tor` | SOCKS5 proxy |
| Socat | 8090 | `socat` | TCP bridge |
| SSH | 8022 | — | Remote access |
| ZES Chrome Ext | — | `zeschrome-mcp` | Browser AI agent (forked ChromePilot + 9Router) |

## ZES Chrome Extension

The ZES Chrome extension provides an AI browser agent with voice input and automation.
Forked from ChromePilot, with Gemini API calls intercepted and routed through 9Router.

### Key Files (deployed at `ZES-project/Zeschrome/`)

| File | Purpose |
|------|---------|
| `js/gemini-proxy.js` | Intercepts Gemini SDK auth & routes to 9Router |
| `js/background.js` | Service worker with 9Router provider (`:20128/v1`) |
| `js/voicekeyboard.js` | Voice input with 9Router fallback |
| `js/debug-toggle.js` | Debug mode bypass for Google OAuth |

### Architecture

```
Sidepanel → gemini-proxy.js (dummy key + fetch reroute) → 9Router (:20128)
     ↕                         ↕
Background SW ←→ MCP Server (:5901) ←→ Chrome CDP (:9222)
```

Extension ID: `cnhdhgglemkhmhfifebllhieckiogchc`

## Quick Links

| Service | URL |
|---------|-----|
| ZES Dashboard | http://localhost:8083 |
| 9Router | http://localhost:20128 |
| Hermes WebUI | http://localhost:8787 |
| Codex Server | http://localhost:5900 |
| Web Terminal | http://localhost:7173 |
| OpenCode Server | http://localhost:9876 |
| VS Code Server | http://localhost:8000 |

## Common Commands

```bash
# Start all services
bash ~/startall.sh

# Stop all services
bash ~/stopall.sh

# Service management
sv status /data/data/com.termux/files/usr/var/service/*
sv restart dashboard8083

# 9Router API
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers

# Dashboard API
curl -s http://localhost:8083/api/status
```

## Gmail Integration

- **Composio SDK** — Gmail OAuth (`arfaxtrade@gmail.com`)
- **IMAP/SMTP** — Alternative email client via `gmail-tool`

## Integrated Modules (from Termux-Claw)

The following modules from [arfaXdev/Termux-Claw](https://github.com/arfaXdev/Termux-Claw) have been adapted for 9Router:

| Module | File | Port | Purpose |
|--------|------|------|---------|
| **Swarm Orchestrator** | `services/zes_swarm.py` | 5030 | Multi-agent workflows via 9Router |
| **Service Toggle** | `services/service_toggle.py` | — | runsv-aware service management |
| **Tool Scanner** | `services/tool_scanner.py` | — | Discover executables and services |
| **Context Feeder** | `services/context_feeder.py` | — | Watch workspace for agent context |
| **OpenClaw Config** | `services/openclaw.json` | — | Agent orchestration with 9Router |

Start the swarm:
```bash
python3 ~/Zes-System/services/zes_swarm.py --port 5030 &
```

List/toggle services:
```bash
python3 ~/Zes-System/services/service_toggle.py list
```

## Plugins

See `plugins/README.md` for plugin integration details.
