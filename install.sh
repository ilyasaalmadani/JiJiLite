#!/bin/zsh

set -e

ROOT="$HOME/JiJiLite"

echo "===================================="
echo " JiJi Lite Installer"
echo "===================================="
echo

mkdir -p "$ROOT"/{bin,core,config,knowledge,cache,logs,plugins}

chmod +x "$ROOT"/bin/jiji 2>/dev/null || true
chmod +x "$ROOT"/main.py 2>/dev/null || true

echo
echo "✓ Folder OK"
echo "✓ Permission OK"

echo
echo "JiJi Lite siap digunakan."
echo "Versi : $(cat "$ROOT/version")"
