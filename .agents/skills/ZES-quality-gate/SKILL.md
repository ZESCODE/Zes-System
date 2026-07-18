---
category: Review

name: ZES-quality-gate
description: Quality enforcement — delivery-gate and gateguard combined. Blocks completion until quality checks pass, detects rationalization patterns, and demands concrete investigation before edits.
metadata:
  origin: ZES
  version: 1.0.0
---


# ZES Quality Gate

Combines delivery-gate + gateguard for unified quality enforcement.

## Before Completion
1. Run all tests: `PYTHONPATH=. python3 -m unittest discover plugins/memory/zes_memory/`
2. Verify no rationalization patterns (surface text heuristics)
3. Check learning logs freshness (filesystem mtime)
4. Verify disk space

## Before Edits/Write
1. Verify data schemas and importers
2. Confirm user instruction alignment
3. No hardcoded secrets
4. All inputs validated

## Quality Metrics
- Test coverage: 80%+ required
- No security vulnerabilities
- No broken service connections
- Memory consistency across all stores

---
### Merged from zes-quality-gate

---
name: zes-quality-gate
description: Quality gate for ZES changes — check test coverage, security posture, service health, and documentation completeness.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Quality Gate

Quality gate checklist for ZES system changes. Ensures every deploy meets minimum quality standards.

## When to Activate

- Before merging any PR to ZES-System
- Before deploying dashboard or agent UI changes
- At the end of each development session
- Weekly system health review

## Quality Gates

### Gate 1: Tests Pass
- [ ] `python3 ~/Zes-System/scripts/run-tests.py` — all passing
- [ ] `python3 ~/Zes-System/scripts/run-evals.py` — all passing

### Gate 2: All Core Services Running
- [ ] Dashboard :8083 — HTTP 200
- [ ] Agent UI :8084 — HTTP 200
- [ ] 9Router :20128 — providers API responds
- [ ] Claude Code — version available
- [ ] zeschrome MCP :5901 — port open
- [ ] ttyd :7173 — terminal accessible
- [ ] Tor :9050 — SOCKS proxy up

### Gate 3: Security Hardening
- [ ] `security-scan.sh` — no critical findings
- [ ] `security-supply-chain-scan.py` — no vulnerable dependencies
- [ ] No hardcoded secrets in changed files

### Gate 4: Documentation
- [ ] AGENTS.md updated if architecture changed
- [ ] README.md updated if services/ports changed
- [ ] Service changes documented in docs/services/

### Gate 5: Backup
- [ ] Recent backup exists: `ls -la ~/Zes-System/backups/snapshots/`
- [ ] Config files committed or backed up

