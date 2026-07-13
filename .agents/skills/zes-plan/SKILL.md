---
name: zes-plan
description: Implementation planning for ZES system — assess impact, risks, and write step-by-step plans before touching code.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Planning

Systematic implementation planning for ZES infrastructure changes.

## When to Activate

- Before implementing new features
- Before refactoring services
- Before changing service architecture
- Before adding new integrations

## Planning Process

### 1. Requirements Restatement
Restate the request in ZES system context. Identify which services, ports, and configs are affected.

### 2. Risk Assessment
- **Service disruption risk**: Will this restart/change affect running services?
- **Security risk**: Does this expose new ports or require new credentials?
- **Data loss risk**: Does this modify backup/state files?
- **Rollback plan**: How to revert if something goes wrong?

### 3. Step-by-Step Plan
```
Phase 1: Preparation (backup configs, notify if needed)
Phase 2: Implementation (specific files to change)
Phase 3: Verification (run evals, check services)
Phase 4: Documentation (update AGENTS.md, README)
```

### 4. Approval Gate
Present plan to user for confirmation before executing.

