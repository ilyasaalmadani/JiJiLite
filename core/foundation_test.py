#!/usr/bin/env python3

from core.confidence_engine import (
    confidence_label,
    normalize_score,
    should_clarify,
)
from core.output_cleaner import clean_output


def check(condition, label):
    if not condition:
        raise AssertionError(label)

    print(f"✓ {label}")


check(
    clean_output("Karang\\</b>anyar") == "Karang anyar",
    "HTML rusak dibersihkan",
)

check(
    clean_output("<b>Karanganyar</b>") == "Karanganyar",
    "Tag HTML dihapus",
)

check(
    confidence_label(0.90) == "TINGGI",
    "Confidence tinggi",
)

check(
    confidence_label(0.60) == "SEDANG",
    "Confidence sedang",
)

check(
    should_clarify(0.20),
    "Confidence rendah meminta klarifikasi",
)

check(
    normalize_score(5) == 1.0,
    "Confidence maksimum dibatasi",
)

print()
print("Foundation tests berhasil.")
