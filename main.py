#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
sys.path.insert(0, str(ROOT))

from core.memory import clear, load
from core.router import handle

VERSION = (ROOT / "version").read_text().strip()

def show_help():
    print("Perintah:")
    print("/help     Bantuan")
    print("/new      Mulai percakapan baru")
    print("/memory   Lihat konteks aktif")
    print("/status   Status sistem")
    print("/version  Versi JiJi")
    print("/doctor   Diagnostik")
    print("/clear    Bersihkan layar")
    print("/exit     Keluar")

def internal(command):
    cmd = command.strip().lower()

    if cmd == "/help":
        show_help()
    elif cmd == "/new":
        clear()
        print("Percakapan baru dimulai.")
    elif cmd == "/memory":
        session = load()
        print("Topik :", session.get("last_query") or "Belum ada")
        print("Mode  :", session.get("last_mode") or "-")
    elif cmd == "/status":
        print(f"JiJi Lite v{VERSION}")
        print("Chat   : gemma3:4b")
        print("Web    : Tavily")
        print("Memory : Active")
        print("Router : Reliability Layer")
    elif cmd == "/version":
        print(f"JiJi Lite v{VERSION}")
    elif cmd == "/doctor":
        subprocess.run(["python3", str(ROOT / "core" / "doctor.py")])
    elif cmd == "/clear":
        print("\033c", end="")
    else:
        return False
    return True

def process(prompt):
    if prompt.startswith("/") and internal(prompt):
        return
    handle(prompt)

if len(sys.argv) > 1:
    process(" ".join(sys.argv[1:]))
    raise SystemExit

print(f"╭─ JiJi Lite v{VERSION} ─────────────────────╮")
print("│ Status : Ready                            │")
print("╰───────────────────────────────────────────╯")
print()
print("Apa yang ingin Anda lakukan?")
print()

while True:
    try:
        question = input("JiJi ❯ ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSampai jumpa.")
        break

    if not question:
        continue
    if question.lower() in ("/exit", "exit", "quit", "keluar"):
        print("Sampai jumpa.")
        break

    process(question)
    print()
