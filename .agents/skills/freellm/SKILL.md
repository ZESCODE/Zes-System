---
category: Uncategorized

name: freellm
description: Use when you need free AI model API keys, free LLM provider configuration, or want to discover free AI models for Codex, Claude Code, or Cursor
---


# FreeLLM — Free AI API Resources

## Overview

[FreeLLM.net](https://freellm.net) tracks **648+ free AI models** from **30+ providers** — all with free tiers, most with no credit card required. Use it to discover, compare, and configure free AI backends for Codex, Claude Code, Cursor, and any OpenAI-compatible tool.

## Key Free Providers

| Provider | Models | Context | Rate Limit | Sign Up |
|----------|--------|---------|------------|---------|
| **NVIDIA NIM** | 115 | Up to 1.0M | 40 RPM | No credit card |
| **Google Gemini** | 12 | Up to 1.0M | 15 RPM | No credit card |
| **Groq** | 20 | Varies | High | No credit card |
| **Cerebras** | 7 | Varies | High | No credit card |
| **OpenRouter** | ~35 free | Varies | 200 req/day | No credit card |
| **Mistral AI** | 9 | Varies | ~1B tokens/mo | No credit card |
| **Cloudflare Workers AI** | 39 | Varies | Free | No credit card |
| **DeepSeek** | 2 | Varies | Free | No credit card |
| **GitHub Models** | 13 | Varies | Copilot limits | Copilot subscription |

## Recommended Free Models for Codex

| Model | Provider | Endpoint | Context |
|-------|----------|----------|---------|
| `z-ai/glm-5.2` | NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | 1.0M |
| `minimaxai/minimax-m3` | NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | 1.0M |
| `gemini-3.5-flash` | Google Gemini | `https://generativelanguage.googleapis.com/v1beta` | 1.0M |
| `deepseek-ai/deepseek-v4-pro` | NVIDIA NIM | `https://integrate.api.nvidia.com/v1` | 1.0M |
| `agnes-2.0-flash` | Agnes AI | `https://apihub.agnes-ai.com/v1` | 256K |

## Getting Free API Keys

| Provider | Get Key At | Notes |
|----------|-----------|-------|
| **Groq** | https://console.groq.com/keys | Free tier, fast inference |
| **Cerebras** | https://console.cerebras.ai/ | Free tier, no credit card |
| **Mistral AI** | https://console.mistral.ai/ | ~1B tokens/month free |
| **NVIDIA NIM** | https://build.nvidia.com/ | No credit card, phone verify |
| **OpenRouter** | https://openrouter.ai/keys | ~35 free models |
| **DeepSeek** | https://platform.deepseek.ai/ | Free tier available |
| **Cloudflare AI** | https://cloudflare.com/ | Free Workers AI tier |
| **GitHub Models** | https://github.com/marketplace/models | With Copilot subscription |
| **Google Gemini** | https://aistudio.google.com/ | 15 RPM free |

## 9Router Integration

This project has 9router running at `http://localhost:20128`. The following free providers are already configured in 9router's database — just add your API key from the links above:

- **Groq (Free)** — Needs API key
- **Cerebras (Free)** — Needs API key  
- **DeepSeek (Free)** — Needs API key
- **Mistral AI (Free)** — Needs API key

**Already active:**
- OpenCode Free — No API key needed
- Kiro AI — Free Claude access (OAuth)
- NVIDIA VIM — Has API key (currently unavailable)
- OpenRouter — Has API key

### How to Add API Keys

1. Open 9Router dashboard: `http://localhost:20128`
2. Login with password
3. Go to **Providers** tab
4. Find the provider, click **Configure**
5. Paste your API key from the link above
6. Click **Test & Save**

### To Use 9Router with Codex

Configure Codex with:
```
Model Provider: OpenAI-compatible
Endpoint: http://localhost:20128/v1
API Key: Get from 9router dashboard → API Keys
Model: Choose from available providers
```

## When to Use This Skill

- **Setting up a new project** — Need free AI access for development
- **API key expired** — Find alternative free providers
- **Need specific model capability** — Search by modality (vision, code, reasoning)
- **Rate limited** — Find providers with higher free limits
- **Configure Codex/Claude Code** — Get the right endpoint URLs and model names

## When NOT to Use

- You already have paid API keys that work fine
- Working with sensitive data that can't go through external providers
- Need guaranteed uptime/SLA (free tiers have no SLA)

## Integration

Combined with **9router**, FreeLLM providers get auto-fallback and token saving. 9router routes between providers so if one fails or rate-limits, it falls back to the next.
