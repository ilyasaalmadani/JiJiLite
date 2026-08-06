def normalize_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(0.0, min(1.0, score))


def confidence_label(score: float) -> str:
    score = normalize_score(score)

    if score >= 0.80:
        return "TINGGI"

    if score >= 0.55:
        return "SEDANG"

    return "RENDAH"


def should_clarify(score: float) -> bool:
    return normalize_score(score) < 0.40
