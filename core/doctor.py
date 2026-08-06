#!/usr/bin/env python3

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path.home() / "JiJiLite"

checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

check("Python", shutil.which("python3"))
check("Ollama", shutil.which("ollama"))
check("Git", shutil.which("git"))
check("Version", (ROOT / "version").exists())
check("Main", (ROOT / "main.py").exists())
check("Router", (ROOT / "core/router.py").exists())
check("Chat", (ROOT / "core/chat.py").exists())
check("Web", (ROOT / "core/web.py").exists())
check("Memory", (ROOT / "core/memory.py").exists())
check("Source Quality", (ROOT / "core/source_quality.py").exists())
check("Quality Test", (ROOT / "core/quality_test.py").exists())
check(
    "Tavily Config",
    (ROOT / "config/tavily.conf").exists(),
)

try:
    result = subprocess.run(
        ["ollama", "list"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    check("Ollama Service", result.returncode == 0)
except OSError:
    check("Ollama Service", False)

try:
    session = ROOT / "memory/session.json"
    if session.exists():
        json.loads(session.read_text(encoding="utf-8"))
    check("Memory Database", True)
except (json.JSONDecodeError, OSError):
    check("Memory Database", False)

print("╭─ JiJi Lite System Doctor ──────────────╮")
for name, status in checks:
    symbol = "✓" if status else "✗"
    print(f"│ {symbol} {name:<35}│")
print("╰────────────────────────────────────────╯")

failed = [name for name, status in checks if not status]

if failed:
    print()
    print("System membutuhkan perhatian:")
    for item in failed:
        print("-", item)
    raise SystemExit(1)

print()
print("✓ System Healthy")
