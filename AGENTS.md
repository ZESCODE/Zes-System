# ZES System — Unified Agent Instructions

**Version:** 3.5.0  
**Scope:** This file governs all agents operating within the ZES (ZES Enterprise System) environment. It supersedes individual AGENTS.md files where conflicts exist.

---

## 1. System Overview

ZES is a unified personal AI system running on Termux (Android). It orchestrates three primary agents — **Codex CLI**, **Hermes Agent**, and **Claude Code** — plus supporting services (9Router AI Gateway, amux Agent Control Plane, ZES Dashboard).

```
┌──────────────────────────────────────────────────────┐
│                    ZES System v3.6                      │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Codex   │  │  Hermes  │  │ Claude   │            │
│  │  CLI     │  │  Agent   │  │  Code    │            │
│  │ (coder)  │  │(orchestr)│  │ (review) │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │             │                   │
│       └─────────┬───┴─────────────┘                   │
│                 ▼                                      │
│       ┌──────────────────┐                            │
│       │  ZES Memory Hub   │  (unified memory)          │
│       └──────────────────┘                            │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │BitRouter │  │ AI-Proxy │  │ ZES Dashboard    │    │
│  │ :4356    │  │ :20129   │  │ (shadcn + Vite)  │    │
│  │GPT+Gemini│  │Groq+OR+  │  │ :5050            │    │
│  │          │  │Mistral+NV│  │                   │    │
│  └──────────┘  └──────────┘  └──────────────────┘    │
│                                                       │
│  ┌──────────┐  ┌──────────┐                           │
│  │   Tor    │  │iprotate  │  ← IP rotation layer      │
│  │ :9050    │  │15min     │                           │
│  └──────────┘  └──────────┘                           │
└──────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Codex is the primary coder** — Execution, planning, file editing, repo work
2. **Claude Code is the secondary coder** — Code review, parallel tasks, multi-agent orchestration
3. **Hermes is the memory hub & orchestrator** — All memories flow through ZESMemoryProvider
4. **9Router is the AI gateway** — Routes all LLM requests, manages API keys
5. **amux is the agent control plane** — Runs, monitors, and orchestrates parallel agent sessions
6. **Skills are shared** — 81 skills across 14 categories, available to all agents
7. **Services communicate via HTTP/WebSocket** — REST APIs, file-based bridges

---

## 2. The Trinity

| Agent | Role | Saying | Config | Entry |
|-------|------|--------|--------|-------|
| **Codex** | Primary coder — the sharp scalpel | *"Unverified code is broken code"* | `~/.codex/AGENTS.md` | `npx codexapp` |
| **Claude Code** | Secondary coder — the face | *"Code it right, test it clean"* | `~/.claude/AGENTS.md` | `claude` via amux |
| **Hermes** | Orchestrator — the steady hand | *"I build to create continuity"* | `~/.hermes/soul.md` | r·sv hermes-gateway |

---

## 3. Component Roles

### Codex CLI
- **AGENTS.md:** `~/.codex/AGENTS.md` (v1.1.0)
- **WORKFLOW.md:** `~/.codex/WORKFLOW.md` — 4-Phase QC workflow (Clarify → Plan → Implement → QC → Report)
- **Skills:** 88 skill dirs (81 effective) at `~/.codex/skills/`
- **MCP:** ZES Memory Hub bridge, GitHub, Context7, Exa, Playwright, Sequential Thinking
- **Memory:** MCP-backed via `~/.zes/memory_hub.sqlite`
- **Entry:** `npx codexapp` (port `:5900`) or direct CLI

### Claude Code
- **AGENTS.md:** `~/.claude/AGENTS.md` (v1.0.0)
- **Runtime:** Node.js, routed through 9Router via `ANTHROPIC_BASE_URL=http://127.0.0.1:5905`
- **Managed by:** amux for parallel sessions
- **Memory:** Queries ZES Memory Hub via `zes-memory` CLI
- **Settings:** `~/.claude/settings.json` — references AGENTS.md + memory context

### Hermes Agent
- **Soul:** `~/.hermes/soul.md` (v1.0.0) — custom ZES identity
- **Config:** `~/.hermes/config.yaml` — routes 100% through 9Router
- **Version:** 0.18.2
- **Dashboard:** `:9119`
- **Memory provider:** holographic → `~/.zes/memory_hub.sqlite`
- **Cron:** Memory sync every 30 min

### 9Router AI Gateway
- **Path:** `~/9router/`
- **Port:** `:20128` (OpenAI-compatible endpoint)
- **Providers:** OpenAI, Anthropic, Groq, DeepSeek, Gemini, and 30+ more
- **Config:** `~/9router/.env`, `~/9router/data/`

### amux Agent Control Plane
- **Path:** `~/amux-fresh/`
- **Port:** `:8822` (web dashboard)
- **Config:** `~/.amux/config.yaml`
- **Projects:** zes-system, workspace, claude-code, codex
- **Features:** Self-healing watchdog, kanban board, session management

### ZES Dashboard
- **Stack:** React 19 + shadcn/ui + Vite 8 + Tailwind CSS v4
- **Port:** `:5050` (Vite dev server)
- **Source:** `~/zes-system-v2/`
- **Backend:** Flask API on `:5002` (runit: `zes-flask-api`)
- **Pages:** Dashboard, Processes, System, Services, Skills Manager, Hermes Chat, 9Router, Design Studio, Kanban, Claude, Architecture

---

## 4. Unified Memory Architecture

### Memory Stores

| Store | Location | Type | Agent Access |
|-------|----------|------|-------------|
| ZES Memory Hub | `~/.zes/memory_hub.sqlite` | SQLite + FTS5 | All agents (primary) |
| Codex MCP Memory | `~/.zes/memory_hub.sqlite` | via MCP bridge | Codex CLI |
| Codex raw memories | `~/.codex/memories/raw_memories.md` | Markdown | Codex CLI |
| Hermes native | `~/.hermes/MEMORY.md` | Markdown | Hermes |
| amux transcripts | `~/.amux/transcripts/` | JSONL | amux sessions |
| Claude Code projects | `~/.claude/projects/*/CLAUDE.md` | Markdown | Claude Code |

### Sync Flow

```
Codex CLI ──zes-memory-sync (daemon)──→ ZES Memory Hub ←── Hermes (holographic)
    │                                            │
    └── MCP bridge server ──────────────────────┘
         (memory_write, memory_search, etc.)
```

### CLI Usage
```bash
zes-memory status       # Hub health & count
zes-memory list 20      # Recent memories
zes-memory search <q>   # FTS5 full-text search
zes-memory write <txt>  # Write memory entry
```

---

## 5. Port & Service Reference

| Service | Port | Status | Managed By |
|---------|------|--------|------------|
| BitRouter AI Gateway | `:4356` | ✅ | runsv (bitrouter) |
| AI-Proxy (Groq/OR/Mistral/NV) | `:20129` | ✅ | runsv (ai-proxy) |
| ZES Dashboard (Vite) | `:5050` | ✅ | runsv (zes-dashboard) |
| Flask API | `:5002` | ✅ | runsv (zes-flask-api) |
| 9Router (legacy) | `:20128` | ⚠️ | runsv (9router-proxy) — deprecated |
| amux Control Plane | `:8822` | ✅ | runsv (amux) |
| Hermes Dashboard | `:9119` | ✅ | runsv (hermes-dashboard) |
| Hermes Gateway | — | ✅ | runsv (hermes-gateway) |
| Tor SOCKS5 | `:9050` | ✅ | runsv (tor) |
| Tor Control | `:9051` | ✅ | runsv (tor) |
| iprotate (Tor IP rotation) | — | ✅ | runsv (zes-ip-rotator) |
| Control Center | `:8083` | ✅ | legacy |
| ZES Memory Sync | — | ✅ | runsv (zes-memory-sync) |
| ttyd web terminal | `:7173` | ✅ | runsv |

### Provider Chain
```
All agents ──→ OpenCode ──→ BitRouter (:4356) ──→ OpenAI / Google Gemini
                  │
                  └──→ AI-Proxy (:20129) ──→ Groq / OpenRouter / Mistral / NVIDIA
Claude Code ──→ BitRouter (:4356) ──→ backed by API key (needs credit balance)
Hermes ──→ BitRouter (:4356) ──→ openai/gpt-5.4-mini (default)
```

---

## 6. Skills

**81 skills across 14 categories** at `~/.codex/skills/`. Shared across all agents.

| Category | Count | Skills |
|----------|-------|--------|
| ZES | 29 | agentic-core, brainstorming, dashboard, design, memory-ops, provider-manager, etc. |
| Core Workflow | 8 | tdd-workflow, verification-loop, coding-standards, error-handling, ecc-integration, etc. |
| Backend | 8 | backend-patterns, api-design, fastapi-patterns, postgres-patterns, python-patterns, etc. |
| Integration | 6 | composio-cli, flightclaw, search-codex-chats, telegram-bridge, 9router, etc. |
| Frontend | 6 | frontend-patterns, react-patterns, react-performance, vite-patterns, dashboard-builder, etc. |
| Project Workflow | 5 | plan-orchestrate, delivery-gate, context-budget, cost-tracking, repo-scan |
| Security | 4 | security-review, security-scan, gateguard, safety-guard |
| Testing & QA | 4 | browser-qa, python-testing, e2e-testing, benchmark |
| Research | 3 | deep-research, documentation-lookup, exa-search |
| System | 2 | imagegen, system-orchestrator |
| Agent | 2 | agentic-engineering, knowledge-ops |
| Discovery | 2 | skill-scout, skill-stocktake |
| Design | 1 | designmd |
| Free AI | 1 | freellm |

---

## 7. Service Management (runit)

```bash
sv start/stop/restart/status zrouter-proxy     # 9Router (:20128)
sv start/stop/restart/status zes-flask-api     # Flask API (:5002)
sv start/stop/restart/status zes-dashboard     # Vite Dashboard (:5050)
sv start/stop/restart/status amux              # amux Control Plane (:8822)
sv start/stop/restart/status hermes-gateway    # Hermes gateway
sv start/stop/restart/status hermes-dashboard  # Hermes WebUI (:9119)
sv start/stop/restart/status zes-memory-sync   # Memory hub sync
```

## 8. Common Commands

```bash
# Health
curl http://127.0.0.1:5002/api/health      # System health
curl http://127.0.0.1:5002/api/system      # System info
curl http://127.0.0.1:5002/api/services    # All services
curl http://127.0.0.1:5002/api/skills      # All skills (81)

# Memory
zes-memory status
zes-memory list 20
zes-memory search <query>

# Agents
npx codexapp            # Codex app-server (:5900)
claude                  # Claude Code (via amux for parallel)
sv restart hermes-gateway  # Restart Hermes

# Dashboard
http://127.0.0.1:5050   # ZES Dashboard (Vite)
http://127.0.0.1:8822   # amux Control Plane
http://127.0.0.1:9119   # Hermes Dashboard
http://127.0.0.1:8083   # Control Center (legacy)
```

## 9. Key Paths

| Resource | Path |
|----------|------|
| ZES Dashboard Source | `~/zes-system-v2/` |
| Codex Config | `~/.codex/config.toml` |
| Codex AGENTS.md | `~/.codex/AGENTS.md` |
| Codex WORKFLOW.md | `~/.codex/WORKFLOW.md` |
| Codex Skills | `~/.codex/skills/` (81 skills) |
| Claude Code AGENTS.md | `~/.claude/AGENTS.md` |
| Hermes Source | `~/hermes-agent-full/` |
| Hermes Config | `~/.hermes/config.yaml` |
| Hermes Soul | `~/.hermes/soul.md` |
| ZES Memory Hub DB | `~/.zes/memory_hub.sqlite` |
| ZES Memory CLI | `~/.local/bin/zes-memory` |
| amux Source | `~/amux-fresh/` |
| amux Config | `~/.amux/config.yaml` |
| 9Router | `~/9router/` |
| Credentials | `~/.secure-credentials/master.env` |
