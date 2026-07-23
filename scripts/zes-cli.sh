#!/data/data/com.termux/files/usr/bin/bash
RESEARCH_ENGINE="$HOME/.local/bin/zes-research"
BATCH_ENGINE="$HOME/.local/bin/zes-batch"
CONSOLIDATE_ENGINE="$HOME/.local/bin/zes-consolidate"
DEBUG_ENGINE="$HOME/.local/bin/zes-debug"
QUALITY_ENGINE="$HOME/.local/bin/zes-quality"
VERIFY_ENGINE="$HOME/.local/bin/zes-verify"
BRAINSTORM_ENGINE="$HOME/.local/bin/zes-brainstorm"
DESIGN_ENGINE="$HOME/.local/bin/zes-design"
INTEGRATE_ENGINE="$HOME/.local/bin/zes-integrate"
COST_ENGINE="$HOME/.local/bin/zes-cost"
USAGE_LOG="$HOME/.zes/usage.log"

# Log usage for cost tracking
cmd="${1:-help}"
ts=$(date '+%Y-%m-%d %H:%M:%S')
mkdir -p "$HOME/.zes"
echo "$ts|$cmd|$*" >> "$USAGE_LOG" 2>/dev/null

case "${cmd}" in
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
    exec python3 "$VERIFY_ENGINE" "$@"
    ;;
  brainstorm|bs)
    shift
    exec python3 "$BRAINSTORM_ENGINE" "$@"
    ;;
  design|dr)
    shift
    exec python3 "$DESIGN_ENGINE" "$@"
    ;;
  integrate|it)
    shift
    exec python3 "$INTEGRATE_ENGINE" "$@"
    ;;
  cost|ct)
    shift
    exec python3 "$COST_ENGINE" "$@"
    ;;
  --check|-c|check)
    echo "=== Research Providers ==="
    python3 "$RESEARCH_ENGINE" --check
    echo ""
    echo "=== ZES CLI Toolkit v4.0 ==="
    echo "  zes research \"topic\"    Multi-agent deep research"
    echo "  zes batch tasks.txt     Batch task processing"
    echo "  zes consolidate          Memory hub consolidation"
    echo "  zes debug \"error\"       3-agent systematic debugging"
    echo "  zes quality              3-agent code quality gate"
    echo "  zes verify               3-agent verification"
    echo "  zes brainstorm \"topic\"  3-agent divergent thinking"
    echo "  zes design               3-agent design review"
    echo "  zes integrate            3-agent integration check"
    echo "  zes cost                 3-agent cost analysis"
    echo "  zes --check              Provider health"
    echo ""
    echo "Usage: zes {research|batch|consolidate|debug|quality|verify|brainstorm|design|integrate|cost|--check}"
    ;;
  *)
    echo "ZES Cloud AI Toolkit v4.0"
    echo "Usage: zes {command} [options]"
    echo ""
    echo "  zes research \"topic\"      Multi-agent deep research (3-7 agents)"
    echo "  zes batch tasks.txt       Batch task processing (round-robin)"
    echo "  zes consolidate           Memory hub maintenance (3 agents)"
    echo "  zes debug \"error\"         Systematic debugging (3 agents)"
    echo "  zes quality               Code quality gate (3 agents)"
    echo "  zes verify                Verification before completion (3 agents)"
    echo "  zes brainstorm \"idea\"    Divergent brainstorming (3 agents)"
    echo "  zes design                Design review + threat modeling (3 agents)"
    echo "  zes integrate             Integration verification (3 agents)"
    echo "  zes cost                  Cost analysis + forecasting (3 agents)"
    echo "  zes --check               Provider health"
    echo ""
    echo "Options: --dir DIR | --quick | --ci | --verbose | --plan FILE | --output DIR"
    echo "Run 'zes <command>' for specific help."
    ;;
esac