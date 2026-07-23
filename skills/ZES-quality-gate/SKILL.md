---
name: ZES-quality-gate
description: 3-Agent code quality gate — Lint (Groq) + Security (OpenRouter) + Coverage (LLM7) running in parallel. Local checks + AI analysis + synthesized PASS/FAIL decision.
---

# ZES Quality Gate — 3-Agent Edition

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  🏛️  ZES Quality Gate (zes quality --dir ~/project)          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 0: Local Tools (instant parallel)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Python syntax │  │ Secret scan  │  │ pytest + coverage│   │
│  │ py_compile    │  │ grep secrets │  │ tests + cov %    │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  Phase 1: 3 AI Agents (parallel, ~20s)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 🔎 Lint      │  │ 🔒 Security  │  │ 🧪 Coverage      │   │
│  │  Groq        │  │ OpenRouter   │  │ LLM7             │   │
│  │  Llama 3.3   │  │ DeepSeek V4  │  │ Codestral        │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘   │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  Code style bugs    Secret exposure     Test coverage gaps  │
│  Import errors      Injection vulns     Missing assertions  │
│  Syntax issues      Unsafe patterns     Weak test design    │
│                                                              │
│  Phase 2: Synthesizer (single call)                         │
│  → Combines all 3 reports + local results                   │
│  → Makes PASS/FAIL/PASS_WITH_WARNINGS decision              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## The 3 Quality Agents

| Agent | Provider | Model | Focus |
|-------|----------|-------|-------|
| **Lint** | Groq | Llama 3.3 70B | Code style, imports, syntax, complexity, dead code |
| **Security** | OpenRouter | DeepSeek V4 Flash | Secrets, injection, eval/exec, path traversal, vulns |
| **Coverage** | LLM7 | Codestral Latest | Test coverage %, test quality, missing tests, edge cases |

## Pipeline

```
Phase 0: Local Checks (instant)
  ├── Python syntax validation (compile all .py files)
  ├── Secret scanning (grep for API keys, tokens, passwords)
  └── Test runner (pytest quick run + coverage report)

Phase 1: AI Agents (parallel, ~20s)
  ├── Lint Agent → Code quality report with CRITICAL/WARNING/INFO
  ├── Security Agent → Vulnerability report with secrets found
  └── Coverage Agent → Test quality report with coverage gaps

Phase 2: Gate Decision (single call)
  └── Synthesizer → PASS / FAIL / PASS_WITH_WARNINGS + action items
```

## CLI Usage

```
zes quality                           # Full AI quality gate on current dir
zes quality --dir ~/project           # Specific project
zes quality --quick                   # Local checks only (no AI, ~5s)
zes quality --ci                      # CI mode — exit 1 on FAIL
zes quality --verbose                  # Show full codebase context
zes quality --quick --dir ~/project   # Fast local-only check
```

## CI Integration

```yaml
# GitHub Actions example
- name: ZES Quality Gate
  run: |
    source ~/.secure-credentials/master.env
    zes quality --dir . --ci
  # Exits 1 if gate FAILS, blocking the pipeline
```

## When to Run

| When | Why | Mode |
|------|-----|------|
| **Before every commit** | Catch issues early | `--quick` |
| **Before PR submission** | Full quality audit | Default |
| **Before deployment** | Hard quality gate | `--ci` |
| **On new dependencies** | Security scan | Default |
| **Weekly codebase health** | Trend tracking | `--verbose` |

## Gate Decision Rules

| Decision | Criteria |
|----------|----------|
| ✅ **PASS** | No critical issues, < 5 warnings, coverage ≥ 80% |
| ⚠️ **PASS_WITH_WARNINGS** | Minor issues only, no security vulns, coverage ≥ 50% |
| ❌ **FAIL** | Critical bugs, hardcoded secrets, coverage < 50% |

## Local Checks (Quick Mode — No AI)

Even without AI agents, the gate runs:
- **Python syntax**: Compiles every `.py` file for syntax errors
- **Secret scan**: Greps for API keys (`sk-`, `ghp_`, `AKIA`), tokens, passwords
- **Test runner**: Runs `pytest` with quick mode, checks coverage

## Pair With

- `ZES-systematic-debugging` — After a FAIL, debug the root cause
- `ZES-parallel-research` — Research unfamiliar security patterns
- `ZES-model-router` — Fine-tune which model each agent uses
- `cdp-audit` — Browser-level quality checks
