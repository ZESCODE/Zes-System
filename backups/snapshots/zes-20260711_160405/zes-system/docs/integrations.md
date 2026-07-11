# ZES System Integrations

## From arfaXdev/Termux-Claw

The Termux-Claw repo contains a complete OpenClaw v2.0 ecosystem built around Ollama.
Key components adapted for ZES:

### Swarm Orchestrator (`services/zes_swarm.py`)

Multi-agent workflow runner:
- 5 agents: planner, coder, reviewer, writer, summarizer
- All routed through 9Router (not Ollama)
- Chain execution: POST `/api/swarm/chain` with steps array
- Single agent: GET `/api/swarm/run/<agent-id>?q=<task>`

Start: `python3 services/zes_swarm.py --port 5030`

### Service Toggle (`services/service_toggle.py`)

Manage all ZES runsv services from one command:
- `python3 services/service_toggle.py list` - show all services
- `python3 services/service_toggle.py restart dashboard` - restart dashboard

### Tool Scanner (`services/tool_scanner.py`)

Scans Termux bin directories and runsv services:
- `python3 services/tool_scanner.py` - outputs to `~/.zes/discovered_tools.json`

### OpenClaw Config (`services/openclaw.json`)

9Router-native agent configuration:
- 3 agents: ZES Core (Claude Sonnet 4.6), ZES Coder (DeepSeek V4 Flash), ZES Fast (Groq Llama)
- Each with fallback models
- Configured to use Hermes gateway for scheduling

## Architecture Comparison

| Aspect | Termux-Claw (original) | ZES (adapted) |
|--------|----------------------|---------------|
| Model router | Ollama + liteLLM | 9Router |
| Agents | Qwen2.5 models | Claude + DeepSeek + Groq |
| Service mgmt | PID-based | runsv |
| Orchestration | Hermes WebUI | Hermes Gateway |
| Proxy | multi_model_proxy.py (:4000) | 9Router (:20128) |
| Swarm | Ollama-native | 9Router-native |

## ZES Chrome Extension

The ZES Chrome extension (forked from ChromePilot) provides an AI-powered browser 
agent connected to 9Router. The extension lives at:

- **Source repo**: `Zes-System/zes-chrome/` (custom source)
- **Deployed fork**: `ZES-project/Zeschrome/` (ChromePilot fork, 1.4MB sidepanel)

### Gemini → 9Router Proxy

The ChromePilot fork bundles the Google GenAI SDK, which requires a Gemini API key.
Three layers intercept this and route through 9Router:

1. **`js/gemini-proxy.js`** — Pre-load script that provides a dummy API key and
   intercepts `generativelanguage.googleapis.com` fetch calls → 9Router
2. **`js/voicekeyboard.js`** — Falls back to 9Router via background script
3. **`js/background.js`** — `aiChat()` + `transcribeAudio` handlers via 9Router

### Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:20128/v1` | 9Router AI provider |
| `http://localhost:5901/mcp` | MCP server |
| `http://localhost:9222` | Chrome CDP debug |
| `chrome-extension://cnhdhgglemkhmhfifebllhieckiogchc/` | Extension ID |

### Debug Mode

Toggle via the floating button in the sidepanel (bottom-right). When enabled,
bypasses Google OAuth and uses mock user info.

```
chrome.storage.local.set({ debugMode: true })
```

### Files Modified for Proxy

| File | Change |
|------|--------|
| `sidepanel.html` | Added `<script src="js/gemini-proxy.js">` before module |
| `js/gemini-proxy.js` | New: storage intercept + fetch reroute |
| `js/background.js` | Fixed AI_API_URL, added transcribeAudio handler |
| `js/voicekeyboard.js` | Added sendTo9Router fallback function |

## OpenClaw Patterns (Android Assistant — v2026.6.1)

Five modules were ported from [openclaw-android-assistant](https://github.com/openclaw/openclaw) 
(19,872 files, TypeScript monorepo with embedded Android APK) into `zes-chrome/mcp-server/`:

### Ported Modules

| Module | File | Lines | Source Pattern |
|--------|------|-------|----------------|
| CDP Helpers | `mcp-server/cdp-helpers.js` | 167 | `extensions/browser/src/browser/cdp.ts` — WS management, screenshot (viewport + full-page), target filtering, `normalizeCdpWsUrl` |
| Agent Stream | `mcp-server/agent-stream.js` | 105 | `packages/agent-core/src/agent-loop.ts` — event-driven lifecycle with `push/subscribe/end`, SSE formatting |
| Tool Repair | `mcp-server/tool-repair.js` | 161 | `packages/tool-call-repair/` — fuzzy name matching (40+ misspellings), field aliasing (css→selector, href→url), schema validation |
| Schema Validate | `mcp-server/schema-validate.js` | 71 | `packages/llm-core/src/validation.ts` — JSON Schema-compatible tool argument validation with type checking |
| 9Router Provider | `mcp-server/9router-provider.js` | 222 | `extensions/litellm/` + `plugin-sdk/provider-auth.ts` — model catalog (8 models), streaming, embeddings, auth abstraction |
| Gateway Protocol | `mcp-server/gateway-protocol.js` | 131 | `packages/gateway-protocol/` — typed event types (14), EventBus with wildcard listeners, SSE formatting |

### Skills Ported from `.agents/skills/`

| Skill | File | Source |
|-------|------|--------|
| Technical Documentation | `.agents/skills/technical-documentation/SKILL.md` | Direct copy |
| ZES Debugging | `.agents/skills/openclaw-debugging/SKILL.md` | Adapted: service checks, 9Router diagnostics, Chrome CDP, MCP health |
| GitCrawl ZES | `.agents/skills/gitcrawl-zes/SKILL.md` | Adapted: ZES repo commands, path references |

### Cline + Continue VS Code Config

Cline and Continue are configured through VS Code Server (`:8000`) to use 9Router:

| Plugin | Provider | Model | MCP |
|--------|----------|-------|-----|
| **Cline** | OpenAI-compat → `:20128/v1` | `ds/deepseek-v4-flash` | `zes-chrome` (stdio) + `zes-9router` (http) |
| **Continue** | OpenAI-compat → `:20128/v1` | 5 models (Claude, DeepSeek, GPT-5.4, Groq, Gemini) | `zes-chrome-mcp` (http) |

Config files:
- `~/.config/Code-Server/data/User/settings.json` — Cline + Continue settings
- `~/.config/Code-Server/.../saoudrizwan.claude-dev/settings/cline_mcp_settings.json` — Cline MCP
- `~/.continue/config.json` — Continue models + MCP
- `~/.local/bin/zeschrome-mcp-bridge` — stdio↔HTTP MCP bridge for Cline
