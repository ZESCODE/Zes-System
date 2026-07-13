#!/bin/bash
# ZES Downloader Daemon - Start script
# Usage: ./start-downloader.sh [--once|--serve-only]

set -e
cd "$(dirname "$0")"

WORKER_URL="${WORKER_URL:-https://api.zes.codes}"
DL_PORT="${DL_PORT:-9090}"
DL_DIR="${DL_DIR:-$(pwd)/downloads}"

mkdir -p "$DL_DIR"

echo "=== ZES Downloader Daemon v3 ==="
echo "Worker: $WORKER_URL"
echo "Store:  $DL_DIR"
echo "Port:   $DL_PORT"

case "$1" in
  --once)
    echo "Mode: One-shot"
    python3 srccode/downloader-daemon.py --once
    ;;
  --serve-only)
    echo "Mode: HTTP server only"
    python3 srccode/downloader-daemon.py --serve-only
    ;;
  *)
    echo "Mode: Daemon (background)"
    nohup python3 srccode/downloader-daemon.py > /tmp/zes-downloader.log 2>&1 &
    PID=$!
    echo "$PID" > /tmp/zes-downloader.pid
    echo "Started PID: $PID"
    echo "Log: tail -f /tmp/zes-downloader.log"
    echo "Stop: kill $PID"
    ;;
esac
