#!/bin/zsh

ROOT="$HOME/JiJiLite"
BACKUP_DIR="$HOME/JiJiLite/backups"

mkdir -p "$BACKUP_DIR"

STAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILE="$BACKUP_DIR/jiji-$STAMP.tar.gz"

echo "===================================="
echo " JiJi Lite Backup"
echo "===================================="
echo

cd "$ROOT" || exit 1

tar \
  --exclude="./backups" \
  --exclude="./cache" \
  --exclude="./logs" \
  -czf "$BACKUP_FILE" .

echo "✓ Backup selesai"
echo
echo "$BACKUP_FILE"
