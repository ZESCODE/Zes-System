---
name: ZES-model-router
description: Smart provider/model selection skill. Automatically selects the best (cheapest, fastest, most capable) provider for each task type — code, writing, reasoning, analysis, speed. Integrates with zes research and zes batch for optimal routing.
metadata:
  origin: ZES
  version: 1.0.0
---

# ZES Model Router — Smart Provider Selection

## Decision Matrix

| Task Type | Best Provider | Model | Why |
|-----------|--------------|-------|-----|
| **Code generation** | OpenRouter | DeepSeek V4 Flash | Best code output, 128K context, free |
| **Code review** | Groq | Llama 3.3 70B | Fastest (1-2s), good analysis |
| **Writing / structured** | BitRouter | GPT-5.4 Mini | Best formatting, reliable |
| **Deep reasoning** | BitRouter | Gemini 3.5 Flash | Strong reasoning, free tier |
| **Speed-critical** | Groq | Llama 3.3 70B | ~300ms response, 30 req/min |
| **Deep research** | OpenRouter | DeepSeek V4 Flash | 128K context, technical depth |
| **Synthesis / fusion** | GitHub Models | GPT-4.1 | Best at combining multiple inputs |
| **Classification** | Groq | Llama 3.3 70B | Fast, reliable, cheap |
| **Extraction** | Groq | Llama 3.3 70B | Fast structured output |
| **Creative writing** | BitRouter | GPT-5.4 Mini | Best creative output |
| **Technical analysis** | OpenRouter | DeepSeek V4 Flash | Strong technical reasoning |
| **Business analysis** | BitRouter | Gemini 3.5 Flash | Broad knowledge, balanced |
| **Translation** | Mistral | Mistral Medium | Multi-lingual strength |
| **Scientific** | NVIDIA | Llama 3.1 70B | Scientific corpus training |
| **Long documents** | OpenRouter | DeepSeek V4 Flash | 128K native context |
| **Code generation** | LLM7 | Codestral Latest | 1M tokens/day free, dedicated code model |
| **Lightweight tasks** | LLM7 | MiniMax M2.7 | Fast, cheap, good for classification |
| **Ultra-fast inference** | Cerebras * | Llama 3.3 70B | 1,800+ tok/s — sign up at inference.cerebras.ai |

*Requires CEREBRAS_API_KEY in master.env

## Provider Capabilities

| Provider | Speed | Quality | Context | Rate Limit | Free Tier |
|----------|-------|---------|---------|------------|-----------|
| **Groq** | ⚡⚡⚡⚡⚡ | ⚡⚡⚡ | 32K | 30 req/min | ✅ Yes |
| **OpenRouter** | ⚡⚡⚡ | ⚡⚡⚡⚡⚡ | 128K | Variable | ✅ Yes |
| **BitRouter GPT** | ⚡⚡⚡⚡ | ⚡⚡⚡⚡ | 128K | Key-based | Key-based |
| **BitRouter Gemini** | ⚡⚡⚡ | ⚡⚡⚡⚡ | 1M | 1500 req/day | ✅ Yes |
| **Mistral** | ⚡⚡⚡ | ⚡⚡⚡⚡ | 32K | 1 req/min | ✅ Yes |
| **NVIDIA** | ⚡⚡ | ⚡⚡⚡ | 128K | 1000 req/day | ✅ Yes |
| **GitHub Models** | ⚡⚡ | ⚡⚡⚡⚡⚡ | 128K | 1 req/min/model | ✅ Free w/ PAT |
| **LLM7** | ⚡⚡⚡ | ⚡⚡⚡⚡ | 32K | 1M tok/day | ✅ Free tier |

## Routing Logic

### For `zes research`

The research engine auto-selects providers based on number of agents:

```
1 agent:  OpenRouter (DeepSeek V4) — most capable generalist
2 agents: OpenRouter + BitRouter GPT — technical + structured
3 agents: + Groq — adds speed/latest developments
4 agents: + Gemini — adds critical analysis
5 agents: + Mistral — adds practical implementation
6 agents: + NVIDIA — adds comparative analysis
```

### For `zes batch`

The batch processor round-robins across ALL available providers to:
- Distribute load evenly
- Avoid hitting any single rate limit
- Get diverse perspectives
- Maximize throughput (~60 tasks/min)

### For Synthesis

Use the most powerful model available for final synthesis:
1. GitHub Models GPT-4.1 (best quality) — but rate limited
2. BitRouter GPT-5.4 Mini (fast, reliable)
3. OpenRouter DeepSeek V4 (backup)

## Quick Reference

```bash
# Research: let the engine choose
zes research "Topic" --agents 4

# Research: force specific providers
zes research "Topic" --providers openrouter_key groq_key bitrouter_gpt

# Batch: all providers round-robin
zes batch tasks.txt

# Batch: specific providers only
zes batch tasks.txt --providers groq bitrouter_gpt

# Check what's available
zes --check
```

## Example: Manual Selection

Based on the routing matrix, for any given task you can select the optimal model:

```python
# Python decision function
def pick_provider(task_type):
    if task_type in ("code", "technical", "deep_research"):
        return "openrouter_key"
    elif task_type in ("speed", "classification", "extraction"):
        return "groq_key"
    elif task_type in ("writing", "structured", "creative"):
        return "bitrouter_gpt"
    elif task_type in ("reasoning", "analysis"):
        return "bitrouter_gemini"
    elif task_type in ("synthesis", "fusion"):
        return "github_key"  # or bitrouter_gpt
    else:
        return "openrouter_key"  # default: most capable
```
