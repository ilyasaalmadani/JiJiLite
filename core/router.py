from core.chat import WEB_NEEDED, ask_local
from core.memory import load, remember
from core.output_cleaner import clean_output
from core.planner import plan
from core.web import search


FAST_RESPONSES = {
    "halo": "Halo! Ada yang bisa saya bantu?",
    "hai": "Hai! Ada yang ingin Anda bahas?",
    "hi": "Halo! Ada yang bisa saya bantu?",
    "hello": "Halo! Ada yang bisa saya bantu?",
    "terima kasih": "Sama-sama.",
    "makasih": "Sama-sama.",
}


def normalize(value):
    return " ".join(
        str(value or "").lower().strip().split()
    )


def needs_context(text):
    words = text.split()

    if len(words) <= 2:
        return True

    references = (
        "di sana",
        "disana",
        "dia",
        "beliau",
        "mereka",
        "yang tadi",
        "tempat itu",
        "daerah itu",
        "itu bagaimana",
        "bagaimana di sana",
        "apakah worth it",
        "kenapa begitu",
    )

    return any(item in text for item in references)


def needs_web(text):
    current_terms = (
        "sekarang",
        "terbaru",
        "hari ini",
        "terkini",
        "berita",
        "harga",
        "cuaca",
        "siapa presiden",
        "siapa menteri",
        "siapa bupati",
        "siapa gubernur",
        "jumlah penduduk",
        "wisata di",
        "kuliner di",
        "tempat wisata",
    )

    return any(item in text for item in current_terms)


def execute_web(user_message, query, plan_data=None):
    plan_data = plan_data or {
        "resolved_query": query,
        "topic": query,
        "canonical_topic": query,
        "entities": [],
        "intent": "ASK",
        "goal": "",
        "route": "WEB",
        "confidence": 1.0,
    }

    print("🌐 Web Search\n")

    try:
        answer, _ = search(query)
        answer = clean_output(answer)
        route = "WEB"
    except Exception as error:
        answer = f"Web Search gagal: {error}"
        route = "ERROR"

    print(answer)
    remember(user_message, answer, route, plan_data)
    return answer


def handle(user_message):
    text = normalize(user_message)

    if text in FAST_RESPONSES:
        answer = FAST_RESPONSES[text]
        print("⚡ Fast Chat\n")
        print(answer)
        return answer

    session = load()

    # Fakta aktual langsung WEB.
    if needs_web(text):
        return execute_web(
            user_message,
            user_message,
        )

    # Pertanyaan mandiri langsung ke Phi.
    if not needs_context(text):
        answer = ask_local(
            user_message,
            session,
        )
        answer = clean_output(answer)

        if WEB_NEEDED.lower() in answer.lower():
            return execute_web(
                user_message,
                user_message,
            )

        print("💬 Chat\n")
        print(answer)

        remember(
            user_message,
            answer,
            "LOCAL",
            {
                "resolved_query": user_message,
                "topic": user_message,
                "canonical_topic": user_message,
                "entities": [],
                "intent": "ASK",
                "goal": "",
                "route": "LOCAL",
                "confidence": 1.0,
            },
        )

        return answer

    # Hanya pertanyaan yang butuh konteks memakai planner.
    cognitive_plan = plan(user_message, session)

    if cognitive_plan.get("need_clarification"):
        answer = (
            cognitive_plan.get("clarification_question")
            or "Mohon jelaskan sedikit lebih spesifik."
        )

        print("🧭 Klarifikasi\n")
        print(answer)

        remember(
            user_message,
            answer,
            "CLARIFY",
            cognitive_plan,
        )
        return answer

    query = (
        cognitive_plan.get("resolved_query")
        or user_message
    )

    if cognitive_plan.get("route") in {"WEB", "VERIFY"}:
        return execute_web(
            user_message,
            query,
            cognitive_plan,
        )

    answer = ask_local(query, session)
    answer = clean_output(answer)

    if WEB_NEEDED.lower() in answer.lower():
        return execute_web(
            user_message,
            query,
            cognitive_plan,
        )

    print("💬 Chat")
    print(
        "🧭 Topik:",
        cognitive_plan.get("canonical_topic")
        or cognitive_plan.get("topic")
        or "-",
    )
    print()
    print(answer)

    remember(
        user_message,
        answer,
        "LOCAL",
        cognitive_plan,
    )

    return answer
