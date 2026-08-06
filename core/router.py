from core.chat import FALLBACK_TOKEN, ask_local
from core.conversation import (
    build_effective_query,
    is_confirmation,
    is_correction,
    is_follow_up,
    needs_clarification,
    update_state,
)
from core.memory import load, remember
from core.web import search

WEB_TERMS = (
    "berita",
    "hari ini",
    "terbaru",
    "sekarang",
    "terkini",
    "update",
    "cari",
    "search",
    "sesrch",
    "web",
    "website",
    "internet",
    "online",
    "referensi",
    "sumber",
    "harga",
    "saham",
    "cuaca",
    "gempa",
    "presiden",
    "menteri",
    "gubernur",
    "bupati",
    "wali kota",
    "pemilu",
    "pilkada",
    "2025",
    "2026",
)

IDENTITY_PREFIXES = (
    "siapa ",
    "siapakah ",
    "siapa itu ",
    "siapakah itu ",
    "profil ",
    "biodata ",
)

def normalize(text):
    return " ".join(text.lower().strip().split())

def classify(prompt, session=None):
    session = session or {}
    text = normalize(prompt)

    if is_correction(prompt):
        return "WEB"

    if is_follow_up(prompt) and session.get("last_mode") == "WEB":
        return "WEB"

    if text.startswith(IDENTITY_PREFIXES):
        return "WEB"

    if any(term in text for term in WEB_TERMS):
        return "WEB"

    return "LOCAL"

def clarification_message(prompt, session):
    topic = session.get("topic", "")

    if is_confirmation(prompt) and not topic:
        return (
            "Saya belum memiliki topik yang cukup jelas. "
            "Silakan sebutkan topik yang ingin Anda lanjutkan."
        )

    return (
        "Topiknya masih cukup luas. Anda ingin membahas "
        "pengertian, peluang, modal, risiko, strategi, "
        "atau contoh penerapannya?"
    )

def answer_web(
    prompt,
    effective_query,
    state,
):
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

    remember(
        prompt,
        answer,
        mode,
        effective_query,
        topic=state["topic"],
        subtopic=state["subtopic"],
        goal=state["goal"],
        intent=state["intent"],
    )

    return answer

def handle(prompt):
    session = load()
    state = update_state(prompt, session)

    session_with_state = {
        **session,
        **state,
    }

    if needs_clarification(prompt, session_with_state):
        answer = clarification_message(
            prompt,
            session_with_state,
        )

        print("🧭 Klarifikasi\n")
        print(answer)

        remember(
            prompt,
            answer,
            "CLARIFY",
            prompt,
            topic=state["topic"],
            subtopic=state["subtopic"],
            goal=state["goal"],
            intent=state["intent"],
        )

        return answer

    effective_query = build_effective_query(
        prompt,
        session_with_state,
    )

    mode = classify(
        effective_query,
        session_with_state,
    )

    if mode == "WEB":
        return answer_web(
            prompt,
            effective_query,
            state,
        )

    answer = ask_local(
        effective_query,
        session.get("history", []),
    )

    if FALLBACK_TOKEN.lower() in answer.lower():
        print(
            "🌐 Pengetahuan lokal belum cukup. "
            "Melakukan verifikasi web...\n"
        )

        return answer_web(
            prompt,
            effective_query,
            state,
        )

    print("💬 Chat\n")
    print(answer)

    remember(
        prompt,
        answer,
        "LOCAL",
        effective_query,
        topic=state["topic"],
        subtopic=state["subtopic"],
        goal=state["goal"],
        intent=state["intent"],
    )

    return answer
