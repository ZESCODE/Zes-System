---
category: Memory

name: ZES-cost-tracker
description: API cost tracking and budget management — monitor token usage, spending, and budgets across all LLM providers.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Cost Tracker

Tracks API spending across all ZES LLM providers.

## Monitoring
```bash
# 9Router usage stats
curl http://localhost:20128/api/usage 2>/dev/null

# Hermes session cost
# Check Hermes dashboard for token counts
```

## Budget Strategy
- Primary routing: 9Router free tier (Groq, NVIDIA, Cloudflare)
- Fallback: Gemini free tier
- Paid: OpenAI/Anthropic via Cloudflare AI Gateway proxy (usage tracked)
- Daily budget alerts via Hermes notifications
