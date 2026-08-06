#!/usr/bin/env python3

import shutil
import subprocess
from pathlib import Path

ROOT = Path.home() / "JiJiLite"

print("====================================")
print("      JiJi Lite System Doctor")
print("====================================")

checks = []

checks.append(("Python", shutil.which("python3") is not None))
checks.append(("Ollama", shutil.which("ollama") is not None))
checks.append(("Git", shutil.which("git") is not None))

checks.append(("Version", (ROOT / "version").exists()))
checks.append(("Router", (ROOT / "core/router.py").exists()))
checks.append(("Chat", (ROOT / "core/chat.py").exists()))
checks.append(("Web", (ROOT / "core/web.py").exists()))

try:
    subprocess.run(
        ["ollama", "list"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    checks.append(("Ollama Service", True))
except:
    checks.append(("Ollama Service", False))

print()

for name, ok in checks:
    print(f"{'✓' if ok else '✗'} {name}")

print()
print("Doctor selesai.")
