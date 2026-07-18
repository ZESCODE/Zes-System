---
category: DevOps

name: system-orchestrator
description: Unified system orchestrator for managing all Termux services — ZES Core, 9Router AI Gateway, Hermes Agent, OpenClaw, React Dashboard, OpenCode Zen, and Codex CLI. Start, stop, monitor, and route between all services from one place.
metadata:
  origin: ECC
  version: 1.0.0
  services:
    - zes-core
    - ninerouter
    - hermes
    - openclaw
    - dashboard
    - opencode-zen
    - codex-cli
---


# System Orchestrator — Unified Service Manager

Manages the full **Termux AI ecosystem**: ZES Core, 9Router, Hermes, OpenClaw, React Dashboard, OpenCode Zen, and Codex CLI. Every service, one skill.

---

## Service Registry

| Service | Port | Purpose | Type |
|---------|------|---------|------|
| **React Dashboard** | 5173 | Unified frontend (single entry point) | web |
| **Flask API** | 5002 | Dashboard backend + Design API | api |
| **ZES Core** | 8082 | AI orchestration, workflows, design studio | web |
| **9Router** | 20128 | AI model gateway (128+ models) | api |
| **Hermes Agent** | 9119 | Agent dashboard + chat | web |
| **OpenClaw** | 5000 | Sessions, tools, memory, health API | api |
| **OpenCode Zen** | 5900 | Codex Web UI proxy | web |

## Single Entry Point

```bash
# Open the unified dashboard
xdg-open http://localhost:5173
```

The dashboard provides tabs for every service:
- **Overview** — System summary (CPU, memory, services, uptime)
- **Services** — Termux runit services
- **Processes** — Running processes
- **Web Services** — All web services with online/offline status
- **ZES Health** — Live health check of all services
- **Hermes Chat** — Embedded Hermes agent chat
- **9Router** — Embedded 9Router admin dashboard
- **Design Studio** — Native theme editor with save/load/export
- **Workflow Builder** — Embedded ZES workflow builder
- **Codex Web** — Embedded Codex Web UI

---

## Service Management

### Quick Status

```bash
# All services health
curl http://localhost:5002/api/health/all

# Web services with ports
curl http://localhost:5002/api/web-services

# System summary
curl http://localhost:5002/api/summary
```

### Start / Stop Individual Services

```bash
# 9Router (Go binary managed by its own daemon)
# Check: curl http://localhost:20128/api/health

# Hermes Dashboard
setsid ~/hermes-agent/venv/bin/hermes dashboard --port 9119 --host 127.0.0.1 < /dev/null > ~/dash.log 2>&1 &

# Hermes Gateway
setsid ~/hermes-agent/venv/bin/python3 -m hermes_cli.main gateway run < /dev/null > ~/gw.log 2>&1 &

# ZES Core Site Server
cd ~/zes-core/site && setsid python3 -u server.py > ~/logs/zes.log 2>&1 &

# Flask API (Dashboard Backend)
cd ~/Documents/Codex/2026-07-12/system-status && setsid python3 -B api/server.py > ~/flask_err.log 2>&1 &

# OpenClaw Server
cd ~/openclaw/server && setsid python3 -u app.py > ~/logs/openclaw.log 2>&1 &

# OpenCode Zen (5900) — managed by Codex CLI automatically
```

### Start All Services

```bash
#!/bin/bash
# Start all core services
echo "Starting all services..."

# 1. Flask API
cd ~/Documents/Codex/2026-07-12/system-status
setsid python3 -B api/server.py > ~/flask_err.log 2>&1 &
echo "  ✅ Flask API on :5002"

# 2. ZES Core
cd ~/zes-core/site
setsid python3 -u server.py > ~/logs/zes.log 2>&1 &
echo "  ✅ ZES Core on :8082"

# 3. OpenClaw
cd ~/openclaw/server
setsid python3 -u app.py > ~/logs/openclaw.log 2>&1 &
echo "  ✅ OpenClaw on :5000"

echo "Done! Dashboard: http://localhost:5173"
```

---

## AI Model Routing via 9Router

```bash
# List available models
curl http://localhost:20128/v1/models | jq '.data[].id'

# Chat completion (OpenAI-compatible)
curl http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "groq/llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Free providers available:
# - Groq: llama-3.3-70b-versatile, llama-4-maverick, qwen3-32b
# - NVIDIA: deepseek-ai/deepseek-v4-flash
# - Cloudflare: @cf/mistralai/mistral-small-3.1-24b
# - Cerebras: llama-3.3-70b, llama-4-scout-17b
# - DeepSeek (Free): deepseek-v4-pro, deepseek-v4-flash
# - Mistral (Free): mistral-large-latest, codestral-latest
```

---

## Design Studio

The **Design Studio** tab in the dashboard (localhost:5173 → Design Studio) is a native React component with:

- **Theme Editor** — Configure colors, typography, spacing
- **Color Palette** — Live color pickers with hex/RGBA input
- **Typography** — Font family, size, weight with live preview
- **Live Preview** — Real-time theme preview card
- **Export** — Generates Tailwind config + CSS variables
- **Persistence** — Save/load designs via API

### API Endpoints

```bash
# List saved designs
curl http://localhost:5002/api/designs

# Save a design
curl -X POST http://localhost:5002/api/designs/my-theme \
  -H "Content-Type: application/json" \
  -d '{"name":"My Theme","colors":{"primary":"#008cff"}}'

# Load a design
curl http://localhost:5002/api/designs/my-theme

# Export as code
curl -X POST http://localhost:5002/api/designs/export \
  -H "Content-Type: application/json" \
  -d '{"name":"Component","colors":{"primary":"#008cff"}}'
```

---

## ZES Workflow Engine

ZES Core includes a workflow engine at `~/zes-core/workflow_engine.py` with pre-defined workflows:

```bash
# List workflows
python3 -c "from workflow_engine import WORKFLOWS; print('\\n'.join(WORKFLOWS.keys()))"

# Execute a workflow (via ZES API)
curl http://localhost:8082/api/tools/execute \
  -X POST -H "Content-Type: application/json" \
  -d '{"tool":"execute_workflow","args":{"name":"full_diagnostic"}}'
```

Built-in workflows: `deploy_site`, `system_update`, `full_diagnostic`, `memory_cleanup`, `backup_sessions`

---

## Health Endpoint Reference

```bash
# ZES Dashboard stats (aggregated)
curl http://localhost:8082/api/dashboard/stats

# OpenClaw health (port-based)
curl http://localhost:5000/api/health/all

# Flask API health (port + pid-based)
curl http://localhost:5002/api/health/all

# System summary
curl http://localhost:5002/api/summary
```

---

## Quick Reference

```bash
# ─── Dashboard ───
# Open: http://localhost:5173

# ─── Service Status ───
curl http://localhost:5002/api/web-services
curl http://localhost:5002/api/health/all

# ─── AI Chat via 9Router ───
curl http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"groq/llama-3.3-70b-versatile","messages":[{"role":"user","content":"hi"}]}'

# ─── Design Studio API ───
curl http://localhost:5002/api/designs

# ─── Logs ───
tail -f ~/logs/zes.log      # ZES Core
tail -f ~/flask_err.log     # Flask API
tail -f ~/dash.log          # Hermes Dashboard
tail -f ~/gw.log            # Hermes Gateway

# ─── Kill All ───
pkill -f "api/server.py"
pkill -f "zes-core/site/server.py"
pkill -f "openclaw/server/app.py"
```
