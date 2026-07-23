#!/data/data/com.termux/files/usr/bin/bash
RESEARCH_ENGINE="$HOME/.local/bin/zes-research"
BATCH_ENGINE="$HOME/.local/bin/zes-batch"

case "${1:-help}" in
  research|r)
    shift
    exec python3 "$RESEARCH_ENGINE" "$@"
    ;;
  batch|b)
    shift
    exec python3 "$BATCH_ENGINE" "$@"
    ;;
  --check|-c|check)
    echo "=== Research Providers ==="
    python3 "$RESEARCH_ENGINE" --check
    echo ""
    echo "=== Batch ==="
    echo "  zes batch tasks.txt          # Process file"
    echo "  zes batch --inline \"task\"    # Single task"
    echo "  zes batch --providers groq bitrouter_gpt"
    ;;
  *)
    echo "ZES Cloud AI Toolkit"
    echo "Usage:"
    echo "  zes research \"topic\" [options]   # Multi-agent deep research"
    echo "  zes batch tasks.txt [options]     # Batch task processing"
    echo "  zes --check                       # Check providers"
    echo ""
    echo "Research options:"
    echo "  --agents N      Number of parallel agents (1-6)"
    echo "  --providers P   Specific providers"
    echo "  --output FILE   Save report"
    echo "  --silent        Minimal output"
    echo ""
    echo "Batch options:"
    echo "  --inline \"task\"   Single task"
    echo "  --concurrent N    Tasks per batch (default: 10)"
    echo "  --timeout N       Per-task timeout (default: 30)"
    echo "  --providers P     Specific providers"
    echo "  --output DIR      Results directory"
    echo ""
    echo "Examples:"
    echo "  zes research \"AI trends 2026\" --agents 4"
    echo "  zes batch tasks.txt --concurrent 20"
    echo "  zes batch --inline \"Write a Python script for X\""
    ;;
esac
