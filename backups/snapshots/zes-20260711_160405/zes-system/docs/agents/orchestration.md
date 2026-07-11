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

## OpenCode AI Coding Agent

OpenCode 2.0 runs inside the proot container on port 9876.

**Config:** `~/.config/opencode/opencode.json`
**Model:** `9router/cf/@cf/meta/llama-3.3-70b-instruct-fp8-fast`
**Provider:** 9Router (OpenAI-compatible)

The config routes all requests through 9router for provider rotation and token management.

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
