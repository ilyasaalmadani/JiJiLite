#!/usr/bin/env python3

from core.memory import empty_session
from core.router import classify, contextualize
from core.source_quality import (
    deduplicate_and_rank,
    domain_score,
    evidence_confidence,
)

passed = 0

def check(condition, name):
    global passed

    if not condition:
        raise AssertionError(name)

    passed += 1
    print(f"✓ {name}")

web_session = empty_session()
web_session["last_user_query"] = "Siapakah Juliyatmono?"
web_session["last_mode"] = "WEB"

tests = [
    (
        classify("Apa itu demokrasi?") == "LOCAL",
        "Pengetahuan umum ke LOCAL",
    ),
    (
        classify("Berita politik hari ini") == "WEB",
        "Berita ke WEB",
    ),
    (
        classify("Siapakah Juliyatmono?") == "WEB",
        "Identitas ke WEB",
    ),
    (
        classify("Harga emas sekarang") == "WEB",
        "Harga terbaru ke WEB",
    ),
    (
        classify("Siapa presiden sekarang?") == "WEB",
        "Jabatan terkini ke WEB",
    ),
    (
        classify("Kurang akurat", web_session) == "WEB",
        "Koreksi mempertahankan WEB",
    ),
    (
        classify("Yakin?", web_session) == "WEB",
        "Pertanyaan yakin mempertahankan WEB",
    ),
    (
        classify("Mana buktinya?", web_session) == "WEB",
        "Permintaan bukti mempertahankan WEB",
    ),
]

for condition, name in tests:
    check(condition, name)

rewritten = contextualize(
    "Kurang akurat",
    web_session,
)

check(
    "Juliyatmono" in rewritten,
    "Query rewrite mempertahankan topik",
)

check(
    domain_score("antaranews.com") >= 3,
    "ANTARA diprioritaskan",
)

check(
    domain_score("instagram.com") < 0,
    "Instagram diturunkan",
)

sample = [
    {
        "title": "Berita A",
        "url": "https://antaranews.com/a",
        "content": "A" * 300,
        "score": 0.9,
        "published_date": "2026-01-01",
    },
    {
        "title": "Berita A",
        "url": "https://antaranews.com/a/",
        "content": "Duplikat",
        "score": 0.8,
    },
    {
        "title": "Video",
        "url": "https://youtube.com/a",
        "content": "",
        "score": 0.4,
    },
]

ranked = deduplicate_and_rank(sample)

check(
    len(ranked) == 2,
    "Duplikat sumber dihapus",
)

check(
    ranked[0]["url"].startswith(
        "https://antaranews.com"
    ),
    "Sumber kuat berada di atas",
)

confidence, score = evidence_confidence(ranked)

check(
    confidence in ("RENDAH", "SEDANG", "TINGGI"),
    "Confidence valid",
)

check(
    isinstance(score, int),
    "Skor confidence numerik",
)

print()
print(f"Semua {passed} Quality Gate tests berhasil.")
