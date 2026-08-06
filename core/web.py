#!/usr/bin/env python3

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from core.config import CONFIG

ROOT = Path.home() / "JiJiLite"
TAVILY_CONFIG = ROOT / "config" / "tavily.conf"
CHAT_MODEL = CONFIG.get("chat_model", "gemma3:4b")
MAX_RESULTS = int(CONFIG.get("web_max_results", 5))

NEWS_TERMS = (
    "berita", "hari ini", "terbaru", "update",
    "politik", "ekonomi", "saham", "harga",
    "cuaca", "gempa", "pemilu", "pilkada",
)

def get_api_key():
    if not TAVILY_CONFIG.exists():
        raise RuntimeError(
            "Konfigurasi Tavily tidak ditemukan."
        )

    for line in TAVILY_CONFIG.read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith("TAVILY_API_KEY="):
            key = line.split("=", 1)[1].strip().strip("'\"")
            if key:
                return key

    raise RuntimeError("API key Tavily kosong.")

def tavily_search(query):
    topic = (
        "news"
        if any(term in query.lower() for term in NEWS_TERMS)
        else "general"
    )

    payload = json.dumps({
        "query": query,
        "topic": topic,
        "search_depth": "advanced",
        "max_results": MAX_RESULTS,
        "include_answer": False,
        "include_raw_content": False,
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={
            "Authorization": "Bearer " + get_api_key(),
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=45,
    ) as response:
        data = json.load(response)

    return data.get("results", [])

def prepare_sources(results):
    blocks = []

    for index, item in enumerate(results, 1):
        title = item.get("title") or "Tanpa judul"
        content = item.get("content") or ""
        url = item.get("url") or ""
        date = item.get("published_date") or "Tidak tersedia"

        content = content.replace("\n", " ").strip()
        content = content[:1800]

        blocks.append(
            f"[{index}]\n"
            f"Judul: {title}\n"
            f"Tanggal: {date}\n"
            f"Isi: {content}\n"
            f"URL: {url}"
        )

    return "\n\n".join(blocks)

def synthesize(query, results):
    if not results:
        return (
            "Saya belum menemukan sumber web yang cukup relevan "
            "untuk menjawab pertanyaan tersebut."
        )

    sources = prepare_sources(results)

    prompt = f"""
Anda adalah editor riset JiJi Lite.

Pertanyaan pengguna:
{query}

Hasil pencarian web:
{sources}

INSTRUKSI:
1. Jawab seluruhnya dalam Bahasa Indonesia.
2. Gunakan hanya informasi yang didukung oleh sumber di atas.
3. Jangan menambah fakta dari ingatan sendiri.
4. Jangan mengarang nama, jabatan, tanggal, status hukum, atau angka.
5. Bandingkan beberapa sumber sebelum menyimpulkan.
6. Bila sumber berbeda atau belum cukup kuat, katakan dengan jelas.
7. Untuk tuduhan atau perkara hukum, bedakan secara tepat:
   diperiksa, saksi, terduga, tersangka, terdakwa, dan terpidana.
8. Jangan menyatakan seseorang bersalah tanpa dasar sumber yang jelas.
9. Gunakan nomor sumber seperti [1], [2], dan seterusnya.
10. Jawab ringkas, terstruktur, dan langsung ke inti.
11. Jangan tampilkan proses berpikir.

Format:
Jawaban
<ringkasan dalam Bahasa Indonesia>

Catatan verifikasi
<ketidakpastian atau perbedaan sumber, bila ada>
""".strip()

    result = subprocess.run(
        ["ollama", "run", CHAT_MODEL, prompt],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return fallback_summary(results)

    answer = result.stdout.strip()

    if not answer:
        return fallback_summary(results)

    return answer

def fallback_summary(results):
    lines = [
        "Saya menemukan sumber berikut, tetapi belum dapat "
        "menyintesisnya dengan model lokal:"
    ]

    for index, item in enumerate(results, 1):
        title = item.get("title") or "Tanpa judul"
        lines.append(f"{index}. {title}")

    return "\n".join(lines)

def format_sources(results):
    lines = ["", "Sumber:"]

    for index, item in enumerate(results, 1):
        title = item.get("title") or "Tanpa judul"
        date = item.get("published_date") or "Tanggal tidak tersedia"
        url = item.get("url") or ""

        lines.append(f"{index}. {title}")
        lines.append(f"   Tanggal: {date}")
        lines.append(f"   {url}")

    return "\n".join(lines)

def search(query):
    results = tavily_search(query)
    answer = synthesize(query, results)
    final = answer + "\n" + format_sources(results)
    return final, results

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
