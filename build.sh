#!/bin/zsh

ROOT="$HOME/JiJiLite"

clear

echo "===================================="
echo "      JiJi Lite Build System"
echo "===================================="
echo

echo "[1/6] Doctor..."
python3 "$ROOT/core/doctor.py" || exit 1

echo
echo "[2/6] Backup..."
"$ROOT/core/backup.sh" || exit 1

echo
echo "[3/6] Publish..."
"$ROOT/core/publish.sh" || exit 1

echo
echo "[4/6] Version..."
cat "$ROOT/version"

echo
echo "[5/6] Git Status..."
git -C "$ROOT" status --short

echo
echo "[6/6] Done."

echo
echo "===================================="
echo " JiJi Build Success"
echo "===================================="
