from core.chat import WEB_NEEDED, ask_local
from core.hallucination_guard import assess_local_answer
from core.memory import empty_session, load, remember
from core.output_cleaner import clean_output
from core.plan_guard import guard_plan
from core.planner import plan
from core.policy_engine import evaluate
from core.turn_guard import is_stale_plan
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


def apply_pipeline(user_message, session):
    cognitive_plan = plan(user_message, session)
    cognitive_plan = guard_plan(
        cognitive_plan,
        session,
        user_message,
    )

    # Cegah memory lama mengambil alih pertanyaan baru.
    if is_stale_plan(user_message, cognitive_plan):
        clean_session = empty_session()

        cognitive_plan = plan(
            user_message,
            clean_session,
        )

        cognitive_plan = guard_plan(
            cognitive_plan,
            clean_session,
            user_message,
        )

        cognitive_plan["intent"] = (
            cognitive_plan.get("intent")
            or "NEW_TOPIC"
        )

    policy = evaluate(cognitive_plan, session)

    cognitive_plan["route"] = policy.route
    cognitive_plan["resolved_query"] = (
        policy.resolved_query
        or cognitive_plan.get("resolved_query")
        or user_message
    )
    cognitive_plan["topic"] = (
        policy.topic
        or cognitive_plan.get("topic", "")
    )
    cognitive_plan["canonical_topic"] = (
        policy.canonical_topic
        or cognitive_plan.get("canonical_topic", "")
    )
    cognitive_plan["entities"] = (
        policy.entities
        or cognitive_plan.get("entities", [])
    )
    cognitive_plan["intent"] = (
        policy.intent
        or cognitive_plan.get("intent", "ASK")
    )
    cognitive_plan["confidence"] = policy.confidence

    if policy.route == "CLARIFY":
        cognitive_plan["need_clarification"] = True
        cognitive_plan["clarification_question"] = (
            policy.clarification
        )

    return cognitive_plan


def execute_web(user_message, cognitive_plan):
    print("🌐 Web Search")
    print(
        "🧭 Topik:",
        cognitive_plan.get("canonical_topic")
        or cognitive_plan.get("topic")
        or "-",
    )
    print()

    try:
        answer, _ = search(
            cognitive_plan["resolved_query"]
        )
        answer = clean_output(answer)
        route = "WEB"

    except Exception as error:
        answer = (
            "Verifikasi web belum berhasil. "
            f"Detail: {error}"
        )
        route = "ERROR"

    print(answer)

    remember(
        user_message,
        answer,
        route,
        cognitive_plan,
    )

    return answer


def handle(user_message):
    text = normalize(user_message)

    if text in FAST_RESPONSES:
        answer = FAST_RESPONSES[text]
        print("⚡ Fast Chat\n")
        print(answer)
        return answer

    session = load()
    cognitive_plan = apply_pipeline(
        user_message,
        session,
    )

    if cognitive_plan.get("need_clarification"):
        answer = (
            cognitive_plan.get("clarification_question")
            or "Mohon jelaskan maksud Anda sedikit lebih spesifik."
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

    if cognitive_plan["route"] in {"WEB", "VERIFY"}:
        return execute_web(
            user_message,
            cognitive_plan,
        )

    answer = ask_local(
        cognitive_plan["resolved_query"],
        session,
    )
    answer = clean_output(answer)

    if WEB_NEEDED.lower() in answer.lower():
        cognitive_plan["route"] = "WEB"
        return execute_web(
            user_message,
            cognitive_plan,
        )

    guard = assess_local_answer(
        cognitive_plan["resolved_query"],
        answer,
        cognitive_plan,
    )

    if not guard.safe and guard.action == "WEB":
        print(
            "🌐 Jawaban lokal perlu diverifikasi. "
            "Mencari sumber web...\n"
        )
        cognitive_plan["route"] = "WEB"
        return execute_web(
            user_message,
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
