from urllib.parse import urlparse

HIGH_TRUST_DOMAINS = (
    "go.id",
    "gov",
    "ac.id",
    "edu",
    "kompas.com",
    "tempo.co",
    "antaranews.com",
    "detik.com",
    "bbc.com",
    "reuters.com",
    "apnews.com",
    "theguardian.com",
    "cnn.com",
    "cnbcindonesia.com",
    "tribunnews.com",
    "solopos.com",
    "espos.id",
)

LOW_TRUST_DOMAINS = (
    "blogspot.com",
    "wordpress.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "pinterest.com",
)

def domain_of(url):
    try:
        return (
            urlparse(url)
            .netloc
            .lower()
            .removeprefix("www.")
        )
    except ValueError:
        return ""

def domain_score(domain):
    if any(domain == item or domain.endswith("." + item)
           for item in HIGH_TRUST_DOMAINS):
        return 3

    if any(domain == item or domain.endswith("." + item)
           for item in LOW_TRUST_DOMAINS):
        return -2

    return 1

def result_score(item):
    domain = domain_of(item.get("url", ""))
    score = domain_score(domain)

    content = (item.get("content") or "").strip()
    title = (item.get("title") or "").strip()

    if len(content) >= 250:
        score += 2
    elif len(content) >= 80:
        score += 1
    else:
        score -= 1

    if item.get("published_date"):
        score += 1

    if not title or not domain:
        score -= 3

    tavily_score = float(item.get("score") or 0)
    score += min(2, round(tavily_score * 2))

    return score

def deduplicate_and_rank(results, limit=6):
    selected = []
    seen_urls = set()
    seen_titles = set()

    for item in results:
        url = (item.get("url") or "").strip()
        title = " ".join(
            (item.get("title") or "").lower().split()
        )

        url_key = url.rstrip("/").lower()

        if not url or not title:
            continue

        if url_key in seen_urls or title in seen_titles:
            continue

        item = dict(item)
        item["_quality_score"] = result_score(item)

        seen_urls.add(url_key)
        seen_titles.add(title)
        selected.append(item)

    selected.sort(
        key=lambda item: (
            item["_quality_score"],
            float(item.get("score") or 0),
        ),
        reverse=True,
    )

    return selected[:limit]

def evidence_confidence(results):
    if not results:
        return "RENDAH", 0

    domains = {
        domain_of(item.get("url", ""))
        for item in results
        if domain_of(item.get("url", ""))
    }

    strong = sum(
        1 for item in results
        if item.get("_quality_score", 0) >= 5
    )

    score = 0
    score += min(len(results), 4)
    score += min(len(domains), 3)
    score += min(strong, 3)

    if score >= 8:
        return "TINGGI", score

    if score >= 5:
        return "SEDANG", score

    return "RENDAH", score
