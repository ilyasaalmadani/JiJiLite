import re

STOPWORDS = {
    "apa", "apakah", "itu", "yang", "di", "ke", "dari",
    "dan", "atau", "ada", "saja", "aja", "yg", "bagaimana",
    "gimana", "kenapa", "mengapa", "siapa", "dimana",
    "mana", "tersebut", "ini", "disana", "sana",
}

def tokens(text):
    words = re.findall(
        r"[a-zA-ZÀ-ÿ0-9]+",
        str(text or "").lower(),
    )
    return {
        word for word in words
        if len(word) >= 3 and word not in STOPWORDS
    }

def is_stale_plan(user_message, plan):
    user_tokens = tokens(user_message)

    # Pesan pendek seperti "wisata", "iya", atau "di sana"
    # memang boleh menggunakan konteks sebelumnya.
    if len(user_tokens) < 1:
        return False

    resolved = str(
        plan.get("resolved_query") or ""
    )

    plan_tokens = tokens(resolved)

    if not plan_tokens:
        return True

    overlap = user_tokens & plan_tokens

    # Setiap pokok kata dari pesan baru semestinya muncul
    # pada query yang sudah diselesaikan planner.
    return len(overlap) == 0
