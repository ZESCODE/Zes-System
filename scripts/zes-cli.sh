#!/data/data/com.termux/files/usr/bin/bash
RESEARCH_ENGINE="$HOME/.local/bin/zes-research"
BATCH_ENGINE="$HOME/.local/bin/zes-batch"
CONSOLIDATE_ENGINE="$HOME/.local/bin/zes-consolidate"
DEBUG_ENGINE="$HOME/.local/bin/zes-debug"
QUALITY_ENGINE="$HOME/.local/bin/zes-quality"

case "${1:-help}" in
  research|r)
    shift
    exec python3 "$RESEARCH_ENGINE" "$@"
    ;;
  batch|b)
    shift
    exec python3 "$BATCH_ENGINE" "$@"
    ;;
  consolidate|c)
    shift
    exec python3 "$CONSOLIDATE_ENGINE" "$@"
    ;;
  debug|d)
    shift
    exec python3 "$DEBUG_ENGINE" "$@"
    ;;
  quality|q)
    shift
    exec python3 "$QUALITY_ENGINE" "$@"
    ;;
  verify|v)
    shift
    exec python3 "$HOME/.local/bin/zes-verify" "$@"
    ;;
  brainstorm|bs)
    shift
    exec python3 "$HOME/.local/bin/zes-brainstorm" "$@"
    ;;
  --check|-c|check)
    echo "=== Research Providers ==="
    python3 "$RESEARCH_ENGINE" --check
    echo ""
    echo "=== ZES CLI Toolkit v3.7 ==="
    echo "  zes research \"topic\"     Multi-agent deep research"
    echo "  zes batch tasks.txt      Batch task processing"
    echo "  zes consolidate           Memory hub consolidation"
    echo "  zes debug \"error\"        3-agent systematic debugging"
    echo "  zes quality               3-agent code quality gate"
    echo "  zes --check               Provider health"
    ;;
  *)
    echo "ZES Cloud AI Toolkit v3.7"
    echo "Usage: zes {research|batch|consolidate|debug|quality|--check}"
    echo ""
    echo "  zes research \"topic\" [options]   # Multi-agent deep research (3-7 agents)"
    echo "  zes batch tasks.txt [options]     # Batch task processing (round-robin)"
    echo "  zes consolidate [options]          # Memory hub maintenance (3 agents)"
    echo "  zes debug \"error msg\" [options]   # Systematic debugging (3 agents)"
    echo "  zes quality [options]              # Code quality gate (3 agents)"
    echo "  zes --check                       # Check providers"
    echo ""
    echo "Quality:     --dir DIR | --quick (local only) | --ci (exit 1) | --verbose"
    echo "Debug:       --dir DIR | --cdp (browser) | --verbose"
    echo "Research:    --agents N | --providers P | --output FILE | --silent"
    echo "Batch:       --inline | --concurrent N | --timeout N | --providers P"
    echo "Consolidate: --report (no changes) | --force (auto-apply)"
    echo ""
    echo "Examples:"
    echo "  zes research \"AI trends 2026\" --agents 4"
    echo "  zes batch tasks.txt --concurrent 20"
    echo "  zes debug \"TypeError: undefined\" --dir ~/project"
    echo "  zes quality --dir ~/project"
    echo "  zes quality --quick"
    echo "  zes consolidate --force"
    ;;
esac