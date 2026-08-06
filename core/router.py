import subprocess
from core.memory import load, remember
from core.web import search

CHAT_MODEL = "gemma3:4b"

WEB_TERMS = (
    "berita", "hari ini", "terbaru", "sekarang", "update",
    "cari", "search", "sesrch", "web", "website", "internet",
    "browsing", "cek online", "referensi", "sumber",
    "harga", "saham", "cuaca", "gempa", "presiden", "menteri",
    "siapa menjabat", "2026",
)

IDENTITY_PREFIXES = (
    "siapa ", "siapakah ", "siapa itu ", "siapakah itu ",
    "profil ", "biodata ",
)

FOLLOW_UPS = (
    "kurang akurat", "tidak akurat", "salah", "cek lagi",
    "coba cek lagi", "verifikasi lagi", "yang tadi",
    "maksud saya", "lebih rinci", "jelaskan lagi",
)

FALLBACK_TOKEN = "WEB_SEARCH_NEEDED"

def normalize(text):
    return " ".join(text.lower().strip().split())

def is_follow_up(prompt):
    text = normalize(prompt)
    return any(x in text for x in FOLLOW_UPS)

def contextualize(prompt, session):
    if is_follow_up(prompt) and session.get("last_query"):
        return (
            f"Verifikasi ulang secara akurat: {session['last_query']}. "
            f"Tanggapan pengguna: {prompt}. "
            "Gunakan sumber kredibel dan jangan mengarang."
        )
    return prompt

def classify(prompt, session=None):
    session = session or {}
    text = normalize(prompt)

    if is_follow_up(prompt) and session.get("last_query"):
        return "WEB" if session.get("last_mode") == "WEB" else "LOCAL"

    if text.startswith(IDENTITY_PREFIXES):
        return "WEB"

    if any(term in text for term in WEB_TERMS):
        return "WEB"

    return "LOCAL"

def run_local(prompt, session):
    history = session.get("history", [])[-6:]
    context = "\n".join(
        f"{item.get('role')}: {item.get('content')}"
        for item in history
    )

    system = f"""
Anda adalah JiJi Lite, asisten AI lokal berbahasa Indonesia.

ATURAN KEANDALAN:
1. Jangan mengarang nama, profil, jabatan, organisasi, tanggal, angka,
   kutipan, URL, referensi, peristiwa, atau biografi.
2. Bila fakta tidak benar-benar Anda ketahui, ambigu, berubah menurut
   waktu, atau memerlukan verifikasi, jawab hanya: {FALLBACK_TOKEN}
3. Jangan mengaku telah membuka internet apabila belum melakukan web search.
4. Bedakan fakta, perkiraan, dan opini.
5. Jawab singkat, jelas, dan langsung ke inti.
6. Jangan menampilkan proses berpikir internal.

Konteks percakapan:
{context}
""".strip()

    result = subprocess.run(
        [
            "ollama", "run", CHAT_MODEL,
            f"{system}\n\nPertanyaan pengguna: {prompt}",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return FALLBACK_TOKEN

    answer = result.stdout.strip()
    if not answer:
        return FALLBACK_TOKEN
    return answer

def handle(prompt):
    session = load()
    effective_query = contextualize(prompt, session)
    mode = classify(prompt, session)

    if mode == "WEB":
        print("🌐 Web Search\n")
        try:
            answer, _ = search(effective_query)
        except Exception as error:
            answer = f"Web Search gagal: {error}"
        print(answer)
        remember(prompt, answer, "WEB", effective_query)
        return answer

    answer = run_local(effective_query, session)

    if FALLBACK_TOKEN.lower() in answer.lower():
        print("🌐 Informasi perlu diverifikasi. Mencari di web...\n")
        try:
            answer, _ = search(effective_query)
            mode = "WEB"
        except Exception as error:
            answer = (
                "Saya belum dapat memastikan jawabannya dan verifikasi web "
                f"gagal: {error}"
            )
            mode = "LOCAL"
    else:
        print("💬 Chat\n")

    print(answer)
    remember(prompt, answer, mode, effective_query)
    return answer
