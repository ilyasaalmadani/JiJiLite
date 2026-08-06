#!/usr/bin/env python3

from pathlib import Path
import sys
from core.router import handle

version = (Path.home()/"JiJiLite/version").read_text().strip()

print(f"╭─ JiJi Lite v{version} ─────────────────────╮")
print("│ Status : Ready                         │")
print("╰────────────────────────────────────────╯")
print()

if len(sys.argv) > 1:
    print("Prompt :", " ".join(sys.argv[1:]))
else:
    while True:
        try:
            q = input("JiJi ❯ ")
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa.")
            break

        if q.lower() in ("exit","/exit","quit"):
            break

        handle(q)
        print()
