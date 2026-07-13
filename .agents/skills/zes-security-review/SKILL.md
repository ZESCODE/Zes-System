---
name: zes-security-review
description: Security review for ZES infrastructure — API keys, port exposure, secrets, Cloudflare tunnel, 9Router, MCP tools.
metadata:
  origin: ZES
  adapted_from: ECC
  version: 1.0
---

# ZES Security Review

Security audit for ZES system. Checks secrets management, network exposure, authentication, and dependency safety.

## When to Activate

- Weekly security audit
- After adding new services or exposing ports
- After changing 9Router provider configs
- After modifying Cloudflare tunnel settings
- When rotating API keys

## Audit Checklist

### 1. Secrets Detection
- [ ] Check `~/.9router/` for restricted permissions
- [ ] Verify `dashboard_v4.py` has no hardcoded keys
- [ ] Check agent-server.js for embedded tokens
- [ ] Review shell scripts for credential parameters
- [ ] Run: `grep -rn "sk-[a-zA-Z0-9]\{20,\}" ~/Zes-System/ --include="*.py" --include="*.js" --include="*.sh"`

### 2. Network Exposure
- [ ] All services bind to 127.0.0.1 (not 0.0.0.0)
- [ ] Cloudflare tunnel only exposes intended services
- [ ] Tor SOCKS5 is properly restricted (9050 localhost only)
- [ ] No unexpected ports in `ss -tlnp`

### 3. Dependency Scan
```bash
python3 ~/Zes-System/scripts/security-supply-chain-scan.py
bash ~/Zes-System/scripts/security-scan.sh
```

### 4. Remediation
- Any found secrets: rotate immediately, check git history
- Open ports: close or restrict with iptables
- Outdated packages: update via pip/npm

