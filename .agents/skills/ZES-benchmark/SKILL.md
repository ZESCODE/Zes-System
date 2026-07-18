---
category: Research

name: ZES-benchmark
description: Performance benchmarking — measure response times, throughput, and resource usage across ZES services and LLM providers.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Benchmark

Measures performance of ZES services and LLM providers.

## LLM Provider Benchmarks
```bash
# Test provider response time
time curl -s http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"groq/llama-3.3-70b-versatile","messages":[{"role":"user","content":"Say hi"}],"max_tokens":10}'
```

## Service Health Benchmarks
```bash
# Dashboard response time
time curl -s http://localhost:5173 > /dev/null

# Memory hub response time
time curl -s http://localhost:9119/api/health > /dev/null
```

## Metrics to Track
- LLM first-token latency
- Dashboard page load time
- Memory write throughput
- Background review completion time

---
### Merged from ZES-benchmark-methodology

---
name: benchmark-methodology
description: >-
  Use after competitive-platform-analysis has produced a tiered competitor set.
  Scores each competitor across nine weighted dimensions (positioning, voice,
  visual craft, offer packaging, evidence, enterprise-readiness, thought
  leadership, pricing, client's strategic tension) with explicit 1–5 rubrics
  and a tension-plot. Precedes competitive-report-structure.
---

# Benchmark Methodology

Use this skill to turn a scoped competitor set into **comparable, defensible
scores**. Each competitor is assessed on the same nine dimensions, with
explicit 1–5 rubrics, then captured in a uniform profile card. Consistency is
the point: scores are only useful if the same evidence would earn the same
number for any competitor.

## When to Activate

- A scoped, tiered competitor set from competitive-platform-analysis is ready to score.
- Need comparable, evidence-anchored scores across competitors — not gut-feel rankings.
- Client's strategic tension (the paired axes defining their target white-space) has been established.
- Preparing to produce profile cards for assembly in competitive-report-structure.

## Client positioning brief (establish first)

Before scoring, establish the client's positioning brief. It supplies:

- **Strategic tension** — the two axes (e.g., memorability × hireability) whose
  intersection marks the client's target white-space. Dimension 9 is always
  the client's named tension; report both poles separately, never averaged.
- **Differentiator** — what makes the client's moat. This informs which
  dimensions matter most for the client's positioning argument.
- **Brand balance** — the intended mix of distinct strategic emphases. Strategic
  recommendations must not break this balance without flagging it.

## Why these dimensions

The client competes on a **specific tension held across two poles**, not on
service breadth. The dimensions are weighted to reflect that moat. Two
dimensions — the tension poles — are scored **separately and never averaged
together**, because the client's strategic question is precisely whether a rival
achieves both simultaneously.

## The nine dimensions (with weights)

Weights guide synthesis emphasis, not a single blended score (avoid a false
composite — see Bias controls). Sum = 100%.

1. **Positioning clarity & distinctiveness** (18%) — Is the studio's position
   sharp, ownable, and instantly legible? Or generic?
2. **Brand voice / verbal distinctiveness** (15%) — Does the copy have an
   ownable register, or is it interchangeable agency-speak?
3. **Visual identity & site craft** (15%) — Quality and ownership of the visual
   system; site as proof-of-craft.
4. **Service offer & packaging** (12%) — Productized and legible (named
   sprints/audits) vs vague. Packaging maturity.
5. **Evidence & credibility** (12%) — Named clients, quantified outcomes,
   case-study depth. Proof beyond assertion.
6. **Enterprise-readiness / commercial maturity** (10%) — Signals they can land
   and hold SaaS/fintech/B2B/enterprise work (process, logos, scale, contracts).
7. **Thought leadership / content presence** (8%) — Owned POV: writing, talks,
   newsletters, frameworks. Depth over volume.
8. **Pricing transparency & engagement model** (5%) — Is pricing/engagement
   legible? Productized vs bespoke vs opaque.
9. **[Client's strategic tension]** (5% as a flag; **score BOTH poles,
   report separately**) — Read the tension name and axis descriptions from the
   client's positioning brief. Plot both; the gap is the insight. The client's
   target quadrant is the single most important finding: who else is already
   there?

## Scoring rubric (1–5, applies to dimensions 1–8)

Anchor every score to observable evidence. Generic descriptors below; adapt the
specifics per dimension but keep the level meaning constant.

- **1 — Absent / generic.** No discernible position or craft; indistinguishable
  from a template. Active liability.
- **2 — Below par.** Some intent but inconsistent, derivative, or unconvincing.
  Wouldn't survive a side-by-side.
- **3 — Competent / table-stakes.** Solid, professional, unremarkable. Meets
  expectation, ownable by nobody.
- **4 — Strong / distinctive.** Clearly above peers; a real strength a buyer
  would notice and cite.
- **5 — Category-defining.** Best-in-class, ownable, hard to imitate. Sets the
  bar others react to.

### Tension axes (dimension 9) — score each 1–5

Read the axis labels and their 1/3/5 anchors from the client's positioning
brief. Example anchors for a memorability × credibility tension:

- **Memorability** — 1: forgotten instantly · 3: recognizable in context ·
  5: unforgettable, talked-about, distinctively owned.
- **Credibility** — 1: feels risky/amateur · 3: safe, competent,
  unexciting · 5: enterprise-trusted, obvious safe choice.

Plot competitors on the tension 2×2. The client's target quadrant is named in
the positioning brief. Who else occupies that quadrant is the single most
important finding of the benchmark.

## How to collect the data

For each competitor, work the dimensions in this order (cheapest signal first):

1. **Competitor's own site** — positioning, voice, offer packaging, pricing
   posture, named clients, manifesto/POV. Screenshot the homepage + one case
   study.
2. **Case studies / work** — evidence depth, quantified outcomes, client names.
   Distinguish *asserted* ("we delivered X") from *proven* (metrics, named,
   verifiable).
3. **Review directories** — corroborate clients, project size, engagement model
   → credibility & enterprise-readiness (e.g. Clutch.co or the niche equivalent).
4. **LinkedIn** — team size/model, founder narrative, content cadence →
   thought leadership, model.
5. **Portfolio / craft platforms** — craft register (use the showcase native to
   the niche: design boards, showreels, published samples, etc.).
6. **Content channels** — newsletter/talks/writing → thought-leadership depth.

**What to record per dimension:** the score, one-line justification, and the
source link/screenshot that earned it. No score without evidence.

## Bias controls

- **No single composite score.** Report dimension scores and the tension plot
  separately. A weighted average hides the asymmetry that matters.
- **Asserted vs proven.** Downgrade credibility/evidence scores for
  self-reported claims with no corroboration. Site copy is marketing, not fact.
- **Aesthetic affinity bias.** Reviewers may over-score studios whose aesthetic
  they share and under-score rivals' commercial strength. Score craft and
  credibility independently; a "boring" site may be winning bigger clients.
- **Recency / flashiness bias.** Award-winning, showpiece work dazzles but may
  lack commercial depth — verify with directories/clients before scoring
  credibility.
- **Survivorship.** The visible, well-marketed studios aren't the whole market;
  note strong-but-quiet operators found via directories/reviews.
- **Calibrate across the set, not in isolation.** Before finalizing, re-read
  scores side-by-side — a "4" must mean the same thing for every competitor.
  Adjust outliers.

## Competitor profile card (output format)

Produce one card per profiled competitor — the atomic unit the report assembles
from:

```
## <Competitor name>
- **Profile / Tier:** <positioning stance · specialization · size band> / <Direct | Adjacent | Aspirational>
- **One-liner:** <how they position themselves, in their words>
- **Model / size / geography:** <solo|micro|boutique> · <region> · <pricing/engagement model>
- **Notable clients / evidence:** <named, with proven/asserted tag>

### Dimension scores
| Dimension | Score (1–5) | Justification (1 line) | Source |
|---|---|---|---|
| Positioning clarity & distinctiveness | | | |
| Brand voice / verbal distinctiveness | | | |
| Visual identity & site craft | | | |
| Service offer & packaging | | | |
| Evidence & credibility | | | |
| Enterprise-readiness / commercial maturity | | | |
| Thought leadership / content presence | | | |
| Pricing transparency & engagement model | | | |

### Tension plot
- **[Axis 1 from positioning brief]:** <1–5> — <why>
- **[Axis 2 from positioning brief]:** <1–5> — <why>
- **Quadrant:** <high/high | high-1/low-2 | low-1/high-2 | low/low>

### Read for [client]
- **Strength to learn from:** <…>
- **Weakness to exploit / white-space it exposes:** <…>
- **Threat to [client]:** <…>
```

Hand the completed cards plus the tension plot to `competitive-report-structure`.

## Anti-Patterns

- **Averaging the tension axes.** The two poles of the client's strategic tension must be scored and reported separately. Averaging destroys the insight — the gap between poles is the finding.
- **Scoring without evidence.** Every score requires a one-line justification and a source link. A score without evidence is an opinion, not a benchmark.
- **Creating a single composite score.** Report dimension scores individually. A weighted average hides the asymmetric strengths that matter for positioning.
- **Applying generic rubric anchors without adapting.** The 1–5 anchors must be calibrated to the specific dimension and competitor set. The generic descriptions are a starting point, not a fixed standard.
- **Running before the competitor set is scoped.** Use competitive-platform-analysis first to produce a tiered, pruned set. Scoring an unscoped list wastes effort on irrelevant competitors.

## Related Skills

- `competitive-platform-analysis` — the prerequisite; produces the tiered competitor set this skill scores.
- `competitive-report-structure` — the next step; assembles the scored profile cards into a client-deliverable report.

---
### Merged from ZES-evals

---
name: zes-evals
description: Formal evaluation framework for ZES system — define pass/fail criteria, measure 9Router/Hermes/Dashboard reliability, track regressions.
---

# ZES Eval Harness

Eval-driven quality assurance for ZES infrastructure. Define pass/fail criteria for service reliability, measure agent task completion, and track regressions.

## When to Activate

- Setting up quality gates for ZES deployments
- Defining what "healthy" means for each service
- Measuring agent task completion reliability
- Creating regression tests for ZES system changes
- Benchmarking service performance

## Philosophy

Evals are the "unit tests of system reliability":
- Define expected behavior BEFORE making changes
- Run evals continuously via Hermes cron
- Track regressions with each change
- Use pass@k metrics for reliability measurement

## ZES Service Evals

### Service Health Eval

```yaml
eval: service-health
schedule: every 30m via Hermes cron
criteria:
  - service: r9
    check: port 20128 open
    pass: tcp_open("127.0.0.1", 20128)
  - service: hermes
    check: binary exists and responds
    pass: "hermes --version returns 0"
  - service: dashboard
    check: HTTP 200 on /api/status
    pass: http_status("http://localhost:8083/api/status") == 200
  - service: tor
    check: SOCKS5 proxy responding
    pass: tcp_open("127.0.0.1", 9050)
```

### Provider Availability Eval

```yaml
eval: 9router-providers
schedule: hourly
criteria:
  - provider: groq
    check: status is "active"
    pass: provider_status("groq") in ("active", "unknown")
  - provider: cerebras
    check: status is "active"
    pass: provider_status("cerebras") in ("active", "unknown")
  - provider: mistral
    check: status is "active"
    pass: provider_status("mistral") in ("active", "unknown")
  - metric: active_providers
    check: at least 10 of 18 active
    pass: count_active_providers() >= 10
```

## Eval Result Format

```json
{
  "eval": "service-health",
  "timestamp": "2026-07-11T13:00:00Z",
  "results": [
    {"service": "r9", "pass": true, "latency_ms": 2},
    {"service": "hermes", "pass": true, "latency_ms": 5},
    {"service": "dashboard", "pass": true, "latency_ms": 15},
    {"service": "tor", "pass": true, "latency_ms": 1}
  ],
  "summary": {"pass": 4, "fail": 0, "total": 4, "pass_rate": 1.0}
}
```

## Hermes Cron Integration

```bash
# Run evals via Hermes cron job
hermes cron add eval-service-health --schedule "*/30 * * * *" --command '
  python3 /data/data/com.termux/files/home/Zes-System/scripts/run-evals.py \
    --eval service-health \
    --output /data/data/com.termux/files/home/.zes/evals/service-health.json
'
```

## Eval Script Template

```python
#!/usr/bin/env python3
"""ZES eval runner — run evals and output JSON results."""
import json, socket, subprocess, sys, os
from datetime import datetime

def tcp_open(host, port, timeout=1):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((host, port))
        s.close()
        return r == 0
    except: return False

def http_status(url, timeout=3):
    import urllib.request
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=timeout)
        return r.status
    except Exception as e:
        return getattr(e, "code", None)

def run_eval(name, checks):
    results = []
    for c in checks:
        try:
            passed = c["check"]()
        except Exception as e:
            passed = False
        results.append({"name": c["name"], "pass": passed})
    passed = sum(1 for r in results if r["pass"])
    return {
        "eval": name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": results,
        "summary": {"pass": passed, "fail": len(results) - passed, "total": len(results)}
    }

if __name__ == "__main__":
    evals = {
        "service-health": [
            {"name": "9Router", "check": lambda: tcp_open("127.0.0.1", 20128)},
            {"name": "Dashboard", "check": lambda: http_status("http://localhost:8083/api/status") == 200},
            {"name": "Tor SOCKS5", "check": lambda: tcp_open("127.0.0.1", 9050)},
        ]
    }
    eval_name = sys.argv[1] if len(sys.argv) > 1 else "service-health"
    result = run_eval(eval_name, evals.get(eval_name, []))
    print(json.dumps(result, indent=2))
```

## Continuous Evaluation

- **30 min**: Service health evals (via Hermes `dashboard-snapshot`)
- **60 min**: Provider availability evals
- **Daily**: Full system eval (all services + providers + latency)
- **On change**: Run relevant evals before declaring a change done

## Best Practices

1. **Define evals BEFORE making changes** — know what "done" looks like
2. **One criterion per eval item** — focused, measurable checks
3. **Track pass rate over time** — look for regression trends
4. **Alert on critical failures** — Hermes cron can trigger notifications
5. **Store history** — eval results in `~/.zes/evals/` for trend analysis

**Remember**: If you can't measure it, you can't improve it. Evals make ZES reliability measurable.

---
### Merged from ZES-performance

---
name: zes-performance
description: "Benchmark, diagnose, and optimize ZES service performance: startup time, response latency, throughput."
---

# ZES Performance

Use when diagnosing slow services, high CPU, or optimizing ZES system performance.

## Workflow

1. **Establish baseline** before changing anything:
   ```bash
   # Service response time
   time curl -s http://localhost:8083/api/status > /dev/null
   
   # Process CPU/RSS
   ps -o pid,%cpu,rss,cmd -p $(pgrep -f dashboard_v3)
   
   # System load
   uptime && free -h
   ```

2. **Profile the bottleneck**:
   - **Dashboard**: Check Python process CPU, profile with `cProfile`
   - **MCP server**: Check Node.js event loop lag
   - **9Router**: Check proxy connection latency with `curl -w "%{time_total}"`
   - **Hermes**: Check cron job duration in logs

3. **Common ZES optimizations**:

   | Area | Tool | Target |
   |------|------|--------|
   | Dashboard | `python3 -m cProfile` | Reduce startup time |
   | MCP server | `node --prof` | Reduce Chrome CDP round-trips |
   | 9Router | `curl -w` | Reduce provider failover latency |
   | Hermes | cron log grep | Reduce job overlap |
   | Tor | `ss -tlnp` | Reduce connection pool size |

4. **Pick the next attack by return**:
   - High return: one service dominates restore time or RSS
   - High leverage: one config change improves all services
   - Quick win: caching or lazy-loading frequently-used data

5. **Verify**:
   ```bash
   # Same measurement as baseline
   time curl -s http://localhost:<port>/api/status > /dev/null
   ps -o pid,%cpu,rss,cmd -p $(pgrep -f <service>)
   ```

## Benchmark Script

```bash
#!/bin/bash
# Quick latency benchmark
for i in 1 2 3; do
  for url in \
    http://localhost:8083/api/status \
    http://localhost:5900/ \
    http://localhost:20128/; do
    echo -n "$url → "
    curl -so /dev/null -w "status=%{http_code} time=%{time_total}s\n" "$url"
  done
done
```
