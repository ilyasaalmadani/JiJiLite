def normalize_score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(0.0, min(1.0, score))


def should_clarify(score):
    return normalize_score(score) < 0.35
