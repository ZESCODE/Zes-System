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

