#!/bin/zsh

ROOT="$HOME/JiJiLite"

cd "$ROOT" || exit 1

VERSION=$(cat version)

echo "===================================="
echo "      JiJi Lite Publish"
echo "===================================="
echo
echo "Version : $VERSION"
echo

git add .

if git diff --cached --quiet; then
    echo "Tidak ada perubahan."
    exit 0
fi

git commit -m "JiJi Lite v$VERSION"

echo
echo "Uploading ke GitHub..."
echo

git push origin main

echo
echo "✓ Publish selesai."
