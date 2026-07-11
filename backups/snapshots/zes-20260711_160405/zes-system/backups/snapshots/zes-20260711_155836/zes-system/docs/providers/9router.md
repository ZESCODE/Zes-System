# 9Router Provider Configuration

## Connected Providers (18)

### OAuth (browser-based auth)
- **GitHub Copilot** — `arfaXdev`, free Copilot tier, supports coding models
- **Cline** — `arfaxtrade@gmail.com`, WorkOS auth
- **Codex (OpenAI)** — `arfaxtrade@gmail.com`, free tier ChatGPT
- **Gemini CLI** — Google Cloud OAuth
- **Qoder** — Device-based auth, 30-day session expiry
- **Kiro** — AWS Builder ID (Cognito), needs re-auth

### API Key
- **NVIDIA NIM** — 100+ models, 40 RPM, no daily limit
- **Groq** — LPU hardware, fastest inference, 30 RPM
- **Gemini** — Google AI Studio key
- **DeepSeek** — Competitive open models
- **Cerebras** — High-throughput inference
- **OpenRouter** — 35+ free models, unified endpoint
- **Anthropic** — Claude models
- **Cloudflare AI** — Workers AI models
- **Mistral AI** — French-hosted, 256K context, no credit card (new)

### OpenAI-Compatible Nodes
Three custom endpoints routed through 9Router:
| Prefix | Service | Endpoint | Route |
|--------|---------|----------|-------|
| `oz` | Zen OpenCode | :5900/codex-api/zen-proxy/v1 | Direct |
| `he` | Hermes AI | :8787 | Tor |
| `oc` | OpenClaw Proxy | :4040/v1 | Tor |

## Model Prefix Reference
/github, /groq, /gemini, /deepseek, /cerebras, /openrouter,
/anthropic, /mistral, /nvidia, /oc, /he, /oz, /kr, /ds, /gh, /gc

## CLI Token
```bash
python3 -c "import hashlib;d=open('$HOME/.9router/machine-id').read().strip();s=open('$HOME/.9router/auth/cli-secret').read().strip();print(hashlib.sha256((d+'9r-cli-auth'+s).encode()).hexdigest()[:16])"
```
