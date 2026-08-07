import os
import subprocess
import sys

from core.cloud import ask_cloud


ROOT = os.path.expanduser("~/JiJiLite")
CLOUD_TRIGGER = "WEB_SEARCH_NEEDED"


def ask_local(prompt: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["jiji", prompt],
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        return False, "JiJi lokal timeout."

    output = (result.stdout or "").strip()

    if result.returncode != 0:
        error = (result.stderr or "").strip()
        return False, error or "JiJi lokal gagal."

    if not output:
        return False, "JiJi lokal menghasilkan jawaban kosong."

    if CLOUD_TRIGGER.lower() in output.lower():
        return False, output

    failure_markers = (
        "belum cukup yakin",
        "mohon jelaskan sedikit lebih spesifik",
        "web search gagal",
        "ollama gagal",
        "model lokal gagal",
    )

    lowered = output.lower()

    if any(marker in lowered for marker in failure_markers):
        return False, output

    return True, output


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()

    if not prompt:
        print('Gunakan: jiji-auto "pertanyaan"')
        raise SystemExit(1)

    success, local_answer = ask_local(prompt)

    if success:
        print(local_answer)
        return

    print("☁️ Lokal belum cukup. Beralih ke Gemini...\n")

    try:
        print(ask_cloud(prompt))
    except Exception as error:
        print("✗ Lokal dan cloud sama-sama gagal.")
        print(f"Detail lokal: {local_answer}")
        print(f"Detail cloud: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
