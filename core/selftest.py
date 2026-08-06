#!/usr/bin/env python3

import tempfile
from pathlib import Path

from core.memory import empty_session
from core.router import classify, contextualize
from core.web import deduplicate

def expect(actual, expected, label):
    if actual != expected:
        raise AssertionError(
            f"{label}: {actual!r} != {expected!r}"
        )
    print(f"✓ {label}")

web_session = empty_session()
web_session["last_user_query"] = "Siapakah Juliyatmono?"
web_session["last_mode"] = "WEB"

expect(
    classify("Apa itu demokrasi?"),
    "LOCAL",
    "Pengetahuan umum memakai lokal",
)

expect(
    classify("Berita politik hari ini"),
    "WEB",
    "Informasi terbaru memakai web",
)

expect(
    classify("Siapakah Juliyatmono?"),
    "WEB",
    "Identitas memakai web",
)

expect(
    classify("Kurang akurat", web_session),
    "WEB",
    "Follow-up mempertahankan web",
)

rewritten = contextualize("Kurang akurat", web_session)

if "Juliyatmono" not in rewritten:
    raise AssertionError("Topik hilang saat query rewrite")

print("✓ Query rewrite mempertahankan topik")

sample = [
    {
        "title": "Berita A",
        "url": "https://contoh.id/a",
        "content": "Isi pertama",
        "score": 0.9,
    },
    {
        "title": "Berita A",
        "url": "https://contoh.id/a/",
        "content": "Duplikat",
        "score": 0.8,
    },
]

expect(
    len(deduplicate(sample)),
    1,
    "Sumber duplikat dihapus",
)

print()
print("Semua self-test v0.4.6 berhasil.")
