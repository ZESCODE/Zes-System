---
name: ZES-ui-language
description: Unified Dashboard Widget — Status CLI (zes status) + Web Widget (zes widget) showing all 11 tools, providers, services, and system resources at a glance.
---

# ZES Unified Dashboard Widget

Two interfaces — CLI and Web — both showing the same unified view of the entire ZES ecosystem.

## Components

### 1. CLI Dashboard (`zes status`)

```
╔══════════════════════════════════════════════════════════╗
║  🏛️  ZES UNIFIED STATUS DASHBOARD                        ║
╚══════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────┐
│ 🛠️  ZES CLI TOOLS (11 commands)                          │
└──────────────────────────────────────────────────────────┘
  🟢 research       r      3-7      —      —   Multi-agent research
  🟢 batch          b      RR       —      —   Batch processing
  🟢 consolidate    c      3        —      —   Memory consolidation
  🟢 debug          d      3+s      —      —   Systematic debugging
  🟢 quality        q      3+s      —      —   Code quality gate
  🟢 verify         v      3+s      —      —   Pre-completion verification
  🟢 brainstorm     bs     3+s      —      —   Brainstorming
  🟢 design         dr     3+s      —      —   Design review
  🟢 integrate      it     3+s      —      —   Integration verification
  🟢 cost           ct     3+s      —      —   Cost tracking
  🟢 bench          bm     3+s      2      01:18  Benchmarking

┌──────────────────────────────────────────────────────────┐
│ 🔌 LLM PROVIDERS (7 configured)                          │
└──────────────────────────────────────────────────────────┘
  🟢 Groq               gsk_6ptd...
  🟢 OpenRouter         sk-or-v1...
  🟢 LLM7               rRO7XGRZ...
  🟢 OpenCode Zen       sk-sjkki...
  ⚪ GitHub Models      No key
  🟢 Mistral            MyV9lhlJ...
  🟢 NVIDIA             nvapi-Xb...

┌──────────────────────────────────────────────────────────┐
│ 🌐 SERVICES & DAEMONS (6 checked)                        │
└──────────────────────────────────────────────────────────┘
  🟢 :4356  BitRouter          106ms
  🟢 :20129 AI-Proxy           11ms
  🟢 :5050  ZES Dashboard      66ms
  🟢 :9119  Hermes Dashboard   40ms
  🔴 :8822  amux               HTTP Error 404
  🔴 :9050  Tor                HTTP Error 501

┌──────────────────────────────────────────────────────────┐
│ 🖥️  SYSTEM RESOURCES                                    │
└──────────────────────────────────────────────────────────┘
  🧠 Memory: 62% used     [██████████████████░░░░░░░░░░░░]
  💾 Disk:  79% used      [███████████████████████░░░░░░░]
  ⏱  Load:  0.00/0.00/0.00
  🧩 Memory Hub: 1.1 MB

════════════════════════════════════════════════════════════
  📊 Health: 🟢 HEALTHY  |  Tools: 11/11  |  Providers: 6/7  |  Services: 4/6
════════════════════════════════════════════════════════════
```

### 2. Web Widget (`zes widget`)

A standalone HTTP server on port 8299 serving:
- **`/`** — Dark theme HTML dashboard widget with real-time bars and auto-refresh
- **`/api/status`** — JSON API for custom integrations

```
🏛️  ZES Status Widget: http://127.0.0.1:8299
📡  JSON API:          http://127.0.0.1:8299/api/status
```

Features:
- Auto-refresh every 30s
- Color-coded health indicators (green/yellow/red)
- Memory and disk usage bars
- All 11 tools listed with install status and run counts
- All services with port and latency
- All providers with key status

## Usage

### CLI
```
zes status                  # Full unified dashboard
zes status --simple         # One-line compact: "ZES: 5 runs | 11 tools | 6/7 providers..."
zes status --json           # JSON for scripts/web
zes status --watch          # Live refresh every 5s (Ctrl+C to stop)
```

### Web
```
zes widget                  # Run on default port :8299
zes widget --port 8888       # Custom port
zes widget --no-open         # Silent mode (just serve)
```

## Data Sources

| Section | Source | Method |
|---------|--------|--------|
| CLI Tools | `~/.local/bin/zes-*` | File existence check |
| Tool Usage | `~/.zes/usage.log` | Auto-logged by `zes` CLI |
| Providers | `$PROVIDER_API_KEY` env vars | Key existence check |
| Services | http://127.0.0.1:{port} | HTTP GET with 3s timeout |
| System | `/proc/loadavg`, `/proc/meminfo`, `df -h` | Direct file reads |
| Memory Hub | `~/.zes/memory_hub.sqlite` | File stat |

## Integration

### Run on system startup
```bash
runsv-add zes-widget
```

### Embed in existing ZES Dashboard
Add an iframe to your SPA:
```html
<iframe src="http://127.0.0.1:8299" width="100%" height="800" style="border:none"></iframe>
```

### Consume JSON API from other tools
```python
import requests
data = requests.get("http://127.0.0.1:8299/api/status").json()
print(data["health"])  # "healthy" | "degraded" | "critical"
```

## Pair With

- `ZES-parallel-research` — Deep-dive investigation of any RED status found here
- `ZES-systematic-debugging` — Debug services showing as DOWN
- `ZES-benchmark` — Performance benchmark correlated with health data
- `ZES-cost-tracker` — Cost vs. health tradeoff analysis
