# ZES Memory Hub — Vector Search

**Added:** 2026-07-17  
**Version:** v3.5.0

## Overview

The ZES Memory Hub now supports **three search modes** powered by a pure Python TF-IDF vectorizer (no external dependencies):

| Mode | Description | Best For |
|------|-------------|----------|
| `fts5` | SQLite FTS5 full-text search | Exact keyword matching |
| `vector` | TF-IDF embedding + cosine similarity | Semantic similarity search |
| `hybrid` | Reciprocal Rank Fusion of FTS5 + vector | Best overall relevance |

## Architecture

```
User Query
    │
    ├── fts5    → SQLite FTS5 MATCH
    ├── vector  → TF-IDF → cosine similarity with stored embeddings
    └── hybrid  → RRF merge of fts5 + vector results
                      │
                      ▼
               memory_hub.sqlite
               ├── memories (table + FTS5 index)
               └── memory_embeddings (memory_id → JSON vector)
```

## How It Works

### Embedding Generation
1. **TF-IDF Vectorizer** — Pure Python implementation (no numpy/scipy/sentence-transformers)
   - Tokenizes text into words
   - Builds vocabulary from all memory content
   - Computes TF-IDF weighted vectors (256-dim by default)
   - L2-normalizes for cosine similarity

2. **Automatic Reindexing** — When the vectorizer is fitted, all existing embeddings are recomputed automatically

3. **Provider Interface** — Extensible design for swapping embedding providers:
   - `TFIDFEmbeddingProvider` — Current default (no external deps)
   - `NineRouterEmbeddingProvider` — Uses 9Router's `/v1/embeddings` API (OpenAI-compatible)

### Database Schema
```sql
CREATE TABLE IF NOT EXISTS memory_embeddings (
    memory_id INTEGER PRIMARY KEY,
    vector TEXT NOT NULL,  -- JSON array of floats
    model TEXT NOT NULL DEFAULT 'tfidf',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);
```

## API Reference

### Search Endpoints

```
GET /api/zes/memory/search?q=<query>&mode=<mode>&limit=<n>

Parameters:
  q       - Search query (required)
  mode    - Search mode: fts5 (default), vector, hybrid
  limit   - Max results (default: 20)
```

**Response:**
```json
{
  "count": 3,
  "mode": "vector",
  "results": [
    {
      "id": 5,
      "content": "Codex CLI is the primary coding agent",
      "type": "fact",
      "priority": "medium",
      "tags": "codex",
      "_score": 0.4747,
      "_search_mode": "vector"
    }
  ]
}
```

### Status Endpoint
```
GET /api/zes/memory/status

Response:
{
  "healthy": true,
  "memories": 42,
  "embeddings": 42,
  "search_modes": ["fts5", "vector", "hybrid"],
  "db_path": "memory_hub.sqlite",
  "provider": "zes_memory"
}
```

### Reindex Endpoint
```
POST /api/zes/memory/reindex

Response:
{
  "success": true,
  "reindexed": 42
}
```

## CLI Usage

```bash
# Full-text search
zes-memory search "agent"

# Semantic vector search
zes-memory search --mode vector "coding agent"

# Hybrid search
zes-memory search --mode hybrid "memory system"

# Reindex all embeddings
zes-memory reindex

# Status
zes-memory status
```

## Dashboard UI

The Memory Hub page (`/memory` on both dashboards) includes:

- **Status panel** — Shows healthy status, memory count, embedding count, search modes
- **Search mode switcher** — Toggle between FTS5 / Vector / Hybrid modes
- **Score display** — Relevance scores shown per result (vector mode) or RRF scores (hybrid mode)
- **FTS5 placeholder** — Updates dynamically to show current mode

## Files Modified

| File | Change |
|------|--------|
| `hermes-agent-full/plugins/memory/zes_memory/embeddings.py` | **New** — TF-IDF vectorizer, cosine similarity, embedding providers |
| `hermes-agent-full/plugins/memory/zes_memory/store.py` | **Updated** — embeddings table, search_semantic(), search_hybrid(), reindex_embeddings() |
| `zes-system-v2/api/server.py` | **Updated** — mode param, embeddings count, reindex endpoint |
| `~/.local/bin/zes-memory` | **Updated** — --mode flag, reindex command |
| `zes-os-v2/app/memory/page.tsx` | **Updated** — mode switcher, score display |

## Future Improvements

- [ ] **sqlite-vec extension** — Native vector search when Termux-compatible `.so` is available
- [ ] **9Router embeddings** — Configure OpenAI-compatible embedding models via 9Router
- [ ] **Sentence-Transformers** — Local embedding models for higher quality
- [ ] **Multi-vector indexing** — HNSW or IVF indices for faster search at scale
- [ ] **Cross-agent sync** — Automatically embed memories from Codex, Hermes, Claude Code
