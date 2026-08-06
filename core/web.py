#!/usr/bin/env python3
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
CONFIG = ROOT / "config" / "tavily.conf"

NEWS_TERMS = (
    "berita", "hari ini", "terbaru", "update", "politik",
    "ekonomi", "saham", "harga", "cuaca", "gempa",
)

def api_key():
    if not CONFIG.exists():
        raise RuntimeError("Konfigurasi Tavily tidak ditemukan.")
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        if line.startswith("TAVILY_API_KEY="):
            key = line.split("=", 1)[1].strip().strip("'\"")
            if key:
                return key
    raise RuntimeError("API key Tavily kosong.")

def search(query):
    topic = "news" if any(x in query.lower() for x in NEWS_TERMS) else "general"

    payload = json.dumps({
        "query": query,
        "topic": topic,
        "search_depth": "advanced",
        "max_results": 5,
        "include_answer": True,
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={
            "Authorization": "Bearer " + api_key(),
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=40) as response:
        data = json.load(response)

    answer = (data.get("answer") or "").strip()
    results = data.get("results", [])

    lines = []
    if answer:
        lines.append(answer)
    else:
        lines.append(
            "Saya belum menemukan jawaban yang cukup kuat untuk disimpulkan."
        )

    lines.append("")
    lines.append("Sumber:")
    for number, item in enumerate(results, 1):
        title = item.get("title") or "Tanpa judul"
        date = item.get("published_date") or "Tanggal tidak tersedia"
        url = item.get("url") or ""
        lines.append(f"{number}. {title}")
        lines.append(f"   Tanggal: {date}")
        lines.append(f"   {url}")

    return "\n".join(lines), results

def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("Masukkan pertanyaan web.")
        raise SystemExit(1)

    try:
        answer, _ = search(query)
        print(answer)
    except Exception as error:
        print(f"Web Search gagal: {error}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
