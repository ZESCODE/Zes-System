---
category: Orchestration

name: ZES-service-orchestrator
description: Manage all ZES services — start, stop, monitor, and route between 9Router, Hermes, OpenClaude, Dashboard, and Codex CLI. Unified service lifecycle for the ZES ecosystem.
metadata:
  origin: ZES
  version: 1.0.0
  services:
    - ninerouter (:20128)
    - hermes (:9119)
    - openclaude
    - dashboard (:5173)
    - old-zes-core (:8082)
---


# ZES Service Orchestrator

Manages the full **ZES ecosystem**: 9Router AI Gateway, Hermes Agent, OpenClaude, System Dashboard, Old ZES Core dev reference. Every service, one skill.

## Service Registry

| Service | Port | Purpose | Start Command |
|---------|------|---------|--------------|
| **9Router** | :20128 | AI model gateway | `cd ~/9router && node server.js &` |
| **Hermes** | :9119 | Agent dashboard + chat | `cd ~/Documents/Codex/2026-07-12/system-status/hermes-agent && python3 run_agent.py &` |
| **Dashboard** | :5173 | ZES main dashboard | `cd ~/Documents/Codex/2026-07-12/system-status && bash start-dashboard.sh` |
| **Old ZES Core** | :8082 | Dev reference / legacy | `cd ~/zes-core/site && python3 server.py &` |
| **OpenClaude** | — | Terminal chat UI | `cd ~/openclaude && bun run start` |

## Quick Status

```bash
# Check all services
for p in 20128 9119 5173 8082; do
  curl -s -o /dev/null -w ":%p → %{http_code}" http://localhost:$p && echo "" || echo ":$p → DOWN"
done
```

## Service Lifecycle

```bash
# Start all
cd ~/Documents/Codex/2026-07-12/system-status && bash start-dashboard.sh

# Stop specific
kill $(lsof -ti :5173) 2>/dev/null
kill $(lsof -ti :9119) 2>/dev/null
```

## Design Doc

`docs/superpowers/specs/2026-07-14-zes-memory-hub-design.md`
`docs/superpowers/plans/2026-07-14-zes-memory-hub-implementation.md`
