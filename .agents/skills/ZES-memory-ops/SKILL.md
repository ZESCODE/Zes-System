---
category: Memory

name: ZES-memory-ops
description: Unified memory hub operations — search, write, sync, and repair memories across Codex, Hermes, and OpenClaude stores via ZESMemoryProvider.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Memory Operations

Manages the unified ZES memory hub powered by ZESMemoryProvider.

## Architecture
- ZES SQLite store (`~/.zes/memory_hub.sqlite`) with FTS5 search
- OpenClaude memdir (`~/openclaude/memdir/`) typed .md files
- Hermes native (`~/.hermes/MEMORY.md`, `USER.md`)
- Codex raw memories (`~/.codex/memories/raw_memories.md`)

## Memory Types
| Type | Example |
|------|---------|
| `preference` | "Prefers dark mode" |
| `decision` | "Use PostgreSQL for ACID" |
| `pattern` | "If EADDRINUSE, kill port 3000" |
| `fact` | "Stripe webhook in .env" |
| `feedback` | "User hated verbose logs" |

## Priority & Conflict Resolution
- `high` > `medium` > `low`
- Same priority → newest timestamp wins
- Source trust: HermesNative > ZES SQLite > OpenClaude

## Key Files
- `hermes-agent/plugins/memory/zes_memory/provider.py`
- `hermes-agent/plugins/memory/zes_memory/store.py`
- `hermes-agent/plugins/memory/zes_memory/codex_sync.py`
- `hermes-agent/plugins/memory/zes_memory/oc_adapter.py`

## CLI
```bash
cd hermes-agent && PYTHONPATH=. python3 -c "
from plugins.memory.zes_memory.provider import ZESMemoryProvider
p = ZESMemoryProvider(); p.initialize(); print(p.get_stats()); p.shutdown()
"
```
