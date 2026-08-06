#!/usr/bin/env python3

from core.memory import empty_session
from core.router import classify, contextualize

def expect(actual, expected, label):
    if actual != expected:
        raise AssertionError(
            f"{label}: {actual!r} != {expected!r}"
        )
    print(f"✓ {label}")

web_session = empty_session()
web_session["last_user_query"] = (
    "Siapakah Ilyas Akbar Almadani?"
)
web_session["last_mode"] = "WEB"

local_session = empty_session()
local_session["last_user_query"] = (
    "Jelaskan pengertian demokrasi"
)
local_session["last_mode"] = "LOCAL"

expect(
    classify("Apa itu demokrasi?"),
    "LOCAL",
    "Pertanyaan umum memakai lokal",
)

expect(
    classify("Berita politik hari ini"),
    "WEB",
    "Berita memakai web",
)

expect(
    classify("Siapakah Juliyatmono?"),
    "WEB",
    "Identitas memakai web",
)

expect(
    classify("Cari di website"),
    "WEB",
    "Instruksi web terdeteksi",
)

expect(
    classify("Kurang akurat", web_session),
    "WEB",
    "Follow-up web mempertahankan mode",
)

expect(
    classify("Jelaskan lagi", local_session),
    "LOCAL",
    "Follow-up lokal mempertahankan mode",
)

rewritten = contextualize(
    "Kurang akurat",
    web_session,
)

if "Ilyas Akbar Almadani" not in rewritten:
    raise AssertionError(
        "Contextual follow-up kehilangan topik."
    )

print("✓ Follow-up membawa topik sebelumnya")
print()
print("Semua self-test v0.4.5 berhasil.")
