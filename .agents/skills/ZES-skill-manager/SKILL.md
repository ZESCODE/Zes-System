---
category: Orchestration

name: ZES-skill-manager
description: Unified skill lifecycle management — discover, install, audit, and create skills across ZES, ECC, and plugin skill sources.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Skill Manager

Combines skill-scout + skill-stocktake into a unified skill lifecycle tool.

## Skill Sources (Priority Order)
1. `.agents/skills/ZES-*` — ZES-prefixed (highest)
2. `~/.codex/plugins/cache/` — Plugin skills
3. `~/.codex/skills/shared_skills/` — Shared skills
4. `~/.codex/skills/.system/` — System skills

## Commands
```bash
# Discover all skills
ls .agents/skills/ | sort

# Audit skill quality
cat .agents/skills/<name>/SKILL.md | head -20
```

## Creating New Skills
Use `skill-creator` skill for guide on creating effective skills.
Place in `.agents/skills/<skill-name>/SKILL.md`.
