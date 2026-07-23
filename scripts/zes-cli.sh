#!/data/data/com.termux/files/usr/bin/bash
RESEARCH_ENGINE="$HOME/.local/bin/zes-research"
case "${1:-help}" in
  research|r)
    shift
    exec python3 "$RESEARCH_ENGINE" "$@"
    ;;
  --check|-c|check)
    exec python3 "$RESEARCH_ENGINE" --check
    ;;
  *)
    echo "ZES Parallel Research Engine"
    echo "Usage:"
    echo "  zes research \"topic\" [--agents N] [--output FILE] [--silent]"
    echo "  zes research --check"
    echo ""
    echo "Examples:"
    echo "  zes research \"DeepSeek vs GPT-5.5\" --agents 4"
    echo "  zes research --check"
    ;;
esac
