#!/bin/zsh

ROOT="$HOME/JiJiLite"
BACKUP_DIR="$ROOT/backups"

echo "===================================="
echo "      JiJi Lite Restore"
echo "===================================="
echo

LATEST=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -n 1)

if [ -z "$LATEST" ]; then
    echo "Tidak ada backup."
    exit 1
fi

echo "Backup terbaru:"
echo "$LATEST"
echo

read "?Restore backup ini? (y/N): " ANS

if [[ "$ANS" != "y" && "$ANS" != "Y" ]]; then
    echo "Dibatalkan."
    exit 0
fi

mkdir -p "$ROOT.restore.tmp"

tar -xzf "$LATEST" -C "$ROOT.restore.tmp"

echo
echo "✓ Backup berhasil diekstrak ke:"
echo "$ROOT.restore.tmp"
echo
echo "Mode restore aman (preview)."
echo "Belum menimpa file JiJi Lite."
