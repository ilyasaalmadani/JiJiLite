from core.confidence_engine import normalize_score, should_clarify
from core.policies.types import Decision


VALID_ROUTES = {
    "LOCAL",
    "WEB",
    "VERIFY",
    "CLARIFY",
}


def evaluate(plan, session):
    plan = plan if isinstance(plan, dict) else {}
    session = session if isinstance(session, dict) else {}

    resolved_query = str(
        plan.get("resolved_query") or ""
    ).strip()

    topic = str(
        plan.get("topic")
        or session.get("topic")
        or ""
    ).strip()

    canonical_topic = str(
        plan.get("canonical_topic")
        or session.get("canonical_topic")
        or topic
    ).strip()

    entities = (
        plan.get("entities")
        or session.get("entities")
        or []
    )

    if not isinstance(entities, list):
        entities = []

    route = str(
        plan.get("route") or "LOCAL"
    ).upper()

    confidence = normalize_score(
        plan.get("confidence", 0.5)
    )

    if route not in VALID_ROUTES:
        route = "CLARIFY"

    if should_clarify(confidence):
        route = "CLARIFY"

    clarification = ""

    if route == "CLARIFY":
        clarification = (
            "Saya belum cukup yakin memahami maksud Anda. "
            "Mohon jelaskan sedikit lebih spesifik."
        )

    return Decision(
        route=route,
        resolved_query=resolved_query,
        topic=topic,
        canonical_topic=canonical_topic,
        entities=entities,
        intent=str(plan.get("intent") or "ASK").upper(),
        confidence=confidence,
        reason="Policy validation",
        clarification=clarification,
    )
