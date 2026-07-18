---
category: Providers

name: ZES-9router
description: 9Router AI Gateway management — model routing, API key management, provider configuration, and load balancing across LLM providers.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES 9Router

Manages the 9Router AI Gateway — the unified LLM routing layer for all ZES agents.

## Service
- **Port:** [http://localhost:20128](http://localhost:20128)
- **Type:** AI model gateway
- **Config:** `~/9router/.env`, `~/9router/data/`

## Admin Dashboard
[http://localhost:20128](http://localhost:20128) — model management, API keys, usage stats

## OpenAI-Compatible API
```
http://localhost:20128/v1/chat/completions
http://localhost:20128/v1/models
```

## Provider Routes
| Route | Backend |
|-------|---------|
| `groq/*` | Groq API (free tier) |
| `nvidia/*` | NVIDIA NIM (free) |
| `@cf/*` | Cloudflare Workers AI |
| `gemini/*` | Google Gemini |
| `openai/*` | OpenAI via Cloudflare proxy |
| `alibaba/*` | Alibaba MaaS |

## Start/Stop
```bash
cd ~/9router && node server.js  # Start
kill $(lsof -ti :20128)         # Stop
```
