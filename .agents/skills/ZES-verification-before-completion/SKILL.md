---
category: Review

name: ZES-verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---


# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Why This Matters

From 24 failure memories:
- your human partner said "I don't believe you" - trust broken
- Undefined functions shipped - would crash
- Missing requirements shipped - incomplete features
- Time wasted on false completion → redirect → rework
- Violates: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.

---
### Merged from ZES-verification

---
name: zes-verification
description: Verify ZES system changes before shipping — service health checks, API response validation, config integrity, and rollback readiness.
---

# ZES Verification Loop

Post-change verification for ZES services. Run after modifying dashboard code, service configs, MCP tools, or 9Router settings.

## When to Use

- After deploying dashboard changes
- After modifying service run scripts
- After adding/modifying MCP tools
- After changing 9Router provider config
- Before restarting critical services

## Verification Phases

### Phase 1: Service Status

```bash
echo "=== All Services ==="
sv status /data/data/com.termux/files/usr/var/service/* 2>&1

echo ""
echo "=== Services That Should Be Running ==="
for svc in r9 hermes-gateway codex dashboard8083 ttyd tor chromium-cdp zeschrome-mcp; do
  sv="/data/data/com.termux/files/usr/var/service/$svc"
  if [ -d "$sv" ]; then
    status=$(sv status "$sv" 2>&1)
    if echo "$status" | grep -q "run:"; then
      echo "  ✅ $svc"
    else
      echo "  ❌ $svc — DOWN!"
    fi
  fi
done
```

### Phase 2: Port Liveness

```bash
echo "=== Port Checks ==="
declare -A PORTS=(
  ["9Router"]=20128
  ["Dashboard"]=8083
  ["Codex"]=5900
  ["MCP"]=5901
  ["ttyd"]=7173
  ["Tor"]=9050
  ["Chrome CDP"]=9222
)
for name in "${!PORTS[@]}"; do
  port=${PORTS[$name]}
  if ss -tlnp 2>/dev/null | grep -q ":$port "; then
    echo "  ✅ $name on :$port"
  else
    echo "  ❌ $name on :$port — NOT LISTENING!"
  fi
done
```

### Phase 3: HTTP Health

```bash
echo "=== HTTP Health ==="
for url in \
  "http://localhost:8083/api/status" \
  "http://localhost:20128/" \
  "http://localhost:5900/"; do
  status=$(curl -so /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  if [ "$status" = "200" ] || [ "$status" = "404" ]; then
    echo "  ✅ $url → $status"
  else
    echo "  ❌ $url → $status"
  fi
done
```

### Phase 4: Config Integrity

```bash
echo "=== Config Integrity ==="
# Check critical config files exist
for cfg in \
  /data/data/com.termux/files/home/.9router/config.yaml \
  /data/data/com.termux/files/home/dashboard_v3.py \
  /data/data/com.termux/files/home/Zes-System/AGENTS.md; do
  if [ -f "$cfg" ]; then
    echo "  ✅ $(basename $cfg)"
  else
    echo "  ❌ MISSING: $cfg"
  fi
done
```

### Phase 5: Rollback Readiness

```bash
echo "=== Rollback ==="
# What was the previous dashboard version?
if [ -f /data/data/com.termux/files/home/dashboard_v2.py ]; then
  echo "  ✅ Previous dashboard version available (v2)"
fi
# Are configs backed up?
if [ -d /data/data/com.termux/files/home/.9router/backups ]; then
  echo "  ✅ 9Router configs backed up"
fi
```

## Quick Smoke Test

```bash
# Full verification in one command
echo "=== ZES Health Check ==="
echo "Services: $(sv status /data/data/com.termux/files/usr/var/service/* 2>&1 | grep -c '^run:')/$(ls -d /data/data/com.termux/files/usr/var/service/* 2>/dev/null | wc -l) running"
echo "Dashboard: $(curl -so /dev/null -w '%{http_code}' http://localhost:8083/api/status)"
echo "9Router: $(curl -so /dev/null -w '%{http_code}' http://localhost:20128/)"
echo "Uptime: $(uptime -p 2>/dev/null || uptime)"
```

## Pass/Fail Criteria

- ALL critical services running → ✅ PASS
- Dashboard API returns 200 → ✅ PASS
- 9Router responds → ✅ PASS
- Primary ports listening → ✅ PASS
- Any failure → ❌ Investigate before declaring done

**Remember**: Verify the change surface first, then do a broad health check. Don't test everything reflexively — prove your specific change works, then confirm the rest is still healthy.

---
### Merged from ZES-verify

---
name: zes-verify
description: Post-change verification for ZES — run full test suite, health evals, service checks, and rollback validation.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Verification Loop

Run after any ZES system change. Verifies all services are healthy and system is operational.

## When to Use

- After deploying changes to dashboard or agent UI
- After modifying runit service scripts
- After updating 9Router provider configs
- After changing MCP server configurations
- Before marking a task complete

## Verification Sequence

### Phase 1: Quick Health (30s)
```bash
# 1. Service status
sv status /data/data/com.termux/files/usr/var/service/* | grep -E "run:|down:" | head -20

# 2. Dashboard responds
curl -s -o /dev/null -w "Dashboard: %{http_code}
" http://localhost:8083/

# 3. Agent UI responds
curl -s -o /dev/null -w "Agent UI: %{http_code}
" http://localhost:8084/

# 4. Claude Code available
claude --version
```

### Phase 2: Full Suite (2min)
```bash
python3 ~/Zes-System/scripts/run-tests.py
python3 ~/Zes-System/scripts/run-evals.py
```

### Phase 3: Security Scan (1min)
```bash
bash ~/Zes-System/scripts/security-scan.sh
python3 ~/Zes-System/scripts/security-supply-chain-scan.py
```

## Rollback
If Phase 1 fails:
```bash
# Restore from backup
bash ~/Zes-System/backups/scripts/zes-restore.sh
# Restart all services
sv restart /data/data/com.termux/files/usr/var/service/*
```

