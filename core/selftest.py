#!/usr/bin/env python3
from core.router import classify, contextualize

def expect(actual, expected, name):
    if actual != expected:
        raise AssertionError(f"{name}: {actual!r} != {expected!r}")
    print(f"✓ {name}")

web_session = {
    "last_query": "Siapakah Ilyas Akbar Almadani?",
    "last_mode": "WEB",
}

expect(classify("Apa itu demokrasi?"), "LOCAL", "pengetahuan umum lokal")
expect(classify("berita politik hari ini"), "WEB", "berita ke web")
expect(classify("siapakah Ilyas Akbar Almadani?"), "WEB", "identitas ke web")
expect(classify("cari di website"), "WEB", "perintah web")
expect(classify("kurang akurat", web_session), "WEB", "follow-up memakai mode lama")

rewritten = contextualize("kurang akurat", web_session)
assert "Ilyas Akbar Almadani" in rewritten
print("✓ follow-up membawa konteks")

print("\nSemua tes v0.4.4 berhasil.")
