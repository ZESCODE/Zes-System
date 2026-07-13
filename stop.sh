#!/data/data/com.termux/files/usr/bin/bash
# ZES System — Stop All Services
# Usage: ./stop.sh          (graceful stop)
#        ./stop.sh --force  (force stop)
set -euo pipefail

echo "╔════════════════════════════════════════════════╗"
echo "║     ZES System — Stopping All Services         ║"
echo "╚════════════════════════════════════════════════╝"

SVDIR="/data/data/com.termux/files/usr/var/service"

# ── Stop in reverse dependency order ──

echo ""
echo "🛑 Dev Tools:"
for svc in ttyd vscode-mobile vscode-server; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc" || true
    fi
done

echo ""
echo "🛑 ZES Services:"
for svc in zes-downloader zes-affiliate zes-9router-tunnel; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc" || true
    fi
done

echo ""
echo "🛑 Claude Code UI:"
for svc in claude-proxy claude-bridge-http claude-bridge-ws claude-ui-frontend claude-ui-backend claude-ui; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc" || true
    fi
done

echo ""
echo "🛑 Chrome MCP:"
for svc in zeschrome-mcp chromium-cdp; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc" || true
    fi
done

echo ""
echo "🛑 Hermes Gateway:"
for svc in hermes-webui hermes-gateway; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc" || true
    fi
done

echo ""
echo "🛑 Dashboard:"
for svc in dashboard8083; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc → http://127.0.0.1:8083" || true
    fi
done

echo ""
echo "🛑 Core Infrastructure:"
for svc in cloudflare-tunnel tor r9; do
    if [ -d "$SVDIR/$svc" ]; then
        $STOP_CMD "$SVDIR/$svc" 2>/dev/null && echo "  ⏹️  $svc" || true
    fi
done

# ── Cleanup background processes ──
echo ""
echo "🧹 Cleanup:"
for pidfile in /tmp/*.pid; do
    [ -f "$pidfile" ] || continue
    pid=$(cat "$pidfile" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null && echo "  🗑️  Killed $(basename "$pidfile" .pid) (PID $pid)" || true
    fi
    rm -f "$pidfile"
done

# ── Verify ──
echo ""
echo "═══════════════════════════════════════════════════"
echo "🔍 Verification:"
RUNNING=0
TOTAL=0
for d in "$SVDIR"/*/; do
    svc=$(basename "$d")
    TOTAL=$((TOTAL + 1))
    if sv status "$d" 2>/dev/null | grep -q "run:"; then
        RUNNING=$((RUNNING + 1))
        echo "  ⚠️  Still running: $svc"
    fi
done
if [ "$RUNNING" -eq 0 ]; then
    echo "  ✅ All $TOTAL services stopped"
else
    echo "  ⚠️  $RUNNING/$TOTAL services still running"
fi
echo ""
echo "✅ ZES System stopped"
