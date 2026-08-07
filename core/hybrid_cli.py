#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

from core.cloud import ask_cloud


ROOT = Path.home() / "JiJiLite"
STATE_FILE = ROOT / "config" / "hybrid.json"

PURPLE = "\033[35m"
GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"

FAILURE_MARKERS = (
    "belum cukup yakin",
    "mohon jelaskan sedikit lebih spesifik",
    "web search gagal",
    "ollama gagal",
    "model lokal gagal",
    "web_search_needed",
)


def load_mode() -> str:
    try:
        data = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
        mode = str(data.get("mode", "auto")).lower()

        if mode in {"local", "cloud", "auto"}:
            return mode

    except (OSError, json.JSONDecodeError):
        pass

    return "auto"


def save_mode(mode: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    STATE_FILE.write_text(
        json.dumps(
            {"mode": mode},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def ask_local(prompt: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["jiji", prompt],
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        return False, "JiJi lokal melewati batas waktu."

    output = (result.stdout or "").strip()

    if result.returncode != 0:
        error = (result.stderr or "").strip()
        return False, error or "JiJi lokal gagal."

    if not output:
        return False, "JiJi lokal menghasilkan jawaban kosong."

    lowered = output.lower()

    if any(marker in lowered for marker in FAILURE_MARKERS):
        return False, output

    return True, output


def answer(prompt: str, mode: str) -> None:
    if mode == "local":
        success, output = ask_local(prompt)

        print("\n🖥️ JiJi Local\n")
        print(output)

        if not success:
            print("\nLocal belum berhasil.")
        return

    if mode == "cloud":
        print("\n☁️ JiJi Cloud\n")
        print(ask_cloud(prompt))
        return

    success, output = ask_local(prompt)

    if success:
        print("\n🖥️ JiJi Local · AUTO\n")
        print(output)
        return

    print("\n☁️ Beralih ke Gemini Cloud...\n")

    try:
        print(ask_cloud(prompt))
    except Exception as error:
        print("Local dan cloud sama-sama gagal.")
        print("Local:", output)
        print("Cloud:", error)


def show_welcome(mode: str) -> None:
    print(PURPLE + r"""
          /\_/\
         ( •.• )     JiJi Hybrid
          > ^ <      Local × Cloud
""" + RESET)

    print(PURPLE + "╭──────────────────────────────────────╮" + RESET)
    print(f"│ Status : {GREEN}READY{RESET}                        │")
    print(f"│ Mode   : {CYAN}{mode.upper():<28}{RESET}│")
    print("│ Local  : Ollama / JiJi              │")
    print("│ Cloud  : Google Gemini              │")
    print(PURPLE + "╰──────────────────────────────────────╯" + RESET)
    print()
    print("/mode local | /mode cloud | /mode auto")
    print("/status | /exit")
    print()


def main() -> None:
    mode = load_mode()
    show_welcome(mode)

    while True:
        try:
            prompt = input(
                PURPLE + f"JiJi [{mode.upper()}] ❯ " + RESET
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSampai jumpa.")
            break

        if not prompt:
            continue

        command = prompt.lower()

        if command in {"/exit", "exit", "keluar", "quit"}:
            print("Sampai jumpa.")
            break

        if command == "/status":
            print(f"Mode aktif : {mode.upper()}")
            print("Local      : JiJi/Ollama")
            print("Cloud      : Gemini")
            continue

        if command.startswith("/mode "):
            requested = command.split(maxsplit=1)[1]

            if requested not in {"local", "cloud", "auto"}:
                print("Mode tersedia: local, cloud, auto")
                continue

            mode = requested
            save_mode(mode)
            print(f"✓ Mode diubah menjadi {mode.upper()}")
            continue

        try:
            answer(prompt, mode)
        except Exception as error:
            print(f"\n✗ Terjadi error: {error}")

        print()


if __name__ == "__main__":
    main()
