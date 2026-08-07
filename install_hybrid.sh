#!/bin/zsh
set -euo pipefail

ROOT="$HOME/JiJiLite"
CORE="$ROOT/core"
BIN="$ROOT/bin"

cd "$ROOT"
mkdir -p "$CORE" "$BIN"

echo "╭─ JiJi Hybrid Installer ─────────────────╮"
echo "│ LOCAL • CLOUD • AUTO                    │"
echo "╰─────────────────────────────────────────╯"
echo

if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "✗ GEMINI_API_KEY belum aktif."
    echo "Jalankan: source ~/.zshrc"
    exit 1
fi

echo "[1/5] Memasang Gemini SDK..."
python3 -m pip install --user -U google-genai

cat > "$CORE/cloud.py" <<'PY'
import os
import sys

from google import genai
from google.genai import types


MODEL = os.environ.get(
    "JIJI_GEMINI_MODEL",
    "gemini-2.5-flash",
)

SYSTEM = """
Anda adalah JiJi Cloud, asisten AI berbahasa Indonesia.

Aturan:
1. Jawab dalam Bahasa Indonesia kecuali diminta lain.
2. Gunakan konteks pertanyaan secara tepat.
3. Jangan mengarang fakta, sumber, URL, nama, jabatan, atau angka.
4. Bila informasi tidak pasti atau membutuhkan data terbaru,
   nyatakan keterbatasannya dengan jelas.
5. Jawab langsung, natural, dan tidak bertele-tele.
""".strip()


def ask_cloud(prompt: str) -> str:
    key = os.environ.get("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan.")

    client = genai.Client(api_key=key)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            temperature=0.2,
            max_output_tokens=1200,
        ),
    )

    text = getattr(response, "text", None)

    if not text:
        raise RuntimeError(
            "Gemini tidak menghasilkan jawaban teks."
        )

    return text.strip()


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()

    if not prompt:
        print('Gunakan: jiji-cloud "pertanyaan"')
        raise SystemExit(1)

    try:
        print("☁️ JiJi Cloud\n")
        print(ask_cloud(prompt))

    except Exception as error:
        print(f"✗ JiJi Cloud gagal: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
PY

cat > "$CORE/hybrid.py" <<'PY'
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
PY

cat > "$BIN/jiji-cloud" <<'SH'
#!/bin/zsh
export PYTHONPATH="$HOME/JiJiLite"
exec python3 "$HOME/JiJiLite/core/cloud.py" "$@"
SH

cat > "$BIN/jiji-local" <<'SH'
#!/bin/zsh
exec jiji "$@"
SH

cat > "$BIN/jiji-auto" <<'SH'
#!/bin/zsh
export PYTHONPATH="$HOME/JiJiLite"
exec python3 -m core.hybrid "$@"
SH

chmod +x \
  "$BIN/jiji-cloud" \
  "$BIN/jiji-local" \
  "$BIN/jiji-auto"

echo "[2/5] Memeriksa Python..."
python3 -m py_compile \
  "$CORE/cloud.py" \
  "$CORE/hybrid.py"

echo "✓ Syntax valid"

echo "[3/5] Menambahkan command ke PATH..."

grep -qxF 'export PATH="$HOME/JiJiLite/bin:$PATH"' \
  "$HOME/.zshrc" 2>/dev/null || \
  echo 'export PATH="$HOME/JiJiLite/bin:$PATH"' \
  >> "$HOME/.zshrc"

export PATH="$HOME/JiJiLite/bin:$PATH"

echo "[4/5] Tes koneksi Gemini..."

jiji-cloud \
  "Jawab hanya dengan kalimat: JiJi Cloud siap."

echo
echo "[5/5] Selesai"
echo
echo "Perintah tersedia:"
echo '  jiji-local "apa itu demokrasi?"'
echo '  jiji-cloud "analisis bisnis AI secara mendalam"'
echo '  jiji-auto  "jelaskan peluang bisnis AI"'
