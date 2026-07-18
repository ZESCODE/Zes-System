---
category: Integrations

name: 9router-integration
description: Use when working with 9Router AI gateway — LLM chat/code generation, vector embeddings, web search, URL fetching. Combines chat, embeddings, search, and web fetch into one unified skill. Requires NINEROUTER_URL and optionally NINEROUTER_KEY.
---


# 9Router — Unified Integration

Local/remote AI gateway exposing OpenAI-compatible REST. One key, many providers, auto-fallback.

## Setup

```bash
export NINEROUTER_URL="http://localhost:20128"      # or VPS / tunnel URL
export NINEROUTER_KEY="sk-..."                      # Dashboard → Keys (omit if auth disabled)
```

Verify: `curl $NINEROUTER_URL/api/health` → `{"ok":true}`

## Model Discovery

```bash
# All models by capability
curl $NINEROUTER_URL/v1/models                    # chat/LLM
curl $NINEROUTER_URL/v1/models/embedding           # embeddings
curl $NINEROUTER_URL/v1/models/web                 # web search + fetch (check `kind` field)
curl $NINEROUTER_URL/v1/models/image               # image-gen
curl $NINEROUTER_URL/v1/models/tts                 # text-to-speech
curl $NINEROUTER_URL/v1/models/stt                 # speech-to-text
curl $NINEROUTER_URL/v1/models/image-to-text       # vision

# Per-model metadata (contextWindow, params, dimensions)
curl "$NINEROUTER_URL/v1/models/info?id=openai/gpt-4o"
```

Combos (e.g. `vip`, `mycodex`, `search-combo`, `fetch-combo`) auto-fallback through multiple providers.

Response shape:
```json
{ "object": "list", "data": [
  { "id": "openai/gpt-5", "object": "model", "owned_by": "openai", "created": 1735000000 }
]}
```

---

## 1. Chat / Code Generation

### Endpoints
- `POST $NINEROUTER_URL/v1/chat/completions` — OpenAI format
- `POST $NINEROUTER_URL/v1/messages` — Anthropic format

### OpenAI format (curl)
```bash
curl -X POST $NINEROUTER_URL/v1/chat/completions \
  -H "Authorization: Bearer $NINEROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-5","messages":[{"role":"user","content":"Hi"}],"stream":false}'
```

### OpenAI format (JS/OpenAI SDK)
```js
import OpenAI from "openai";
const client = new OpenAI({
  baseURL: `${process.env.NINEROUTER_URL}/v1`,
  apiKey: process.env.NINEROUTER_KEY
});
const res = await client.chat.completions.create({
  model: "openai/gpt-5",
  messages: [{ role: "user", content: "Hi" }],
  stream: true,
});
for await (const chunk of res) {
  process.stdout.write(chunk.choices[0]?.delta?.content || "");
}
```

### Anthropic format
```bash
curl -X POST $NINEROUTER_URL/v1/messages \
  -H "Authorization: Bearer $NINEROUTER_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"cc/claude-opus-4-7","max_tokens":1024,"messages":[{"role":"user","content":"Hi"}]}'
```

### Response shapes

OpenAI:
```json
{ "id": "chatcmpl-...", "object": "chat.completion", "model": "openai/gpt-5",
  "choices": [{ "index": 0, "message": { "role": "assistant", "content": "Hello!" }, "finish_reason": "stop" }],
  "usage": { "prompt_tokens": 8, "completion_tokens": 2, "total_tokens": 10 } }
```

Streaming (`stream:true`) emits SSE: `data: {choices:[{delta:{content:"..."}}]}\n\n` ... `data: [DONE]\n\n`.

Anthropic:
```json
{ "id": "msg_...", "type": "message", "role": "assistant", "model": "cc/claude-opus-4-7",
  "content": [{ "type": "text", "text": "Hello!" }],
  "stop_reason": "end_turn", "usage": { "input_tokens": 8, "output_tokens": 2 } }
```

---

## 2. Vector Embeddings

### Endpoint
`POST $NINEROUTER_URL/v1/embeddings`

| Field | Required | Notes |
|---|---|---|
| `model` | yes | from `/v1/models/embedding` |
| `input` | yes | string OR array of strings |
| `encoding_format` | no | `float` (default) / `base64` |
| `dimensions` | no | OpenAI v3 only |

### Examples
```bash
curl -X POST $NINEROUTER_URL/v1/embeddings \
  -H "Authorization: Bearer $NINEROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/text-embedding-3-small","input":["hello","world"]}'
```

```js
const r = await fetch(`${process.env.NINEROUTER_URL}/v1/embeddings`, {
  method: "POST",
  headers: { "Authorization": `Bearer ${process.env.NINEROUTER_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify({ model: "gemini/text-embedding-004", input: "RAG chunk text" }),
});
const { data } = await r.json();
console.log(data[0].embedding.length);  // dimension
```

### Response shape
```json
{ "object": "list", "model": "openai/text-embedding-3-small",
  "data": [
    { "object": "embedding", "index": 0, "embedding": [0.0123, -0.045, ...] },
    { "object": "embedding", "index": 1, "embedding": [...] }
  ],
  "usage": { "prompt_tokens": 5, "total_tokens": 5 } }
```

### Provider notes
| Provider | Notes |
|---|---|
| OpenAI, OpenRouter, Mistral, Voyage, etc. | Native OpenAI shape — `dimensions` works only on OpenAI v3 |
| Gemini / Google AI Studio | Server auto-converts to `embedContent`/`batchEmbedContents` — send OpenAI shape |
| Custom endpoints | Custom `baseUrl` from credentials |

Batch (`input` as array) is faster; some providers consolidate single vectors into parallel calls.

---

## 3. Web Search

### Endpoint
`POST $NINEROUTER_URL/v1/search`

| Field | Required | Notes |
|---|---|---|
| `model` (or `provider`) | yes | from `/v1/models/web` (e.g. `tavily`, `exa`, `brave-search`) |
| `query` | yes | Search query string |
| `max_results` | no | Max results (default varies by provider) |
| Provider-specific extras | no | See quirks below |

### Examples
```bash
curl -X POST $NINEROUTER_URL/v1/search \
  -H "Authorization: Bearer $NINEROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"tavily","query":"9Router open source","max_results":5}'
```

```js
const r = await fetch(`${process.env.NINEROUTER_URL}/v1/search`, {
  method: "POST",
  headers: { "Authorization": `Bearer ${process.env.NINEROUTER_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify({ model: "search-combo", query: "latest LLM benchmarks", max_results: 10 }),
});
console.log(await r.json());
```

### Response shape
```json
{
  "provider": "tavily",
  "results": [
    { "title": "...", "url": "...", "snippet": "...", "score": 0.92,
      "citation": { "provider": "tavily", "retrieved_at": "2026-...", "rank": 1 }
    }
  ],
  "usage": { "queries_used": 1, "search_cost_usd": 0.008 }
}
```

### Provider quirks
| Provider | Supports | Required extras |
|---|---|---|
| `tavily` | country, domain_filter, news topic | — |
| `exa` | domain_filter, news category | — |
| `brave-search` | country, language | — |
| `serper` | country, language, news | — |
| `perplexity` | country, language, domain_filter | — |
| `linkup` | domain_filter, time_range | `depth: fast/standard/deep` |
| `google-pse` | country, language, time_range, offset | **`cx` required** (providerOptions) |
| `searchapi` | country, language, pagination | — |
| `youcom` | country, language, time_range | — |
| `searxng` | language, time_range | Self-hosted, **noAuth** |

Provider IS the model — `"provider":"tavily"` ≡ `"model":"tavily"`.

---

## 4. Web Fetch (URL → Markdown)

### Endpoint
`POST $NINEROUTER_URL/v1/web/fetch`

| Field | Required | Notes |
|---|---|---|
| `model` (or `provider`) | yes | from `/v1/models/web` (e.g. `firecrawl`, `jina-reader`) |
| `url` | yes | URL to extract |
| `format` | no | `markdown` (default) / `text` / `html` |
| `max_characters` | no | truncate output |

### Examples
```bash
# Jina Reader (free tier, fastest markdown)
curl -X POST $NINEROUTER_URL/v1/web/fetch \
  -H "Authorization: Bearer $NINEROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"jina-reader","url":"https://9router.com","format":"markdown"}'

# Firecrawl (JS-rendered pages)
curl -X POST $NINEROUTER_URL/v1/web/fetch \
  -H "Authorization: Bearer $NINEROUTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"firecrawl","url":"https://example.com","format":"markdown","max_characters":0}'
```

```js
const r = await fetch(`${process.env.NINEROUTER_URL}/v1/web/fetch`, {
  method: "POST",
  headers: { "Authorization": `Bearer ${process.env.NINEROUTER_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify({ model: "fetch-combo", url: "https://example.com", format: "markdown", max_characters: 5000 }),
});
const { data } = await r.json();
console.log(data.title, data.content.length);
```

### Response shape
```json
{
  "provider": "jina-reader",
  "url": "...",
  "title": "...",
  "content": { "format": "markdown", "text": "...", "length": 1234 },
  "usage": { "fetch_cost_usd": 0 },
  "metrics": { "response_time_ms": 850, "upstream_latency_ms": 700 }
}
```

### Provider quirks
| Provider | Auth | Best for |
|---|---|---|
| `firecrawl` | Bearer | JS-rendered pages, `format=markdown/html` |
| `jina-reader` | Bearer (optional) | Free tier (~1M chars/mo); fastest plain markdown |
| `tavily` | Bearer | Bulk extract; returns `raw_content` |
| `exa` | `x-api-key` | Pre-indexed pages; fast text extraction |

---

## Error Handling

| HTTP | Meaning | Action |
|------|---------|--------|
| 401 | Auth required | Set/refresh `NINEROUTER_KEY` (Dashboard → Keys) |
| 400 | Invalid model format | Check `model` exists in `/v1/models/<kind>` |
| 503 | All accounts unavailable | Wait `retry-after` header or add another provider account |

## Quick Reference

| Capability | Endpoint | Model Discovery |
|---|---|---|
| Chat | `POST /v1/chat/completions` | `GET /v1/models` |
| Anthropic Chat | `POST /v1/messages` | `GET /v1/models` |
| Embeddings | `POST /v1/embeddings` | `GET /v1/models/embedding` |
| Web Search | `POST /v1/search` | `GET /v1/models/web` (kind=webSearch) |
| Web Fetch | `POST /v1/web/fetch` | `GET /v1/models/web` (kind=webFetch) |
