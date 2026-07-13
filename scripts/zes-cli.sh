#!/data/data/com.termux/files/usr/bin/bash
# ZES CLI — One-command system management
set -euo pipefail

CMD="${1:-help}"
shift 2>/dev/null || true

case "$CMD" in
  status)
    echo "📊 ZES System Status"
    echo "━━━━━━━━━━━━━━━━━━━━"
    sv status /data/data/com.termux/files/usr/var/service/* 2>/dev/null
    echo ""
    echo "🔄 Health:"
    python3 ~/Zes-System/scripts/run-evals.py 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'  {d[\"summary\"][\"pass\"]}/{d[\"summary\"][\"total\"]} passing')" 2>/dev/null || echo "  Run: zes health"
    ;;
  health)
    python3 ~/Zes-System/scripts/run-tests.py 2>&1
    ;;
  mcp)
    case "${1:-list}" in
      list)
        echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
          node ~/Zes-System/zes-chrome/zes-bridge-mcp/server.js 2>/dev/null | \
          python3 -c "import json,sys;d=json.load(sys.stdin);[print(f'  {t[\"name\"]}') for t in d.get('result',{}).get('tools',[])]" 2>/dev/null
        ;;
      *) echo "Usage: zes mcp [list]" ;;
    esac
    ;;
  backup)
    bash ~/Zes-System/backups/scripts/zes-backup.sh "${1:-snapshot}"
    ;;
  restore)
    bash ~/Zes-System/backups/scripts/zes-restore.sh
    ;;
  restart)
    sv restart "/data/data/com.termux/files/usr/var/service/${1:-dashboard8083}" 2>/dev/null || echo "Usage: zes restart <service-name>"
    ;;
  logs)
    TAIL="${2:-20}"
    if [ -n "${1:-}" ]; then
      cat "/data/data/com.termux/files/home/.svlog/$1/current" 2>/dev/null | tail -"$TAIL" || echo "No logs for: $1"
    else
      echo "Usage: zes logs <service-name> [lines]"
      echo "Services: dashboard8083, zeschrome-mcp, hermes-gateway, tor, chromium-cdp"
    fi
    ;;
  dashboard)
    echo "  http://127.0.0.1:8083/"
    ;;
  pipeline)
    node ~/Zes-System/scripts/orchestrate-pipeline.js "${@:2}"
    ;;
  scan)
    python3 ~/Zes-System/scripts/security-supply-chain-scan.py
    ;;
  kanban)
    curl -s http://127.0.0.1:8084/api/kanban/tasks | python3 -m json.tool
    ;;
  deploy)
    node ~/Zes-System/scripts/deploy-agent.js "${@:2}"
    ;;
  plugins)
    curl -s http://127.0.0.1:8083/api/plugins | python3 -m json.tool
    ;;
  start)
    bash ~/Zes-System/start.sh
    ;;
  stop)
    bash ~/Zes-System/stop.sh
    ;;
  menu)
    clear
    echo "╔═══════════════════════════════════════════════╗"
    echo "║        ZES Control Center — TUI Menu          ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "  ┌─────────────────────────────────────────────┐"
    echo "  │ 1) Status     — Show all services           │"
    echo "  │ 2) Health     — Run test suite              │"
    echo "  │ 3) Start      — Start all services          │"
    echo "  │ 4) Stop       — Stop all services           │"
    echo "  │ 5) Dashboard  — Open http://localhost:8083  │"
    echo "  │ 6) Logs       — Tail service logs           │"
    echo "  │ 7) MCP Tools  — List MCP servers            │"
    echo "  │ 8) Cron Jobs  — Show Hermes cron status     │"
    echo "  │ 9) Backup     — Snapshot configs            │"
    echo "  │ 0) Exit                                     │"
    echo "  └─────────────────────────────────────────────┘"
    echo ""
    read -p "  Select option [0-9]: " CHOICE
    case "$CHOICE" in
        1) bash "$0" status;;
        2) bash "$0" health;;
        3) bash ~/Zes-System/start.sh;;
        4) bash ~/Zes-System/stop.sh;;
        5) echo "  Opening dashboard: http://127.0.0.1:8083";;
        6) read -p "  Service name: " SVC; bash "$0" logs "$SVC";;
        7) bash "$0" mcp list;;
        8) bash ~/.codex/skills/zes-orchestrator/scripts/hermes-cron-notify.sh status;;
        9) bash "$0" backup;;
        0) echo "  Goodbye!"; exit 0;;
        *) echo "  Invalid option"; sleep 1; bash "$0" menu;;
    esac
    echo ""
    read -p "  Press Enter to return to menu..." dummy
    bash "$0" menu
    ;;

  help|*)
    echo "ZES CLI — System Management"
    echo ""
    echo "  zes status          Show all services + health"
    echo "  zes health          Run full test suite"
    echo "  zes mcp list        List MCP tools"
    echo "  zes backup          Snapshot configs"
    echo "  zes restore         Restore from last backup"
    echo "  zes restart <svc>   Restart a service"
  echo "  zes start            Start all ZES services"
  echo "  zes stop             Stop all ZES services"
    echo "  zes logs <svc>      Tail service logs"
    echo "  zes dashboard       Open dashboard URL
  zes pipeline        Run agent orchestration pipeline
  zes scan            Run security supply chain scan
  zes kanban          Show kanban task board
  zes deploy          Deploy agents to other harnesses
  zes plugins         List registered dashboard plugins"
    ;;
esac
