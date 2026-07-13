#!/data/data/com.termux/files/usr/bin/bash
# ZES Security Hardening Scan
set -euo pipefail

SCORE=0
TOTAL=0
WARNINGS=()

check() {
  TOTAL=$((TOTAL+1))
  if eval "$2" >/dev/null 2>&1; then
    echo "  ✅ $1"
    SCORE=$((SCORE+1))
  else
    echo "  ⚠️  $1"
    WARNINGS+=("$1: $3")
  fi
}

echo "🛡️  ZES Security Scan"
echo "━━━━━━━━━━━━━━━━━━━━\n"

# ── Port Exposure ──
echo "📡 Port Exposure:"
check "9Router :20128 filtered" "fuser 20128/tcp 2>/dev/null" "Public proxy access — verify in config"
check "Dashboard :8083 local only" "netstat -tln 2>/dev/null | grep -q '127.0.0.1:8083'" "Should be localhost-only"
check "Tor :9050 running" "fuser 9050/tcp 2>/dev/null" "Tor SOCKS5 proxy offline"

# ── Credentials ──
echo -e "\n🔑 Credential Hygiene:"
check "No .env in backups" "! grep -rl 'API_KEY\|SECRET\|PASSWORD\|token' ~/Zes-System/backups/snapshots/*/ 2>/dev/null | head -1 | grep -q ." "Secrets may be in backup snapshots"
check "No SSH keys in Zes-System" "! grep -rl 'PRIVATE KEY' ~/Zes-System/ --include='*.md' --include='*.py' --include='*.sh' --include='*.json' 2>/dev/null | head -1 | grep -q ." "Private keys committed"

# ── Permissions ──
echo -e "\n🔐 File Permissions:"
check "9router secret 600" "[ $(stat -c '%a' ~/.9router/auth/cli-secret 2>/dev/null) = '600' ]" "Permissions too open"
check "Dashboard 755" "[ -x ~/dashboard_v4.py ]" "Not executable"
check "Backup scripts 755" "[ -x ~/Zes-System/backups/scripts/zes-backup.sh ]" "Not executable"

# ── MCP Security ──
echo -e "\n🧩 MCP Security:"
check ".claude.json has access controls" "grep -q 'access' ~/.claude.json 2>/dev/null || true" "No access controls in MCP config"
check "MCP uses localhost only" "! grep -q '0.0.0.0' ~/.claude.json 2>/dev/null || true" "MCP listening on all interfaces"

# ── Tor Check ──
echo -e "\n🌐 Tor Anonymity:"
TOR_CHECK=$(curl -s --socks5 127.0.0.1:9050 --max-time 5 https://check.torproject.org/api/ip 2>/dev/null || echo "")
if echo "$TOR_CHECK" | grep -q '"IsTor":true'; then
  echo "  ✅ Tor circuit active"
  SCORE=$((SCORE+1))
else
  echo "  ⚠️  Tor circuit not verified"
  WARNINGS+=("Tor not active")
fi
TOTAL=$((TOTAL+1))

# ── Summary ──
echo -e "\n━━━━━━━━━━━━━━━━━━━━"
echo "  Score: $SCORE/$TOTAL"
echo "━━━━━━━━━━━━━━━━━━━━\n"

if [ ${#WARNINGS[@]} -gt 0 ]; then
  echo "⚠️  Warnings:"
  for w in "${WARNINGS[@]}"; do echo "  • $w"; done
fi

exit 0
