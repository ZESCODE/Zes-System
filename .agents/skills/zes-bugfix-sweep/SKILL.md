---
name: zes-bugfix-sweep
description: "Fix only small, high-certainty bugs in ZES system services: 9Router, Dashboard, Claude Code, MCP, Hermes, scripts."
---

# ZES Bugfix Sweep

Batch workflow for pasted ZES issue/PR refs.
Triage reviews, proves, and patches local fixes first.

## Principles

1. Review each issue deeply enough to prove current behavior and root cause.
2. Fix only easy, high-confidence bugs with narrow ownership and focused proof.
3. One commit per accepted fix, with an update note.
4. Do not batch unrelated fixes into one commit.

## Loop

For each ref:

1. Read live context — check `sv status` for service state, grep configs, check logs.
2. Check existing docs in `Zes-System/docs/` for related known behavior.
3. Read body, comments, linked refs, changed files, current code.
4. Trace the real runtime path.
5. Fix locally only if:
   - it's a real bug (not config/docs/workflow)
   - current code proves root cause
   - the implicated path is clear
   - a narrow patch is cleaner than refactor
6. Add focused verification proof.
7. Run the smallest meaningful gate.

## Service Verification

```bash
# Check service is running
sv status /data/data/com.termux/files/usr/var/service/<name>

# Check port is listening
ss -tlnp 2>/dev/null | grep <port>

# Check HTTP health (if applicable)
curl -s http://localhost:<port>/health
```

## Skip If

- not a bug (config/docs/workflow/release/support/dependency)
- repro or root cause is uncertain
- larger refactor or owner-boundary change is cleaner
- already fixed on current main
- dependency behavior is guessed
- no focused proof is feasible

## Fix Rules

- Owner module first; generic seam only when required
- Follow existing patterns/helpers
- No drive-by refactors
- Test near the failing surface
- Docs only for changed public behavior

## Output Shape

Ledger: `fixed-local`, `skipped`, `needs-human`.
Final: files changed, tests/gates output, skip reasons.
