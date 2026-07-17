#!/data/data/com.termux/files/usr/bin/bash
# ═══════════════════════════════════════════
#  ZES Architecture Review Gate
#  Checks that implementation matches architecture
#  Runs pacts and validates phase gates
# ═══════════════════════════════════════════

set -e
ARCH_FILE="${1:-$HOME/Zes-System/docs/architecture.json}"
PHASE="${2:-1}"

echo "╔═══════════════════════════════════════════╗"
echo "║   ZES Architecture Review Gate            ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# 1. Check architecture doc exists
if [ ! -f "$ARCH_FILE" ]; then
  echo "❌ Architecture doc not found: $ARCH_FILE"
  echo "   Run: python3 ~/Zes-System/scripts/zes-reverse-arch.py --markdown"
  exit 1
fi
echo "✅ Architecture doc: $ARCH_FILE"

# 2. Run pact gate check
echo ""
echo "─── Phase $PHASE Gate Check ───"
python3 ~/Zes-System/scripts/zes-pact.py gate --phase "$PHASE" || true

# 3. Check services match architecture
echo ""
echo "─── Service Validation ───"
RUNNING=$(sv status /data/data/com.termux/files/usr/var/service/* 2>/dev/null | grep -c "^run:" || echo 0)
echo "  Running services: $RUNNING"
echo "  Expected: 27"

# 4. Check key endpoints
echo ""
echo "─── Endpoint Health ───"
for ep in "9Router:20128" "Dashboard:8083" "Agent:8084" "Hermes:8787" "Teams:8788"; do
  name="${ep%%:*}"
  port="${ep##*:}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://127.0.0.1:$port/" 2>/dev/null || echo "down")
  if [ "$code" != "down" ] && [ "$code" != "000" ]; then
    echo "  ✅ $name :$port ($code)"
  else
    echo "  ❌ $name :$port (down)"
  fi
done

# 5. Generate updated architecture
echo ""
echo "─── Generating Updated Architecture ───"
python3 ~/Zes-System/scripts/zes-reverse-arch.py 2>&1 | tail -5

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║   Review Complete                         ║"
echo "╚═══════════════════════════════════════════╝"
