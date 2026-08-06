#!/usr/bin/env python3

import urllib.request
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
RELEASE_DIR = ROOT / "releases"

URL = "https://raw.githubusercontent.com/ilyasaalmadani/JiJiLite/main/install.sh"

print("====================================")
print(" Download JiJi Update")
print("====================================")
print()

RELEASE_DIR.mkdir(exist_ok=True)

try:
    print("Downloading...")

    urllib.request.urlretrieve(
        URL,
        RELEASE_DIR / "install_latest.sh"
    )

    print("✓ Download selesai.")
    print(RELEASE_DIR / "install_latest.sh")

except Exception as e:
    print("Download gagal.")
    print(e)
