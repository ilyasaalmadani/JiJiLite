from core.chat import FALLBACK_TOKEN, ask_local
from core.memory import load, remember
from core.web import search

WEB_TERMS = (
    "berita", "hari ini", "terbaru", "sekarang", "update",
    "cari", "search", "sesrch", "telusuri", "web", "website",
    "internet", "browsing", "online", "referensi", "sumber",
    "harga", "saham", "cuaca", "gempa", "presiden", "menteri",
    "gubernur", "bupati", "wali kota", "dpr", "pemilu",
    "pilkada", "2025", "2026",
)

IDENTITY_PREFIXES = (
    "siapa ",
    "siapakah ",
    "siapa itu ",
    "siapakah itu ",
    "profil ",
    "biodata ",
)

FOLLOW_UP_TERMS = (
    "kurang akurat",
    "tidak akurat",
    "belum akurat",
    "salah",
    "cek lagi",
    "coba cek lagi",
    "verifikasi lagi",
    "telusuri lagi",
    "yang tadi",
    "maksud saya",
    "lebih rinci",
    "jelaskan lagi",
    "apa sumbernya",
    "dari mana sumbernya",
    "yakin",
    "masa",
    "benarkah",
    "kok begitu",
    "buktinya",
    "mana buktinya",
)

CURRENT_FACT_TERMS = (
    "saat ini",
    "sekarang",
    "terkini",
    "terbaru",
    "masih menjabat",
    "menjabat apa",
    "siapa menjabat",
)

def normalize(text):
    return " ".join(text.lower().strip().split())

def is_follow_up(prompt):
    text = normalize(prompt)
    return any(term in text for term in FOLLOW_UP_TERMS)

def contextualize(prompt, session):
    if not is_follow_up(prompt):
        return prompt

    last_user_query = session.get("last_user_query", "")

    if not last_user_query:
        return prompt

    return (
        f"Verifikasi ulang pertanyaan berikut secara lebih akurat: "
        f"{last_user_query}. "
        f"Masukan lanjutan pengguna: {prompt}. "
        "Bandingkan beberapa sumber kredibel dan jelaskan "
        "jika terdapat ketidakpastian."
    )

def classify(prompt, session=None):
    session = session or {}
    text = normalize(prompt)

    if is_follow_up(prompt):
        if session.get("last_mode") == "WEB":
            return "WEB"
        if session.get("last_user_query"):
            return "LOCAL"

    if text.startswith(IDENTITY_PREFIXES):
        return "WEB"

    if any(term in text for term in CURRENT_FACT_TERMS):
        return "WEB"

    if any(term in text for term in WEB_TERMS):
        return "WEB"

    return "LOCAL"

def answer_web(prompt, effective_query):
    print("🌐 Web Search\n")

    try:
        answer, _ = search(effective_query)
        mode = "WEB"
    except Exception as error:
        answer = (
            "Saya belum dapat melakukan verifikasi web. "
            f"Detail: {error}"
        )
        mode = "ERROR"

    print(answer)
    remember(prompt, answer, mode, effective_query)
    return answer

def handle(prompt):
    session = load()
    effective_query = contextualize(prompt, session)
    mode = classify(prompt, session)

    if mode == "WEB":
        return answer_web(prompt, effective_query)

    answer = ask_local(
        effective_query,
        session.get("history", []),
    )

    if FALLBACK_TOKEN.lower() in answer.lower():
        print(
            "🌐 Pengetahuan lokal belum cukup. "
            "Melakukan verifikasi web...\n"
        )
        return answer_web(prompt, effective_query)

    print("💬 Chat\n")
    print(answer)

    remember(
        prompt,
        answer,
        "LOCAL",
        effective_query,
    )

    return answer
