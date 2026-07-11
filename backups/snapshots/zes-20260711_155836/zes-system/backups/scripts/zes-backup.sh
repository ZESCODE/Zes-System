#!/data/data/com.termux/files/usr/bin/bash
# ZES Backup & Recovery System
set -euo pipefail

BACKUP_DIR="$HOME/Zes-System/backups/snapshots"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_DIR="$BACKUP_DIR/zes-$TIMESTAMP"
LOG="$BACKUP_DIR/backup.log"
mkdir -p "$BACKUP_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# Files to backup (full paths)
CONFIGS=(
  "$HOME/.9router/machine-id"
  "$HOME/.9router/auth/cli-secret"
  "$HOME/.9router/config.yaml"
  "$HOME/.claude.json"
  "$HOME/.hermes/config.yaml"
  "$HOME/.hermes/ecc-config.yaml"
  "$HOME/dashboard_v4.py"
  "$HOME/dashboard_v3.py"
  "$HOME/.codex/AGENTS.md"
)

SERVICES=(
  zeschrome-mcp dashboard8083 hermes-gateway chromium-cdp tor ttyd vscode-server
)

snapshot() {
  mkdir -p "$SNAPSHOT_DIR"
  log "📸 Snapshot: $TIMESTAMP"

  for full in "${CONFIGS[@]}"; do
    if [ -f "$full" ] || [ -d "$full" ]; then
      sub="${full#$HOME/}"
      dest="$SNAPSHOT_DIR/.${sub#.}"
      mkdir -p "$(dirname "$dest")"
      cp -r "$full" "$dest" 2>/dev/null && log "  ✅ ${sub:0:40}" || log "  ⚠️  ${sub:0:40}"
    else
      log "  ⬜ ${full#$HOME/} (not found)"
    fi
  done

  # Archive Zes-System tracked files
  if [ -d "$HOME/Zes-System/.git" ]; then
    mkdir -p "$SNAPSHOT_DIR/zes-system"
    cd "$HOME/Zes-System"
    git ls-files | tar -T - -cf - | tar -C "$SNAPSHOT_DIR/zes-system" -xf - 2>/dev/null || true
    log "  ✅ Zes-System ($(git ls-files | wc -l) files)"
  fi

  # Service status snapshot
  for svc in "${SERVICES[@]}"; do
    sv status "/data/data/com.termux/files/usr/var/service/$svc" 2>/dev/null | head -1 >> "$SNAPSHOT_DIR/service-status.txt" || true
  done
  log "  ✅ Service status"

  count=$(find "$SNAPSHOT_DIR" -type f 2>/dev/null | wc -l)
  size=$(du -sh "$SNAPSHOT_DIR" 2>/dev/null | cut -f1)
  log "✅ Done: $count files, $size"

  # Auto-commit to Zes-System git
  cd "$HOME/Zes-System"
  git add backups/ 2>/dev/null || true
  git diff --cached --quiet || git commit -m "backup: snapshot $TIMESTAMP" --no-gpg-sign 2>/dev/null || true
}

list_snapshots() {
  echo "📋 Snapshots:"
  for d in "$BACKUP_DIR"/zes-*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    c=$(find "$d" -type f 2>/dev/null | wc -l)
    s=$(du -sh "$d" 2>/dev/null | cut -f1)
    echo "  $n  ($c files, $s)"
  done | sort -r
}

restore() {
  local SRC="${1:-$BACKUP_DIR/$(ls -1d "$BACKUP_DIR"/zes-* 2>/dev/null | tail -1)}"
  [ -d "$SRC" ] || { echo "❌ Snapshot not found"; exit 1; }
  log "🔄 Restoring: $SRC"

  # Restore known configs from snapshot structure
  for f in "$SRC"/.9router/* "$SRC"/.claude.json "$SRC"/.hermes/* "$SRC"/dashboard_v4.py "$SRC"/dashboard_v3.py "$SRC"/.codex/*; do
    [ -f "$f" ] || continue
    target="$HOME/${f#$SRC/}"
    target="${target/#.9router/.9router}"
    target="${target/#.claude.json/.claude.json}"
    target="${target/#.hermes/.hermes}"
    target="${target/#.codex/.codex}"
    cp -r "$f" "$target" 2>/dev/null && log "  ✅ ${f#$SRC/}"
  done

  log "✅ Restore complete. Restart services: sv restart dashboard8083 hermes-gateway"
}

case "${1:-snapshot}" in
  snapshot) snapshot ;;
  list) list_snapshots ;;
  restore) restore "$2" ;;
  *) echo "Usage: zes-backup.sh [snapshot|list|restore]" ;;
esac
