---
name: ZES-brainstorming
description: 3-Agent divergent brainstorming — Technical Architect (Groq) + Market Strategist (OpenRouter) + UX Designer (LLM7) in parallel. Synthesizes 2-3 approaches with trade-offs.
---

# ZES Brainstorming — 3-Agent Edition

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  💡 ZES Brainstorm (zes brainstorm "topic")                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 1: 3 Parallel Agents (divergent, ~25s)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 🔧 Technical │  │ 📈 Market    │  │ 🎨 UX Designer   │   │
│  │  Architect   │  │  Strategist  │  │                  │   │
│  │  Groq        │  │ OpenRouter   │  │ LLM7             │   │
│  │  Llama 3.3   │  │ DeepSeek V4  │  │ Codestral        │   │
│  │  temp: 0.8   │  │ temp: 0.8    │  │ temp: 0.8        │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘   │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  Architecture         Market need        User journeys     │
│  Tech stack           Competition        Interaction design│
│  Feasibility          Value prop         Accessibility     │
│  Implementation       Business model     Usability         │
│                                                              │
│  Phase 2: Synthesizer (convergent, single call)             │
│  └──────────────┐                           ┌──────────────┘
│                  ▼                           ▼               
│        2-3 Approaches with trade-offs                         
│        Recommended approach                                  
│        Next steps                                             
│                                                              
│  Phase 3: Design Document Saved                              
│  └── docs/superpowers/specs/YYYY-MM-DD-topic-brainstorm.md   
│                                                              
└──────────────────────────────────────────────────────────────┘
```

## The 3 Brainstorming Agents

| Agent | Provider | Model | Perspective | Temperature |
|-------|----------|-------|-------------|-------------|
| **Technical Architect** | Groq | Llama 3.3 70B | Architecture, tech stack, feasibility | 0.8 (creative) |
| **Market Strategist** | OpenRouter | DeepSeek V4 Flash | Market fit, competition, business model | 0.8 (creative) |
| **UX Designer** | LLM7 | Codestral Latest | User flows, interaction, accessibility | 0.8 (creative) |

Higher temperature (0.8) enables creative divergence — each agent thinks differently.

## Pipeline

```
Phase 1: 3 Parallel Agents (~25s)
  ├── Technical Architect → Architecture, components, tech stack, risks, MVP scope
  ├── Market Strategist → Problem, target users, competition, value prop, TAM
  └── UX Designer → User needs, key flows, interaction design, accessibility, risks

Phase 2: Synthesizer (single call, ~3s)
  └── Combines all 3 perspectives → 2-3 approaches with trade-offs → recommendation → next steps

Phase 3: Design Document Saved
  └── docs/superpowers/specs/YYYY-MM-DD-topic-brainstorm.md
```

## CLI Usage

```
zes brainstorm "Build a CLI tool for project scaffolding"
zes brainstorm "AI-powered code review bot" --dir ~/project
zes brainstorm "Markdown note-taking app" --output ~/designs/
zes brainstorm "Feature: real-time collaboration" --quick
```

### Options

| Flag | Description |
|------|-------------|
| `--dir`, `-d` | Project directory for context (README, git log, file listing) |
| `--output`, `-o` | Output directory for design document |
| `--quick`, `-q` | Single synthesis instead of 3-agent (faster, ~3s) |
| `--save-only` | Save document without full terminal output |
| `--verbose`, `-v` | Show full context |

## Output

A markdown design document with:

```
# Brainstorming: [Topic]

## 1. Perspectives
### 🔧 Technical Perspective
### 📈 Market Perspective
### 🎨 UX Perspective

## 2. Synthesized Approaches
- Approach 1: [Name] — trade-off, risk level
- Approach 2: [Name] — trade-off, risk level
- Recommended: [Which and why]
- Next Steps: [What to validate first]
```

Saved to `docs/superpowers/specs/YYYY-MM-DD-topic-brainstorm.md`.

## When to Run

| Scenario | Why |
|----------|-----|
| **Starting a new feature** | Get diverse perspectives before coding |
| **Architecture decision** | Compare approaches from multiple angles |
| **Product planning** | Evaluate market fit alongside feasibility |
| **Design exploration** | UX-first thinking with technical reality check |
| **Quick idea validation** | `--quick` mode for rapid feedback |

## Examples

### Full 3-Agent (recommended)
```
zes brainstorm "Build a CLI tool for AI-powered code review"
```
→ Technical: architecture, tech stack, feasibility assessment
→ Market: competition analysis, value proposition, TAM
→ UX: user flows, interaction design, usability risks
→ Synthesis: 3 approaches (integrate with linters / custom engine / API-based)

### Quick Mode
```
zes brainstorm "Markdown note-taking app" --quick
```
→ Single call, 3s, still gives 2-3 approaches with recommendation

### With Project Context
```
zes brainstorm "Real-time collaboration" --dir ~/my-project
```
→ Agents see your README, recent commits, and file structure

## Pair With

- `ZES-design` — After brainstorming, formalize into a design spec
- `ZES-writing-plans` — Break down the chosen approach into implementation plan
- `ZES-parallel-research` — Research technologies recommended by Technical Architect
- `ZES-quality-gate` — Verify quality before implementing brainstormed features
