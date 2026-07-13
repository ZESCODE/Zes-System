# Agent Orchestration

## Hermes AI Agent

Hermes is the primary AI agent framework running on this system.

**Config:** `~/.hermes/config.yaml`
**Gateway:** Port 8787
**Model Provider:** Custom (routes through 9router at `http://127.0.0.1:20128/v1`)
**Default Model:** `cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast`

### Cron Jobs

Two scheduled jobs are active:

1. **daily-health-check** — System health check every 6 hours
2. **log-cleanup** — Log rotation cleanup every 24 hours

```bash
hermes cron list                    # List all cron jobs
hermes cron add <name> <schedule>   # Add a cron job
hermes cron remove <id>             # Remove a cron job
```

### Skills

Hermes skills are located at `~/hermes-agent-full/skills/`. The Google Workspace skill at `skills/productivity/google-workspace/` provides OAuth-based Gmail, Calendar, and Drive access.

## Claude Code AI Coding Agent

Claude Code 2.0 runs inside the proot container on port 9876.

**Claude Code:** CLI agent via 9Router proxy · `claude -p "task"`
**Model:** `9router/cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast`
**Provider:** 9Router (OpenAI-compatible)

The config routes all requests through 9router for provider rotation and token management.


## Codex NL Orchestrator

Codex is the **natural language orchestrator** for ZES, routing tasks to the best backend.

### Architecture

```
Codex ──┬── proot-distro → Claude Code (deep coding, file ops, MCP tools)
        ├── hermes CLI → Hermes Gateway (cron jobs, messaging)
        ├── sv → runsv services (system start/stop/restart)
        ├── curl → 9Router API (18 AI providers, model switching)
        └── curl → Dashboard API (:8083, health monitoring)
```

### Delegation Patterns

| Task Type | Backend | Method |
|-----------|---------|--------|
| Coding, debugging, file ops | Claude Code (proot) | `claude -p "task" --bare` |
| Scheduled tasks | Hermes cron | `hermes cron create "schedule" "prompt"` |
| System health | Dashboard API | `curl localhost:8083/api/status` |
| Model switching | 9Router API | `9router-switch-model.sh switch <model>` |
| Service management | runsv | `sv restart <service>` |

### Agent Config Files

| Agent | File | Purpose |
|-------|------|---------|
| **Codex** | `~/.codex/AGENTS.md` | Orchestrator knowledge + connection map |
| **Claude Code** | `proot ~/.claude/CLAUDE.md` | Takes orders from Codex, uses MCP tools |
| **Hermes** | `~/.hermes/SOUL.md` (Termux + proot) | Accepts scheduling from Codex |

### Orchestrator Skill

Path: `~/.codex/skills/zes-orchestrator/`

- `SKILL.md` — 6 delegation patterns + 3 new features (357 lines)
- `scripts/` — 6 executable scripts
- `sub-skills/9router-model-switch/SKILL.md` — Model selection reference
- `references/architecture.md` — Full system topology

### Dashboard Integration

The dashboard at `:8083` has a **Cron tab** showing all 6 Hermes cron jobs with status, schedule, and recent results. Auto-refreshes every 30s.


## CMDOP Fleet Orchestration

CMDOP provides multi-machine orchestration. The agent is enrolled at `zes.cmdop.dev`.

**Status:**
```bash
proot-distro login debian -- cmdop agent status
```

**Commands:**
```bash
proot-distro login debian -- cmdop doctor    # Check agent health
proot-distro login debian -- cmdop machines  # List fleet machines
```

**Config (inside proot):** `/root/.config/cmdop/config.yaml`

## OpenClaw SDK

OpenClaw is an open-source agent orchestration plugin (thin wrapper around CMDOP Python SDK).

**Version:** 2026.3.20
**Import:** `from openclaw import OpenClaw`

## 9Router as AI Gateway

All agents route through 9router which provides:
- Provider rotation
- Token management
- Tor proxy for privacy
- Unified API endpoint at `http://127.0.0.1:20128/v1`
