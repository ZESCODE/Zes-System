---
category: Orchestration

name: ZES-agentic-core
description: Core agent behavior patterns — agentic engineering, eval-first execution, decomposition, and cost-aware model routing for the ZES system.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Agentic Core

Defines how ZES agents behave: decompose tasks, evaluate, route, and execute.

## Principles
1. **Agent-First** — Delegate to specialized agents for domain tasks
2. **Test-Driven** — Write tests before implementation, 80%+ coverage
3. **Security-First** — Never compromise on security; validate all inputs
4. **Plan Before Execute** — Plan complex features before writing code

## Agent Roles
| Agent | Purpose |
|-------|---------|
| Codex | Primary coding agent |
| Hermes | Persistent agent with memory |
| OpenClaude | Terminal chat UI + tools |
| ZESMemoryProvider | Memory authority |
| 9Router | LLM routing gateway |

## Model Routing via 9Router
- Free tier: Groq, NVIDIA, Cloudflare Workers AI, Gemini
- Paid tier: OpenAI, Anthropic (via Cloudflare proxy)
- Cost-aware: route to cheapest available for each task type
