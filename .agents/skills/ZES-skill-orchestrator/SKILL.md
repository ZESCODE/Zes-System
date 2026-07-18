---
category: Orchestration

name: ZES-skill-orchestrator
description: Master skill orchestrator for the ZES ecosystem. Discovers, loads, and coordinates all 28 ZES skills. Use when starting any session — establishes skill hierarchy and routing rules.
metadata:
  origin: ZES
  version: 1.1.0
  replaces: using-superpowers
  total_skills: 29
---


# ZES Skill Orchestrator

This skill **replaces** `using-superpowers`. It extends skill discovery across ALL ZES and ECC skills.

## Skill Discovery Priority

1. **`.agents/skills/ZES-*`** — ZES-prefixed skills (highest)
2. **`.agents/skills/*`** — ECC workflow skills
3. **Plugin cache** `~/.codex/plugins/cache/` — Superpowers, Build Web Apps, Cloudflare, etc.
4. **`~/.codex/skills/shared_skills/`** — Android, Telegram, Twitter, etc.
5. **`~/.codex/skills/`** — Global agent instructions

## All 28 ZES Skills

### Core (15)
| Skill | Purpose |
|-------|---------|
| `ZES-skill-orchestrator` | Skill discovery & routing (this skill) |
| `ZES-service-orchestrator` | Service lifecycle (start/stop/monitor) |
| `ZES-integration` | Cross-agent orchestration |
| `ZES-memory-ops` | Memory hub operations |
| `ZES-agentic-core` | Core agent behavior |
| `ZES-skill-manager` | Skill lifecycle management |
| `ZES-provider-manager` | LLM provider config |
| `ZES-cost-tracker` | API cost tracking |
| `ZES-context-manager` | Context window budget |
| `ZES-dashboard` | Dashboard building |
| `ZES-design` | Design system |
| `ZES-quality-gate` | Quality enforcement |
| `ZES-safety` | Safety checks |
| `ZES-benchmark` | Performance benchmarking |
| `ZES-9router` | 9Router management |
| `ZES-github-research` | Deep GitHub research |

### Superpowers (13)
| Skill | Purpose |
|-------|---------|
| `ZES-brainstorming` | Collaborative design |
| `ZES-dispatching-parallel-agents` | Multi-agent parallel execution |
| `ZES-executing-plans` | Execute implementation plans |
| `ZES-finishing-a-development-branch` | Merge/PR/cleanup |
| `ZES-receiving-code-review` | Technical review reception |
| `ZES-requesting-code-review` | Dispatch review agents |
| `ZES-subagent-driven-development` | Plan via subagents |
| `ZES-systematic-debugging` | Structured debugging |
| `ZES-test-driven-development` | TDD workflow |
| `ZES-using-git-worktrees` | Git workspace isolation |
| `ZES-verification-before-completion` | Verification gate |
| `ZES-writing-plans` | Plan creation |
| `ZES-writing-skills` | Skill authoring |

## Quick Discovery
```bash
ls .agents/skills/ | grep "^ZES-" | sort
```
