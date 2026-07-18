---
category: Orchestration

name: ZES-integration
description: Cross-agent orchestration — wire Codex, Hermes, OpenClaude, and ZES Memory Hub into unified workflows. Use when building integrations between ZES components.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Integration

Orchestrates cross-agent workflows across the ZES ecosystem.

## Architecture

```
Codex CLI → ZES Memory Hub → Hermes Agent
                      ↓
              OpenClaude memdir
              Hermes MEMORY.md
              Codex raw_memories.md
```

## Key Integration Points

### Memory Flow
- Hermes self-improvement loop writes to ZESMemoryProvider
- ZESMemoryProvider broadcasts to all 3 stores
- CodexSync imports Codex stage1_outputs every 5 min

### Agent Communication
- 9Router (:20128) — unified LLM gateway for all agents
- Kanban (:9119/kanban) — shared task board
- Dashboard (:5173) — unified control panel

### Config Files
- `~/.hermes/config.yaml` — Hermes config (memory.provider: zes_memory)
- `~/.codex/config.toml` — Codex config (model_providers.9router)
- `~/9router/data/` — 9Router provider configs

## Integration Skill References
- `ZES-memory-ops` for memory operations
- `ZES-provider-manager` for LLM provider setup
- `ZES-service-orchestrator` for service lifecycle
