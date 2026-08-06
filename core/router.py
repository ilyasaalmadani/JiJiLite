import os
import subprocess

ROOT = os.path.expanduser("~/JiJiLite")
CHAT_MODEL = "gemma3:4b"

WEB_KEYWORDS = [
    "berita", "hari ini", "terbaru", "update", "sekarang",
    "cari", "search", "sesrch", "web", "website", "internet",
    "browsing", "cek online", "sumber", "referensi",
    "politik", "ekonomi", "saham", "harga", "cuaca", "gempa",
    "presiden", "menteri", "bitcoin", "emas", "2026"
]

IDENTITY_PREFIXES = (
    "siapa ", "siapakah ", "siapa itu ", "siapakah itu ",
)

UNCERTAIN_MARKERS = [
    "web_search_needed",
    "saya tidak tahu",
    "saya tidak yakin",
    "tidak dapat memastikan",
    "tidak memiliki informasi",
    "informasi tidak tersedia",
    "tidak ditemukan",
]

def web_search(prompt):
    print("🌐 Web Search\n")
    subprocess.run([
        "python3",
        f"{ROOT}/core/web.py",
        prompt
    ])

def local_chat(prompt):
    system = (
        "Anda adalah JiJi Lite. Jawab dalam Bahasa Indonesia, "
        "singkat, jelas, dan akurat. Jangan mengarang nama, "
        "jabatan, organisasi, sumber, tanggal, atau biografi. "
        "Jika tidak benar-benar yakin atau informasi perlu "
        "diverifikasi, jawab hanya: WEB_SEARCH_NEEDED"
    )

    result = subprocess.run(
        [
            "ollama",
            "run",
            CHAT_MODEL,
            f"{system}\n\nPertanyaan: {prompt}"
        ],
        text=True,
        capture_output=True
    )

    if result.returncode != 0:
        web_search(prompt)
        return

    answer = result.stdout.strip()
    lower_answer = answer.lower()

    if not answer or any(x in lower_answer for x in UNCERTAIN_MARKERS):
        print("Informasi perlu diverifikasi. Mencari di web...\n")
        web_search(prompt)
        return

    print("💬 Chat\n")
    print(answer)

def handle(prompt):
    text = " ".join(prompt.lower().split())

    needs_web = (
        any(keyword in text for keyword in WEB_KEYWORDS)
        or text.startswith(IDENTITY_PREFIXES)
    )

    if needs_web:
        web_search(prompt)
    else:
        local_chat(prompt)
