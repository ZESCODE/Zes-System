---
name: ZES-parallel-research
description: Spawns multiple AI sub-agents across different models/providers for parallel deep research, then synthesizes results into comprehensive reports. Use for any topic requiring thorough multi-perspective analysis.
metadata:
  origin: ZES
  version: 1.0.0
---

# ZES Parallel Research — Multi-Model Sub-Agent Swarm

> Spawn N parallel AI agents (default 4) across different providers (OpenRouter/DeepSeek V4, BitRouter/GPT-5.4, Groq/Llama 70B, Gemini 3.5 Flash) to research a topic from multiple angles simultaneously, then synthesize into a final report.

## When to Use

- User asks to "deep research" or "thoroughly investigate" any topic
- Need multi-perspective analysis (technical, business, news, critical)
- Competitive analysis, technology evaluation, market research
- Any question where a single model's perspective might be incomplete
- User says "research", "deep dive", "spawn agents", "parallel research"

## Quick Start

```bash
# Basic research (3 agents, auto-synthesized)
zes research "Impact of AI on software development"

# Or use the direct command:
zes-research "How will quantum computing affect cryptography?"

# Specify number of agents (1-6)
zes research "Rust vs Go performance" --agents 6

# Choose specific providers
zes research "Topic" --providers bitrouter_gpt openrouter_key groq_key

# Save report to file
zes research "Topic" --output ~/research/report.md

# Check which providers are available
zes research --check

# Raw results without synthesis
zes research "Topic" --no-synthesize

# Silent mode (just the report, no progress)
zes research "Topic" --silent
```

## Available Providers

| Provider Key | Model | Best For |
|-------------|-------|----------|
| `openrouter` | DeepSeek V4 Flash | Technical depth, analysis |
| `bitrouter_gpt` | GPT-5.4 Mini | Structured writing, synthesis |
| `groq` | Llama 3.3 70B | Fast broad coverage |
| `bitrouter_gemini` | Gemini 3.5 Flash | Comprehensive reasoning |
| `mistral` | Mistral Medium | Technical docs, code |
| `nvidia` | Llama 3.1 70B | Scientific analysis |

## Research Angles (by agent count)

| Agents | Angles |
|--------|--------|
| 1 | General analysis |
| 2 | Technical + Strategic |
| 3 | Technical + Strategic + Latest Developments |
| 4 | Technical + Strategic + Latest + Critical Analysis |
| 5 | + Practical Implementation |
| 6 | + Comparative Analysis |

## Architecture

```
User: "Research X"
  │
  ▼
zes-research (orchestrator)
  │
  ├── Spawns Agent 1 → OpenRouter/DeepSeek-V4  → "Technical Analysis"
  ├── Spawns Agent 2 → BitRouter/GPT-5.4       → "Strategic Analysis"
  ├── Spawns Agent 3 → Groq/Llama 70B          → "Latest Developments"
  └── Spawns Agent 4 → Gemini 3.5 Flash        → "Critical Analysis"
       │
       ▼ (all 4 run in parallel via asyncio, ~5-15 seconds)
       │
  Synthesis Agent → Final research report
       │
       ▼
  Saved to ~/.zes/research/ + optionally custom path
```

## Output

Each research run is automatically saved to `~/.zes/research/` with a timestamped filename. The report includes:
- Executive summary
- Key findings organized by theme
- Detailed analysis (synthesized across all agents)
- Critical assessment (risks, limitations)
- Conclusions and recommendations

## Integration with Hermes

Hermes can use this for its background review loop and strategic planning:

```bash
# In Hermes' soul.md or background_review.py:
# - Run periodic research on system improvement topics
# - Spawn parallel research for strategic decisions
# - Store reports in memory hub via fact_store
```

## Example Output

```markdown
# ZES Parallel Research Report

**Topic:** Impact of AI on software development
**Generated:** 2026-07-23 21:45:00
**Agents:** 4 (openrouter→Technical, bitrouter_gpt→Strategic, 
               groq→Latest, bitrouter_gemini→Critical)

## Executive Summary
AI is transforming software development across three dimensions:
1. Code generation (LLMs producing production code)
2. Automated testing and debugging
3. Architectural design assistance
...
```
