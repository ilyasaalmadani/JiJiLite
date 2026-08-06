#!/usr/bin/env python3

from core.conversation import (
    build_effective_query,
    detect_intent,
    extract_topic,
    is_confirmation,
    is_follow_up,
    update_state,
)
from core.memory import empty_session
from core.router import classify

passed = 0

def check(condition, label):
    global passed

    if not condition:
        raise AssertionError(label)

    passed += 1
    print(f"✓ {label}")

check(
    extract_topic(
        "Saya butuh informasi tentang bisnis AI"
    ) == "bisnis ai",
    "Topik bisnis AI terdeteksi",
)

check(
    is_confirmation("ya"),
    "Jawaban ya dikenali",
)

check(
    is_confirmation("iya"),
    "Jawaban iya dikenali",
)

check(
    is_follow_up("apakah worth it"),
    "Worth it dikenali sebagai follow-up",
)

check(
    detect_intent("apakah worth it") == "EVALUATE",
    "Intent evaluasi terdeteksi",
)

session = empty_session()
session["topic"] = "bisnis AI"
session["goal"] = "memahami bisnis AI"
session["last_mode"] = "LOCAL"
session["last_user_query"] = (
    "Saya butuh informasi tentang bisnis AI"
)

effective = build_effective_query(
    "apakah worth it",
    session,
)

check(
    "bisnis AI" in effective,
    "Query follow-up membawa topik",
)

check(
    "worth it" in effective,
    "Query follow-up membawa pertanyaan",
)

confirmation = build_effective_query(
    "ya",
    session,
)

check(
    "bisnis AI" in confirmation,
    "Konfirmasi membawa topik",
)

state = update_state(
    "apakah worth it",
    session,
)

check(
    state["topic"] == "bisnis AI",
    "State mempertahankan topik",
)

check(
    state["intent"] == "EVALUATE",
    "State menyimpan intent",
)

check(
    classify(
        "berita bisnis AI hari ini",
        session,
    ) == "WEB",
    "Berita bisnis AI memakai web",
)

check(
    classify(
        effective,
        session,
    ) == "LOCAL",
    "Evaluasi umum dapat memakai lokal",
)

print()
print(
    f"Semua {passed} Conversation Intelligence tests berhasil."
)
