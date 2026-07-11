#!/data/data/com.termux/files/usr/bin/bash
# ZES Quick Restore — one-command restore from last snapshot
set -euo pipefail

BACKUP_DIR="$HOME/Zes-System/backups/snapshots"
LATEST=$(ls -1d "$BACKUP_DIR"/zes-* 2>/dev/null | tail -1)

if [ -z "$LATEST" ]; then
  echo "❌ No snapshots found"
  exit 1
fi

echo "🔄 ZES Quick Restore"
echo "   From: $LATEST"
echo ""
read -p "   Restore all configs from this snapshot? (y/N) " confirm
[ "$confirm" != "y" ] && [ "$confirm" != "Y" ] && { echo "Cancelled"; exit 0; }

bash "$HOME/Zes-System/backups/scripts/zes-backup.sh" restore "$LATEST"

echo ""
echo "✅ Restore complete. Consider restarting services:"
echo "   sv restart dashboard8083 hermes-gateway"
