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
