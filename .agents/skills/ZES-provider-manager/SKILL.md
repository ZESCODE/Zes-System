---
category: Providers

name: ZES-provider-manager
description: LLM provider discovery and configuration — manage API keys, routing, and fallbacks across Groq, OpenAI, Anthropic, Gemini, Alibaba, Cloudflare Workers AI, and free models.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Provider Manager

Manages all LLM providers for the ZES system via 9Router gateway.

## Config: `~/.hermes/config.yaml`
```yaml
model:
  default: gpt-4o-mini
  provider: custom
  base_url: http://localhost:20128/v1
```

## Active Providers
| Provider | Status | Source |
|----------|--------|--------|
| 9Router (proxy) | ✅ | `~/.hermes/config.yaml` |
| Groq | ✅ | freellm.net discovery |
| Gemini | ✅ | Free tier |
| Alibaba | ✅ | MaaS endpoint |
| OpenAI | ⚠️ | Via Cloudflare proxy |
| Anthropic | ⚠️ | Via 9Router |

## Free Models via freellm.net
```bash
curl -s https://freellm.net/api/models | head -50
```

## 9Router Admin Dashboard
- [http://localhost:20128](http://localhost:20128) — model management, API keys
