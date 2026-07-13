---
name: zes-agent-debugging
description: Structured self-debugging for Claude Code and Codex when failing, looping, or drifting during ZES work.
---

# ZES Agent Introspection Debugging

Use when an agent run is failing repeatedly, consuming tokens without progress, looping on the same tools, or drifting from the intended task.

## When to Activate

- Maximum tool call / loop-limit failures
- Repeated retries with no forward progress
- Context growth or prompt drift degrading output quality
- File-system or environment state mismatch
- Tool failures that are likely recoverable

## Four-Phase Debug Loop

### Phase 1: Capture the Failure

Before retrying, record exactly what failed:

```bash
# 1. What was the last command?
# 2. What was the error/output?
# 3. What state is the system in now?
sv status /data/data/com.termux/files/usr/var/service/* 2>&1
```

Capture:
- Error type, message, and traceback
- Which tool/command was being used
- What input was provided
- What output was expected vs received

### Phase 2: Diagnose the Pattern

Common ZES agent failure patterns:

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `sv status` says "down" | Service not running | `sv start <name>` or check run script |
| `curl` timeout | Service on wrong port | Check port_map values |
| File not found | Wrong path | Use `PREFIX` not hardcoded paths |
| Permission denied | Termux file perms | Use `~` not `/data/data/...` |
| JSON parse error | API returned HTML/error | Check response body first |
| Dependency missing | Node/Python module | Check `pkg list-installed` |

### Phase 3: Apply Contained Recovery

```bash
# 1. Fix the immediate issue
sv restart <failed-service>

# 2. Verify the fix
curl -s http://localhost:<port>/health | head -5

# 3. Wait for stability
sleep 2 && sv status <service>
```

### Phase 4: Produce a Debug Report

Summarize for the user:

```
## Debug Report
- **Symptom**: [what went wrong]
- **Root cause**: [why it happened]
- **Fix applied**: [what was changed]
- **Verification**: [proof it's working]
- **Prevention**: [how to avoid next time]
```

## Prevention Checklist

Before starting a ZES task:

- [ ] Check which services need to be running
- [ ] Verify the working directory exists
- [ ] Check file permissions
- [ ] Confirm expected ports are free/listening
- [ ] Read relevant AGENTS.md or docs first

**Remember**: The goal is to fix the root cause, not work around it. If you've tried 3+ fixes without success, stop and reassess the approach.
