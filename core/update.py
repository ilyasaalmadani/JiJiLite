#!/usr/bin/env python3

import urllib.request
from pathlib import Path

ROOT = Path.home() / "JiJiLite"

LOCAL = (ROOT / "version").read_text().strip()

URL = "https://raw.githubusercontent.com/ilyasaalmadani/JiJiLite/main/version"

print("====================================")
print("      JiJi Lite Updater")
print("====================================")
print()

print("Current :", LOCAL)

try:
    REMOTE = urllib.request.urlopen(URL, timeout=10).read().decode().strip()
    print("Latest  :", REMOTE)

    if LOCAL == REMOTE:
        print()
        print("✓ JiJi Lite sudah versi terbaru.")
    else:
        print()
        print("↑ Update tersedia.")
except Exception as e:
    print()
    print("Tidak dapat mengecek update.")
    print(e)
