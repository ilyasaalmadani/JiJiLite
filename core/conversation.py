import re

SHORT_CONFIRMATIONS = {
    "ya",
    "iya",
    "yap",
    "oke",
    "ok",
    "baik",
    "betul",
    "benar",
    "lanjut",
    "terus",
    "silakan",
    "boleh",
}

FOLLOW_UP_MARKERS = (
    "worth it",
    "layak",
    "kenapa",
    "mengapa",
    "bagaimana",
    "gimana",
    "berapa",
    "yakin",
    "masa",
    "benarkah",
    "apa risikonya",
    "apa keuntungannya",
    "apa kekurangannya",
    "lebih rinci",
    "jelaskan lagi",
    "lanjutkan",
    "terus bagaimana",
    "kalau begitu",
    "kalau iya",
    "kalau tidak",
)

CORRECTION_MARKERS = (
    "kurang akurat",
    "tidak akurat",
    "belum akurat",
    "salah",
    "cek lagi",
    "verifikasi lagi",
    "coba cari lagi",
    "mana buktinya",
    "apa sumbernya",
)

BROAD_TOPIC_PATTERNS = (
    r"^saya (ingin|mau|butuh) (membahas|informasi tentang|tahu tentang) (.+)$",
    r"^jelaskan tentang (.+)$",
    r"^informasi tentang (.+)$",
    r"^(.{3,40})\?$",
)

def normalize(text):
    return " ".join(
        str(text or "").lower().strip().split()
    )

def extract_topic(prompt):
    text = normalize(prompt)

    for pattern in BROAD_TOPIC_PATTERNS:
        match = re.match(pattern, text)

        if match:
            topic = match.groups()[-1]
            return topic.strip(" ?.")

    if len(text.split()) <= 5:
        blocked = SHORT_CONFIRMATIONS | {
            "kenapa",
            "mengapa",
            "bagaimana",
            "gimana",
            "worth it",
        }

        if text not in blocked:
            return text.strip(" ?.")

    return ""

def is_confirmation(prompt):
    return normalize(prompt) in SHORT_CONFIRMATIONS

def is_correction(prompt):
    text = normalize(prompt)
    return any(marker in text for marker in CORRECTION_MARKERS)

def is_follow_up(prompt):
    text = normalize(prompt)

    if is_confirmation(prompt) or is_correction(prompt):
        return True

    if len(text.split()) <= 8:
        return any(marker in text for marker in FOLLOW_UP_MARKERS)

    return False

def detect_intent(prompt):
    text = normalize(prompt)

    if is_confirmation(prompt):
        return "CONFIRM"

    if is_correction(prompt):
        return "VERIFY"

    if "worth it" in text or "layak" in text:
        return "EVALUATE"

    if text.startswith(("kenapa", "mengapa")):
        return "EXPLAIN_CAUSE"

    if text.startswith(("bagaimana", "gimana")):
        return "EXPLAIN_METHOD"

    if "risiko" in text:
        return "RISK"

    if "keuntungan" in text or "manfaat" in text:
        return "BENEFIT"

    return "ASK"

def needs_clarification(prompt, session):
    text = normalize(prompt)

    if is_confirmation(prompt):
        return not bool(session.get("topic"))

    vague = (
        len(text.split()) <= 2
        and not is_follow_up(prompt)
        and not session.get("topic")
    )

    return vague

def build_effective_query(prompt, session):
    text = normalize(prompt)
    topic = session.get("topic", "").strip()
    goal = session.get("goal", "").strip()
    last_query = session.get("last_user_query", "").strip()

    if is_confirmation(prompt):
        if topic:
            return (
                f"Jelaskan lebih lanjut mengenai {topic}. "
                f"Fokus tujuan pengguna: {goal or 'memahami topik tersebut'}."
            )

        return prompt

    if is_correction(prompt):
        base = topic or last_query

        if base:
            return (
                f"Verifikasi ulang informasi mengenai {base}. "
                f"Masukan pengguna: {prompt}. "
                "Gunakan sumber yang lebih kuat dan jangan mengarang."
            )

    if is_follow_up(prompt) and topic:
        return (
            f"Topik percakapan: {topic}. "
            f"Pertanyaan lanjutan pengguna: {prompt}. "
            f"Tujuan percakapan: {goal or 'memberikan jawaban yang relevan'}."
        )

    return prompt

def update_state(prompt, session):
    topic = session.get("topic", "")
    extracted = extract_topic(prompt)

    if extracted and not is_follow_up(prompt):
        topic = extracted

    intent = detect_intent(prompt)

    goal = session.get("goal", "")

    if intent == "EVALUATE":
        goal = f"menilai kelayakan {topic or prompt}"

    elif intent == "RISK":
        goal = f"memahami risiko {topic or prompt}"

    elif intent == "BENEFIT":
        goal = f"memahami manfaat {topic or prompt}"

    elif not goal and topic:
        goal = f"memahami {topic}"

    return {
        "topic": topic,
        "subtopic": normalize(prompt) if topic else "",
        "goal": goal,
        "intent": intent,
    }
