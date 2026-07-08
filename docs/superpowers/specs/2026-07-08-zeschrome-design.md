# zesChrome — AI Browser Agent Extension

**Date:** 2026-07-08
**Status:** Draft Design
**System:** ZES (Android Termux + Proot)

---

## 1. Overview

zesChrome is a Chrome extension that brings Codex-style AI agent intelligence directly into the browser. It combines a chat side panel with autonomous browser control (computer use), routing all AI calls through the local 9Router instance for provider flexibility.

### Goals
- Persistent AI assistant in the browser (side panel + popup)
- Autonomous browser control via vision + mouse simulation
- Connect to Gmail, Drive, Calendar, Sheets, GitHub, Slack via Composio
- Use 9Router's 18 AI providers (multi-model agent: planner + executor)
- Integrate with ZES dashboard (`:8083`) for auth, history, settings
- Hermes cron jobs for recurring tasks

### Non-Goals
- Not a replacement for the full Codex CLI — focuses on browser-specific tasks
- No Rust-compiled dependencies (Android-incompatible)
- No external tunnels or fleet orchestration

---

## 2. Architecture

```
Browser Extension
├── Popup (quick actions, 320×400)
├── Side Panel (chat + agent, full panel)
└── Background Service Worker
        │
        ▼ HTTP API
Dashboard (:8083) — ZES Control Center
├── /api/agent/* — Chat, actions, history
├── /api/services/* — Composio OAuth, token mgmt
├── /api/models/* — 9Router model listing
└── Hermes integration for cron
        │
        ▼
9Router (:20128) — AI Provider Router
├── Claude (planner/orchestrator)
├── Gemini Computer Use (vision/actions)
├── Groq (fast text extraction)
└── 15+ other providers
        │
        ▼
Composio API — Service Integrations
├── Gmail, Drive, Calendar
├── Sheets, GitHub, Slack/Discord
└── OAuth token management
```

### Data Flow

1. User types task in Side Panel
2. Background SW sends to Dashboard API
3. Dashboard routes through 9Router to appropriate model
4. For computer-use: extension captures screenshot, Dashboard proxies to Gemini via 9Router
5. Response flows back: 9Router → Dashboard → Extension → User
6. Service calls (Gmail, Drive etc.) go through Dashboard → Composio API

---

## 3. Extension Structure

### File Layout
```
zes-chrome/
├── manifest.json           # Manifest V3
├── popup.html              # Popup UI
├── popup.js                # Popup logic
├── popup.css               # Popup styles
├── sidepanel.html          # Side Panel UI
├── sidepanel.js            # React-based chat + agent UI
├── sidepanel.css           # Side Panel styles
├── background.js           # Service worker
├── content.js              # Page content script
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── lib/
    ├── api-client.js       # Dashboard API calls
    ├── composio-auth.js    # OAuth token management
    ├── computer-use.js     # Screenshot + action dispatch
    └── utils.js            # Shared utilities
```

### Manifest V3 Features
- `sidePanel` API for persistent side panel
- `scripting` + `activeTab` for content injection
- `storage` + `unlimitedStorage` for local data
- `identity` for OAuth flows
- Host permissions: `<all_urls>` (for computer-use screenshots)
- Commands: `Ctrl+Shift+S` (open side panel)

### Popup (`popup.html`)
- **Size:** 320×400px
- **Sections:**
  - Agent on/off toggle
  - Recent tasks (last 5)
  - Service connection status (Gmail, Drive etc.)
  - "Open Side Panel" button
  - Settings shortcut
- **Behavior:** Opens on toolbar icon click. Sends quick commands via `chrome.runtime.sendMessage`

### Side Panel (`sidepanel.html`)
- **Full Chrome side panel** — persists across tabs
- **Sections:**
  - Chat interface (multi-turn conversation)
  - Agent control panel (status, pause/resume, cancel)
  - Service browser (mini views for Gmail, Drive files)
  - Task history & favorites
  - Record/playback automation rules
- **Opens via:** `Ctrl+Shift+S` or toolbar icon action

### Background Service Worker (`background.js`)
- **Responsibilities:**
  - Tab management (track active tab for computer-use)
  - Screenshot capture (`chrome.tabs.captureVisibleTab`)
  - Content script injection (`chrome.scripting.executeScript`)
  - Message routing between popup ↔ side panel ↔ dashboard API
  - Offscreen document for audio (if speech input needed)
- **No direct API calls to 9Router** — all go through Dashboard

### Content Script (`content.js`)
- **Injected into:** `<all_urls>` at `document_idle`
- **Functions:**
  - Detect page structure (forms, buttons, inputs)
  - Execute click/type/scroll commands from agent
  - Extract page text for context
  - Report page state back to background

---

## 4. Dashboard Integration

### New API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/agent/chat` | Send chat message, get AI response |
| POST | `/api/agent/action` | Execute computer-use action (screenshot → Gemini) |
| POST | `/api/agent/task` | Create scheduled task (→ Hermes) |
| GET | `/api/agent/history` | Get conversation history |
| GET | `/api/services` | List service auth status |
| POST | `/api/services/auth` | Trigger Composio OAuth flow |
| POST | `/api/services/revoke` | Revoke service access |
| GET | `/api/models` | Available models from 9Router |

### Dashboard UI Additions
- **Agent Tab:** Active tasks, agent status, manual override
- **Service Auth Tab:** Composio OAuth buttons, token status, refresh
- **Settings Tab:** Default model per task, safety levels, scheduled tasks
- **History Tab:** All agent actions, model costs, token usage

---

## 5. Multi-Model Agent Strategy

### Model Routing

| Role | Model | Provider | Purpose |
|------|-------|----------|---------|
| **Planner** | Claude Sonnet/Opus | 9Router (anthropic) | Decompose tasks, plan steps |
| **Computer Use** | Gemini 2.5 Computer Use | 9Router (gemini-cli) | Vision + mouse/click simulation |
| **Text Extraction** | Llama 3.3 70B or Groq | 9Router (groq/cf) | Fast page text analysis |
| **Chat** | Claude Haiku or GPT-5 | 9Router (gh/opencode) | Casual conversation |
| **Services** | Claude Haiku | 9Router | Tool-calling for Gmail/Drive |

### Agent Flow
1. **Planning Phase:** Claude receives task, breaks into steps
2. **Execution Phase:** For each step:
   - Screenshot page → Gemini Computer Use → action commands
   - Type text / click buttons via content script
   - Call services (Gmail etc.) via Composio
3. **Review Phase:** Fast model extracts page state, reports to planner
4. **Iteration:** Planner decides next step or declares done

---

## 6. Service Integrations (Composio)

### Configured Services
- **Gmail** — Read, send, search, compose drafts
- **Drive** — List, read, upload, search files
- **Calendar** — Check schedule, create events
- **Sheets** — Read/write spreadsheet data
- **GitHub** — Search repos, read PRs, create issues
- **Slack** — Send messages, search channels

### OAuth Flow
1. User clicks "Connect Gmail" in Dashboard
2. Dashboard opens Composio OAuth URL in new tab
3. User authorizes → Composio returns tokens
4. Dashboard stores tokens, extension reads via API
5. Agent uses tokens for service calls when needed

---

## 7. Hermes Cron Integration

### Scheduled Tasks (via Hermes)
- **Daily Email Summary** — Read last 24h Gmail, summarize key messages
- **Calendar Check** — Morning: show today's events
- **Web Scrape Task** — Periodic check of specific pages
- **Log Cleanup** — Weekly purge of old agent history
- **Model Rotation** — Switch primary model if rate-limited

---

## 8. Development Plan

### Phase 1: Scaffold Extension (Day 1)
- Create `zes-chrome/` directory structure
- Write `manifest.json` with all permissions
- Implement basic Popup (toggle + status)
- Implement basic Side Panel (chat shell)

### Phase 2: Dashboard API (Day 2)
- Add agent endpoints to `:8083` dashboard
- Implement 9Router proxy in dashboard
- Add Composio OAuth endpoints

### Phase 3: Computer-Use Engine (Day 3)
- Implement screenshot capture in background SW
- Build Gemini Computer Use integration
- Inject content script for click/type/scroll

### Phase 4: Service Integrations (Day 4)
- Connect each service via Composio
- Build service browser views in side panel

### Phase 5: Agent Logic (Day 5)
- Implement multi-model planner/executor loop
- Add safety confirmations
- Conversation history + persistence

### Phase 6: Hermes + Cron (Day 6)
- Integrate with Hermes for scheduled tasks
- Add recurring task management UI

### Phase 7: Polish & Testing (Day 7)
- Mobile-responsive side panel
- Performance optimization
- Edge case handling

---

## 9. Dependencies

| Service | Port | Required? |
|---------|------|-----------|
| 9Router | 20128 | Required — all AI calls |
| Dashboard | 8083 | Required — API proxy + auth |
| Hermes | 8787 | Optional — cron/scheduler |
| Composio | — | Required — service OAuth |
| Headless Chrome | 9222 | Optional — computer-use debugging |

### Credentials
- Composio API key: `ak_aeZUsOJY8PCeLchjGEMy`
- Gmail: `arfaxtrade@gmail.com` (app password: `tesr blce lmwh eeje`)
- Mistral API key: `vTYz0IEIkKvgYOYARr9u7576UcEFEqp3`

---

## 10. Open Questions

1. Should the side panel use React (heavier) or vanilla JS (lighter) for the chat UI? → **React** (reuse existing ChromePilot Pro patterns)
2. Should computer-use screenshots be processed locally or via dashboard? → **Dashboard** (keeps extension thin)
3. Storage format for conversation history? → **JSON via Dashboard API** (centralized, accessible from mobile)

---

## Appendix: Key Code References

### From Existing srcplugin (Abra Cadabra)
- `background/gemini_computer_use_refactored.js` — Full computer-use engine
- `background/gemini_modules/api_handler.js` — Gemini API call pattern
- `modules/click_simulator.js` — Click simulation
- `modules/text_input_simulator.js` — Text input
- `modules/element_finder.js` — Element detection

### From Existing Zeschrome (ChromePilot Pro)
- `manifest.json` — V3 manifest reference
- `sidepanel.html/css` — Side panel structure
- `background.js` — Service worker patterns
- `js/speechify.js` — Speech-to-text (optional)
