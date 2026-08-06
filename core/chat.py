import subprocess
from core.config import CONFIG

CHAT_MODEL = CONFIG.get("chat_model", "gemma3:4b")
FALLBACK_TOKEN = "WEB_SEARCH_NEEDED"

SYSTEM_PROMPT = """
Anda adalah JiJi Lite, asisten AI lokal berbahasa Indonesia.

ATURAN MUTLAK:
1. Selalu jawab dalam Bahasa Indonesia.
2. Jangan mengarang nama, jabatan, organisasi, tanggal, angka,
   berita, kutipan, URL, sumber, biografi, atau peristiwa.
3. Jangan membuat referensi atau tautan palsu.
4. Bila informasi bersifat terbaru, identitas seseorang tidak dikenal,
   fakta meragukan, atau memerlukan verifikasi, jawab hanya:
   WEB_SEARCH_NEEDED
5. Bedakan fakta, analisis, perkiraan, dan opini.
6. Jangan mengaku sudah mencari internet apabila belum melakukannya.
7. Jangan tampilkan proses berpikir internal.
8. Jawab singkat, jelas, dan langsung ke inti.
""".strip()

def ask_local(prompt, history=None):
    history = history or []

    context_lines = []
    for item in history[-6:]:
        role = item.get("role", "")
        content = item.get("content", "")
        context_lines.append(f"{role}: {content}")

    context = "\n".join(context_lines)

    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Konteks percakapan:\n{context}\n\n"
        f"Pertanyaan pengguna:\n{prompt}"
    )

    result = subprocess.run(
        ["ollama", "run", CHAT_MODEL, full_prompt],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return FALLBACK_TOKEN

    answer = result.stdout.strip()

    if not answer:
        return FALLBACK_TOKEN

    return answer
