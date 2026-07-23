---
name: ZES-cost-tracker
description: 3-Agent cost analysis — Usage Analyzer (Groq) + Cost Optimizer (OpenRouter) + Budget Forecaster (LLM7) in parallel. Real usage tracking via usage.log.
---

# ZES Cost Tracker — 3-Agent Edition

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  💰 ZES Cost Tracker (zes cost)                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 0: Data Collection (instant)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Usage log    │  │ Output files │  │ Active services  │   │
│  │ ~/.zes/usage │  │ Recent tasks │  │ sv status        │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│  Phase 1: 3 AI Agents (parallel, ~35s)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 📊 Usage     │  │ 💰 Optimizer │  │ 🔮 Forecaster    │   │
│  │  Groq        │  │ OpenRouter   │  │ LLM7             │   │
│  │  Llama 3.3   │  │ DeepSeek V4  │  │ Codestral        │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘   │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  Provider costs      Savings opps        Monthly proj.     │
│  Token estimates     Optimal routing     Growth trends     │
│  Free tier status    Waste detection     Anomaly alerts    │
│                                                              │
│  Phase 2: Synthesizer → HEALTHY / CAUTION / OVER_BUDGET     │
└──────────────────────────────────────────────────────────────┘
```

## The 3 Cost Agents

| Agent | Provider | Model | Focus |
|-------|----------|-------|-------|
| **Usage Analyzer** | Groq | Llama 3.3 70B | Provider costs, token estimates, free tier status, trends |
| **Cost Optimizer** | OpenRouter | DeepSeek V4 Flash | Savings, routing optimization, waste detection |
| **Budget Forecaster** | LLM7 | Codestral Latest | Monthly projections, growth trends, anomaly alerts |

## Data Sources

| Source | What It Provides |
|--------|-----------------|
| `~/.zes/usage.log` | Every `zes` command with timestamp (auto-logged by CLI) |
| `~/.zes/research/*.md` | Output files for token estimation (~4 chars ≈ 1 token) |
| `sv status` | Active services |
| Known pricing table | Per-provider input/output costs and free tier limits |

## Provider Pricing (Reference)

| Provider | Input $/M | Output $/M | Free Tier |
|----------|-----------|------------|-----------|
| Groq | $0.59 | $0.79 | ✅ Yes |
| OpenRouter DeepSeek V4 | $0.15 | $0.60 | ❌ No |
| LLM7 Codestral | $0.00 | $0.00 | ✅ 1M/day |
| OpenCode Zen MiMo | $0.00 | $0.00 | ✅ Unlimited |
| GitHub Models | $0.15 | $0.60 | ✅ 1.5M/day |
| BitRouter Gemini | $0.00 | $0.00 | ✅ 1k/day |
| Mistral Medium | $0.10 | $0.30 | ❌ No |
| NVIDIA Llama 3.1 | $0.10 | $0.10 | ❌ No |
| BitRouter GPT | $0.50 | $1.50 | ❌ No |

## Pipeline

```
Phase 0: Data Collection (instant)
  ├── Usage log (last 20 commands, command breakdown)
  ├── Output files (size-based token estimation)
  ├── Active services (running daemons)
  └── Pricing data (all providers with free tier info)

Phase 1: 3 AI Agents (~35s)
  ├── Usage Analyzer → PROVIDER_COSTS + FREE_TIER + TOP_CONSUMERS + PATTERNS
  ├── Cost Optimizer → SAVINGS + OPTIMAL_ROUTING + WASTE
  └── Budget Forecaster → PROJECTION + GROWTH + ANOMALIES + ALERTS

Phase 2: Synthesizer (single call, ~3s)
  └── Monthly Summary → Top 3 Savings → Free Tier Status → Budget Verdict
```

## CLI Usage

```
zes cost                           # Full 3-agent cost analysis
zes cost --quick                   # Quick summary (single AI call, ~7s)
zes cost --verbose                 # Show raw usage data
```

### Options

| Flag | Description |
|------|-------------|
| `--quick`, `-q` | Single AI synthesis instead of 3-agent |
| `--verbose`, `-v` | Show raw data before analysis |

## Output Sections

### Usage Analyzer
```
PROVIDER_COSTS: Table with provider, estimated tokens, cost
FREE_TIER_STATUS: Remaining free quota per provider
TOP_CONSUMERS: Which files/commands use the most
PATTERNS: Usage trends and observations
OVERALL: Cost verdict
```

### Cost Optimizer
```
CURRENT_SPEND: Estimated monthly spend
SAVINGS_OPPORTUNITIES: Specific $ amounts
OPTIMAL_ROUTING: Best provider per task type
WASTE: Unnecessary costs
OVERALL: Optimization verdict
```

### Budget Forecaster
```
MONTHLY_PROJECTION: Next 30 days estimate
GROWTH_TREND: stable / growing / declining
ANOMALIES: Unusual patterns
ALERTS: Free tier deadlines, cost spikes
WHAT_IF: Different routing scenarios
OVERALL: Forecast verdict
```

### Synthesis
```
Monthly Cost Summary
Top 3 Savings
Free Tier Status
Risk Alerts
Budget Verdict: HEALTHY / CAUTION / OVER_BUDGET
```

## Usage Logging

Every `zes` command is automatically logged to `~/.zes/usage.log`:

```
2026-07-24 01:15:00|research|AI trends
2026-07-24 01:16:00|quality|--dir ~/project
2026-07-24 01:17:00|cost|
```

After a week of usage, the cost tracker will have real data to analyze instead of estimates.

## When to Run

| Scenario | Why |
|----------|-----|
| **Weekly budget check** | Monitor usage trends |
| **Before adding a provider** | Evaluate if you need more free tier |
| **Cost spike investigation** | Find what caused the increase |
| **Routing decision** | Compare provider costs |
| **Monthly planning** | Forecast next month's spend |

## Pair With

- `ZES-model-router` — Routing decisions informed by cost analysis
- `ZES-parallel-research` — Research new free providers
- `ZES-verification-before-completion` — Verify cost before deploying
