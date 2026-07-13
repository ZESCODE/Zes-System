#!/data/data/com.termux/files/usr/bin/bash
# ZES System — Start All Services
set -euo pipefail

echo "╔════════════════════════════════════════════════╗"
echo "║     ZES System — Starting All Services         ║"
echo "╚════════════════════════════════════════════════╝"

SVDIR="/data/data/com.termux/files/usr/var/service"

# ── 1. Core Infrastructure ──
echo ""
echo "📡 Core Infrastructure:"
for svc in r9 tor cloudflare-tunnel; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc" || echo "  ⚠️  $svc (check config)"
    fi
done

# ── 2. Dashboard ──
echo ""
echo "📊 Dashboard:"
for svc in dashboard8083; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc → http://127.0.0.1:8083"
    fi
done

# ── 3. Hermes Gateway ──
echo ""
echo "🔷 Hermes Gateway:"
for svc in hermes-gateway hermes-webui; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc"
    fi
done

# ── 4. Chrome MCP — Browser Automation ──
echo ""
echo "🌐 Chrome MCP:"
for svc in chromium-cdp zeschrome-mcp; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc"
    fi
done

# ── 5. Claude Code UI Layer ──
echo ""
echo "🤖 Claude Code UI:"
for svc in claude-ui claude-ui-backend claude-ui-frontend claude-bridge-ws claude-bridge-http claude-proxy; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc" || echo "  ⚠️  $svc not found"
    fi
done

# ── 6. ZES Services ──
echo ""
echo "⚡ ZES Services:"
for svc in zes-9router-tunnel zes-affiliate zes-downloader; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc"
    fi
done

# ── 7. Dev Tools ──
echo ""
echo "🛠️  Dev Tools:"
for svc in vscode-server vscode-mobile ttyd; do
    if [ -d "$SVDIR/$svc" ]; then
        sv start "$SVDIR/$svc" 2>/dev/null && echo "  ✅ $svc" || echo "  ⚠️  $svc not found"
    fi
done

# ── 8. Verify ──
echo ""
echo "═══════════════════════════════════════════════════"
echo "🔍 Verification:"
echo ""
RUNNING=0
TOTAL=0
for d in "$SVDIR"/*/; do
    svc=$(basename "$d")
    TOTAL=$((TOTAL + 1))
    if sv status "$d" 2>/dev/null | grep -q "run:"; then
        RUNNING=$((RUNNING + 1))
    fi
done
echo "  Services: $RUNNING/$TOTAL running"
echo ""

# ── Dashboard URL ──
echo "  📊 Dashboard: http://127.0.0.1:8083"
echo "  🖥️  VS Code:   http://127.0.0.1:8000"
echo "  💻 ttyd:      http://127.0.0.1:7173"
echo "  🤖 Claude UI: http://127.0.0.1:8080"
echo "  🔷 Hermes:    http://127.0.0.1:8787"
echo ""

# ── Check orchestrator scripts ──
if [ -f ~/.codex/skills/zes-orchestrator/scripts/system-health.sh ]; then
    echo "  🔧 Orchestrator skill: ✅ zes-orchestrator loaded"
fi
echo ""
echo "✅ ZES System started"
