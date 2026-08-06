#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
sys.path.insert(0, str(ROOT))

from core.config import CONFIG
from core.memory import clear, load
from core.router import handle

VERSION = (ROOT / "version").read_text().strip()
PURPLE = "\033[35m"
CYAN = "\033[36m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"

def show_welcome():
    model = CONFIG.get("chat_model", "gemma3:4b")
    tavily = (
        "ONLINE"
        if (ROOT / "config/tavily.conf").exists()
        else "OFFLINE"
    )

    print(PURPLE + r"""
             /\_/\
            ( •.• )        /^\/^\
             > ^ <        _|__|  •|
                          /     \_/ 
         JiJi Rabbit × Snake Intelligence
""" + RESET)

    print(PURPLE + f"╭─ JiJi Lite v{VERSION} ─────────────────────────╮" + RESET)
    print(f"│ {GREEN}● Status{RESET}  : READY                            │")
    print(f"│ {CYAN}◆ Mode{RESET}    : ACCURACY                         │")
    print(f"│ ◆ Router  : LOCAL • WEB • VERIFY              │")
    print(f"│ ◆ Memory  : ACTIVE                            │")
    print(f"│ ◆ Web     : {tavily:<33}│")
    print(f"│ ◆ Model   : {model:<33}│")
    print(PURPLE + "╰───────────────────────────────────────────────╯" + RESET)
    print()
    print(DIM + "Ketik /help untuk melihat perintah." + RESET)
    print()

def show_help():
    print("Perintah JiJi:")
    print("/help      Tampilkan bantuan")
    print("/new       Mulai percakapan baru")
    print("/memory    Lihat konteks aktif")
    print("/status    Lihat status sistem")
    print("/version   Lihat versi")
    print("/doctor    Jalankan pemeriksaan")
    print("/clear     Bersihkan layar")
    print("/exit      Keluar")

def run_internal(command):
    cmd = command.strip().lower()

    if cmd in ("/help", "help"):
        show_help()

    elif cmd == "/new":
        clear()
        print("✓ Percakapan baru dimulai.")

    elif cmd == "/memory":
        session = load()
        print("Topik :", session.get("last_user_query") or "Belum ada")
        print("Mode  :", session.get("last_mode") or "-")
        print("Pesan :", len(session.get("history", [])))

    elif cmd == "/status":
        print(f"JiJi Lite v{VERSION}")
        print("Status : READY")
        print("Mode   : ACCURACY")
        print("Router : LOCAL • WEB • VERIFY")
        print("Memory : ACTIVE")
        print("Web    : Tavily")
        print("Model  :", CONFIG.get("chat_model", "gemma3:4b"))

    elif cmd == "/version":
        print(f"JiJi Lite v{VERSION}")

    elif cmd == "/doctor":
        subprocess.run([
            "python3",
            str(ROOT / "core" / "doctor.py"),
        ])

    elif cmd == "/clear":
        print("\033c", end="")
        show_welcome()

    else:
        return False

    return True

def process(prompt):
    if run_internal(prompt):
        return
    handle(prompt)

if len(sys.argv) > 1:
    process(" ".join(sys.argv[1:]))
    raise SystemExit

show_welcome()

while True:
    try:
        question = input(PURPLE + "JiJi ❯ " + RESET).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSampai jumpa.")
        break

    if not question:
        continue

    if question.lower() in (
        "/exit", "exit", "quit", "keluar"
    ):
        print("Sampai jumpa.")
        break

    process(question)
    print()
