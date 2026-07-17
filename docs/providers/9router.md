# 9Router Provider Guide

## Overview

9Router v0.5.20 manages 23 AI provider connections across 13+ providers.
All providers are stored in `~/.9router/db/data.sqlite`.

## Authentication

### CLI Token
```bash
TOKEN=$(python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])")
curl -H "x-9r-cli-token: $TOKEN" http://localhost:20128/api/providers
```

### API Proxy (for model requests)
Use `x-api-key` header with any of the registered API keys.

## Provider Status

| Provider | Status | Auth | Notes |
|----------|--------|------|-------|
| **GitHub Copilot** | ✅ active | OAuth | Free plan: GPT-4o, GPT-4.1, GPT-5.4-mini-free-auto |
| **Kiro** | ✅ active | OAuth | 34 models: claude-sonnet-4.5, claude-haiku-4.5, gemini-2.5-flash |
| **OpenRouter** | ✅ active | API key | Free models: qwen/qwen3-coder:free, gemma-4 |
| **Gemini** | ✅ active | API key | Gemini 2.5 Flash/Pro |
| **Gemini CLI** | ✅ active | OAuth | Gemini CLI integration |
| **KiloCode** | ✅ active | OAuth | Code-focused models |
| **Nvidia Nim** | ✅ active | API key | Some 502 timeout issues |
| **Anthropic** | ❌ unavailable | API key | Credit balance too low |
| **Cline** | ❌ unavailable | OAuth | Expired, needs re-auth |
| **Codex** | ❌ unavailable | OAuth | ChatGPT plan limitation |
| **Cerebras** | ❌ unavailable | API key | Model access issue |
| **Mistral AI** | ❌ unavailable | API key | Invalid model |
| **Deepseek** | ❌ unavailable | API key | Insufficient balance |
| **Groq** | ❌ unavailable | API key | Model not found |
| **Cloudflare AI** | ❌ unavailable | API key | Model access issue |
| **Antigravity** | ❌ unavailable | OAuth | API error |
| **Qoder** | ❌ unavailable | OAuth | Model config pending |
| **Ollama** | ❌ unavailable | API key | Subscription required |
| **LLM7** | ⏳ policy review | API key | Free 1M tokens/day, OpenAI-compatible |

## Provider Prefixes (Custom OpenAI-Compatible)

| Prefix | Provider | Base URL | Status |
|--------|----------|----------|--------|
| `llm7` | LLM7 | `https://api.llm7.io/v1` | Policy review (~14h) |
| `gm` | Gemini 2.5 Flash | `generativelanguage.googleapis.com/v1beta/openai` | API key |
| `nv` | Nvidia Nim | `integrate.api.nvidia.com/v1` | Active (502 timeout) |
| `he` | Hermes AI | `127.0.0.1:8787` | Local (offline) |
| `oc` | OpenClaw Proxy | `127.0.0.1:4040/v1` | Local (offline) |

### Model Naming Convention
Custom providers use `prefix/model-name` format. Built-in providers use `provider/model`:
```bash
# Custom providers
llm7/gpt-5.4-mini        # LLM7
nv/nvidia/llama-3.1-nemotron-51b-instruct  # Nvidia
gm/gemini-2.5-flash      # Gemini

# Built-in providers
gh/gpt-4o                # GitHub Copilot
kr/claude-sonnet-4.5     # Kiro (recommended for Claude Code)
openrouter/qwen/qwen3-coder:free  # OpenRouter free
groq/llama-3.3-70b-versatile      # Groq
```

## Recommended Active Models

| Model ID | Provider | Use Case |
|----------|----------|----------|
| `kr/claude-sonnet-4.5` | Kiro | Primary Claude Code model, free |
| `gh/gpt-4o` | GitHub Copilot | General chat, coding |
| `gh/gpt-4.1` | GitHub Copilot | Coding tasks |
| `gh/gpt-5.4-mini-free-auto` | GitHub Copilot | Cost-effective |
| `openrouter/qwen/qwen3-coder:free` | OpenRouter | Free coding |
| `gm/gemini-2.5-flash` | Gemini | Fast/reasoning |
| `llm7/*` | LLM7 | When approved: 1M free tokens/day |

## Database Schema

### providerConnections
| Column | Description |
|--------|-------------|
| `id` | UUID |
| `provider` | Provider type or node reference |
| `authType` | `apikey`, `oauth` |
| `data` | JSON blob: apiKey, providerSpecificData, modelLocks, errors |

## Adding a Provider

```bash
# 1. Insert into providerNodes table (via SQLite)
python3 -c "
import sqlite3, json, uuid
conn = sqlite3.connect('~/.9router/db/data.sqlite')
cur = conn.cursor()
cur.execute('INSERT OR IGNORE INTO providerNodes (id, type, name, data, createdAt, updatedAt) VALUES (?,?,?,?,?,?)',
  ('openai-compatible-chat-' + str(uuid.uuid4()), 'openai-compatible', 'My Provider',
   json.dumps({'prefix':'mp','apiType':'chat','baseUrl':'https://api.example.com/v1'}),
   '2026-01-01T00:00:00Z','2026-01-01T00:00:00Z'))
conn.commit()

# 2. Add connection with API key
cur.execute('INSERT INTO providerConnections (id, provider, authType, name, data, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)',
  (str(uuid.uuid4()), node_id, 'apikey', 'My Provider',
   json.dumps({'apiKey':'sk-...','providerSpecificData':{'prefix':'mp','apiType':'chat','baseUrl':'https://api.example.com/v1','nodeName':'My Provider'}}),
   '2026-01-01T00:00:00Z','2026-01-01T00:00:00Z'))
conn.commit()
conn.close()
"
