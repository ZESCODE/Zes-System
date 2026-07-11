# 9Router Provider Plugin

## Overview

The 9Router Provider Plugin formalizes how AI models are accessed through 9Router
at `http://localhost:20128/v1`. Modeled on OpenClaw's plugin-sdk provider pattern,
it provides a consistent interface for chat, streaming, embeddings, and model discovery.

## Architecture

```
Plugin pattern (OpenClaw-style)
├── NineRouterProvider class
│   ├── modelCatalog — static model definitions
│   ├── chat() — OpenAI-compatible chat completions
│   ├── streaming — async generator for SSE responses
│   ├── embed() — text embeddings
│   ├── listModels() — dynamic + fallback catalog
│   └── testConnection() — health check
│
├── Auth methods
│   ├── "none" (default for local 9Router)
│   ├── "api-key" (Bearer token)
│   └── "cli" (9Router CLI token from machine-id)
│
└── Usage in background.js
    └── const AI = new NineRouterProvider({ defaultModel: 'groq/llama-3.3-70b-versatile' })
```

## Model Catalog

The provider includes a built-in catalog with these models:

| ID | Provider | Context | Notes |
|----|----------|---------|-------|
| `groq/llama-3.3-70b-versatile` | Groq | 32K | Default, fast |
| `gh/gpt-5.4-mini-free-auto` | GitHub | 262K | Free tier |
| `deepseek/deepseek-v4-flash-free` | DeepSeek | 262K | Free, large ctx |
| `anthropic/claude-sonnet-4-6` | Anthropic | 200K | Premium |
| `google/gemini-3.1-flash-lite` | Gemini | 131K | Google |
| `nvidia/nemotron-4-340b` | NVIDIA | 16K | |

Models are auto-discovered from 9Router's `/v1/models` endpoint on first use,
with the static catalog as fallback.

## Usage

```javascript
import { NineRouterProvider } from './zes-chrome/mcp-server/9router-provider.js';

// Default (no auth, local 9Router)
const ai = new NineRouterProvider();

// With API key
const ai = new NineRouterProvider({
  auth: { type: 'api-key', key: 'sk-...' }
});

// Chat
const reply = await ai.chat([
  { role: 'user', content: 'Hello!' }
], { model: 'groq/llama-3.3-70b-versatile' });

// Stream
for await (const chunk of ai.chat(messages, { stream: true })) {
  process.stdout.write(chunk);
}

// List available models
const models = await ai.listModels();
```

## Adding Models

To add a model to the catalog, edit `modelCatalog` in `9router-provider.js`:

```javascript
'mistral/mistral-large': {
  api: 'openai-completions',
  contextTokens: 32768,
  description: 'Mistral Large',
  provider: 'mistral',
},
```

## Migration from Ad-hoc Code

Previously, `background.js` had ad-hoc fetch calls to 9Router. The provider pattern
encapsulates all 9Router interaction in one place with:
- Consistent error handling
- Streaming support
- Auth abstraction
- Model catalog with descriptions
- Connection testing
