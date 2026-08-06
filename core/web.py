#!/usr/bin/env python3
import json
import sys
import urllib.request
from pathlib import Path

config = Path.home() / "JiJiLite/config/tavily.conf"
if not config.exists():
    print("Web Search: konfigurasi Tavily tidak ditemukan.")
    sys.exit(1)

key = ""
for line in config.read_text().splitlines():
    if line.startswith("TAVILY_API_KEY="):
        key = line.split("=", 1)[1].strip().strip(chr(39)).strip(chr(34))

if not key:
    print("Web Search: API key Tavily kosong.")
    sys.exit(1)

query = " ".join(sys.argv[1:]).strip()
payload = json.dumps({
    "query": query,
    "topic": "news",
    "search_depth": "basic",
    "max_results": 5,
    "include_answer": True
}).encode()

request = urllib.request.Request(
    "https://api.tavily.com/search",
    data=payload,
    headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json"
    }
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
except Exception as error:
    print("Web Search gagal:", error)
    sys.exit(1)

print("JiJi Web")
print()
answer = data.get("answer")
if answer:
    print(answer)
    print()

print("Sumber:")
for number, item in enumerate(data.get("results", []), 1):
    title = item.get("title", "Tanpa judul")
    date = item.get("published_date") or "Tanggal tidak tersedia"
    url = item.get("url", "")
    print(f"{number}. {title}")
    print(f"   Tanggal: {date}")
    print(f"   {url}")
