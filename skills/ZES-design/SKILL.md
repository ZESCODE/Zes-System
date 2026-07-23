---
name: ZES-design
description: 3-Agent design review — Architecture Reviewer (Groq) + Security Reviewer (OpenRouter) + UX Reviewer (LLM7) in parallel. Synthesizes findings into prioritized report.
---

# ZES Design Review — 3-Agent Edition

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  🏛️  ZES Design Review (zes design --dir ~/project --doc .md) │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 0: Context Gathering                                  │
│  ┌──────────────┐  ┌──────────────────────────────────┐     │
│  │ Project scan │  │ Design document parsing           │     │
│  │ File tree    │  │ Architecture, component listing   │     │
│  │ Source files │  │ Data flow, requirements           │     │
│  └──────────────┘  └──────────────────────────────────┘     │
│                                                              │
│  Phase 1: 3 Parallel Agents (divergent, ~40s)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 🏛️  Architect │  │ 🔒 Security  │  │ 🎨 UX Reviewer  │   │
│  │  Groq        │  │ OpenRouter   │  │ LLM7             │   │
│  │  Llama 3.3   │  │ DeepSeek V4  │  │ Codestral        │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘   │
│         │                 │                 │               │
│         ▼                 ▼                 ▼               │
│  System structure     Attack vectors      User flows       │
│  Modularity           Data protection    Accessibility     │
│  Scalability          Auth/access        Consistency       │
│  Extensibility        Compliance         Cognitive load    │
│                                                              │
│  Phase 2: Synthesizer (convergent, single call)             │
│  └──────────────┐                           ┌──────────────┘
│                  ▼                           ▼               
│         Top 5 Findings (across all 3 dimensions)             
│         Strengths, Quick Wins, Strategic Improvements        
│         Overall Verdict                                     
│                                                              
└──────────────────────────────────────────────────────────────┘
```

## The 3 Design Review Agents

| Agent | Provider | Model | Focus |
|-------|----------|-------|-------|
| **Architecture Reviewer** | Groq | Llama 3.3 70B | Structure, modularity, data flow, scalability, patterns |
| **Security Reviewer** | OpenRouter | DeepSeek V4 Flash | Threat model, auth, data protection, compliance, secrets |
| **UX Reviewer** | LLM7 | Codestral Latest | User flows, accessibility, consistency, cognitive load |

## Pipeline

```
Phase 0: Context Gathering (instant)
  ├── Project structure scan (file tree, sizes, key entry points)
  ├── Design document parsing (architecture, requirements, flows)
  └── Key file content sampling (main entry points)

Phase 1: 3 Parallel Agents (~40s)
  ├── Architecture Reviewer → STRENGTHS, CONCERNS (HIGH/MED/LOW), RECOMMENDATIONS, OVERALL
  ├── Security Reviewer → THREATS (CRITICAL/HIGH/MED/LOW), WEAKNESSES, STRENGTHS, RECOMMENDATIONS
  └── UX Reviewer → STRENGTHS, ISSUES (HIGH/MED/LOW), ACCESSIBILITY, RECOMMENDATIONS

Phase 2: Synthesizer (single call, ~3s)
  └── Top 5 Findings → Strengths → Quick Wins → Strategic Improvements → Overall Verdict
```

## CLI Usage

```
zes design                              # Review current directory
zes design --dir ~/project              # Review a project's design
zes design --doc design.md              # Review a design document
zes design --dir ~/ --doc spec.md       # Both codebase + design doc
zes design --quick                       # Single synthesis (faster, ~3s)
```

### Options

| Flag | Description |
|------|-------------|
| `--dir`, `-d` | Project directory to review (scans file tree, entry points) |
| `--doc` | Design document path (.md, .txt) |
| `--quick`, `-q` | Single synthesis instead of 3-agent |
| `--verbose`, `-v` | Show full context |

## Output Sections

### Architecture Review
```
STRENGTHS: What the design does well architecturally
CONCERNS: Architectural risks (with HIGH/MED/LOW severity)
RECOMMENDATIONS: Specific improvements
OVERALL: One-sentence verdict
```

### Security Review
```
THREATS: Identified attack vectors (CRITICAL/HIGH/MED/LOW)
WEAKNESSES: Security gaps found
STRENGTHS: Security measures done right
RECOMMENDATIONS: Prioritized security improvements
OVERALL: One-sentence verdict
```

### UX Review
```
STRENGTHS: UX elements done well
ISSUES: Usability problems (HIGH/MED/LOW severity)
ACCESSIBILITY: WCAG considerations
RECOMMENDATIONS: Prioritized UX improvements
OVERALL: One-sentence verdict
```

### Synthesis
```
Top 5 Findings: Cross-cutting critical issues
Strengths: What's working well
Quick Wins: Immediate fixes
Strategic Improvements: Larger changes
Overall Verdict: One-sentence design quality assessment
```

## When to Run

| Scenario | Why |
|----------|-----|
| **Before building** | Review design doc before implementation starts |
| **After prototype** | Catch issues before they're embedded |
| **Before code review** | Pre-filter design-level feedback |
| **Architecture decision** | Evaluate trade-offs from multiple angles |
| **Security audit** | Systematic threat modeling |

## Example Output

```
zes design --dir ~/Zes-Orchestration-System/scripts
```

**Architecture:** Identified hooks directory coupling, module boundary issues
**Security:** 10 attack vectors cataloged (command injection, hardcoded secrets, insecure deserialization)
**UX:** Noted lack of UI, inconsistent naming, documentation gaps
**Synthesis:** 5 critical findings, 4 quick wins, 3 strategic improvements

## Pair With

- `ZES-brainstorming` — Generate design ideas before reviewing them
- `ZES-systematic-debugging` — When design reviews reveal issues to debug
- `ZES-quality-gate` — Quality gate the implementation after design review
- `ZES-verification-before-completion` — Verify design doc meets requirements
- `ZES-cost-tracker` — Estimate cost impact of design recommendations
