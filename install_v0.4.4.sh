#!/bin/zsh
set -e

ROOT="$HOME/JiJiLite"
CORE="$ROOT/core"
MEMORY="$ROOT/memory"

cd "$ROOT"

echo "JiJi Lite v0.4.4 Installer"
echo "Membuat backup..."

mkdir -p "$ROOT/backups" "$CORE" "$MEMORY"
STAMP=$(date +"%Y%m%d-%H%M%S")
tar --exclude="./backups" --exclude="./cache" --exclude="./logs" \
  -czf "$ROOT/backups/pre-v0.4.4-$STAMP.tar.gz" -C "$ROOT" .

cat > "$CORE/memory.py" <<'PY'
import json
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
MEMORY_DIR = ROOT / "memory"
SESSION_FILE = MEMORY_DIR / "session.json"
MAX_MESSAGES = 12

def empty_session():
    return {
        "topic": "",
        "last_query": "",
        "last_answer": "",
        "last_mode": "",
        "history": [],
    }

def load():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSION_FILE.exists():
        return empty_session()
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        return {**empty_session(), **data}
    except (json.JSONDecodeError, OSError):
        return empty_session()

def save(data):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    data["history"] = data.get("history", [])[-MAX_MESSAGES:]
    SESSION_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def clear():
    save(empty_session())

def remember(user, answer, mode, effective_query=None):
    data = load()
    query = effective_query or user
    data["topic"] = query
    data["last_query"] = query
    data["last_answer"] = answer
    data["last_mode"] = mode
    data["history"].append({"role": "user", "content": user})
    data["history"].append({"role": "assistant", "content": answer})
    save(data)
PY

cat > "$CORE/web.py" <<'PY'
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
PY

cat > "$CORE/router.py" <<'PY'
import subprocess
from core.memory import load, remember
from core.web import search

CHAT_MODEL = "gemma3:4b"

WEB_TERMS = (
    "berita", "hari ini", "terbaru", "sekarang", "update",
    "cari", "search", "sesrch", "web", "website", "internet",
    "browsing", "cek online", "referensi", "sumber",
    "harga", "saham", "cuaca", "gempa", "presiden", "menteri",
    "siapa menjabat", "2026",
)

IDENTITY_PREFIXES = (
    "siapa ", "siapakah ", "siapa itu ", "siapakah itu ",
    "profil ", "biodata ",
)

FOLLOW_UPS = (
    "kurang akurat", "tidak akurat", "salah", "cek lagi",
    "coba cek lagi", "verifikasi lagi", "yang tadi",
    "maksud saya", "lebih rinci", "jelaskan lagi",
)

FALLBACK_TOKEN = "WEB_SEARCH_NEEDED"

def normalize(text):
    return " ".join(text.lower().strip().split())

def is_follow_up(prompt):
    text = normalize(prompt)
    return any(x in text for x in FOLLOW_UPS)

def contextualize(prompt, session):
    if is_follow_up(prompt) and session.get("last_query"):
        return (
            f"Verifikasi ulang secara akurat: {session['last_query']}. "
            f"Tanggapan pengguna: {prompt}. "
            "Gunakan sumber kredibel dan jangan mengarang."
        )
    return prompt

def classify(prompt, session=None):
    session = session or {}
    text = normalize(prompt)

    if is_follow_up(prompt) and session.get("last_query"):
        return "WEB" if session.get("last_mode") == "WEB" else "LOCAL"

    if text.startswith(IDENTITY_PREFIXES):
        return "WEB"

    if any(term in text for term in WEB_TERMS):
        return "WEB"

    return "LOCAL"

def run_local(prompt, session):
    history = session.get("history", [])[-6:]
    context = "\n".join(
        f"{item.get('role')}: {item.get('content')}"
        for item in history
    )

    system = f"""
Anda adalah JiJi Lite, asisten AI lokal berbahasa Indonesia.

ATURAN KEANDALAN:
1. Jangan mengarang nama, profil, jabatan, organisasi, tanggal, angka,
   kutipan, URL, referensi, peristiwa, atau biografi.
2. Bila fakta tidak benar-benar Anda ketahui, ambigu, berubah menurut
   waktu, atau memerlukan verifikasi, jawab hanya: {FALLBACK_TOKEN}
3. Jangan mengaku telah membuka internet apabila belum melakukan web search.
4. Bedakan fakta, perkiraan, dan opini.
5. Jawab singkat, jelas, dan langsung ke inti.
6. Jangan menampilkan proses berpikir internal.

Konteks percakapan:
{context}
""".strip()

    result = subprocess.run(
        [
            "ollama", "run", CHAT_MODEL,
            f"{system}\n\nPertanyaan pengguna: {prompt}",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return FALLBACK_TOKEN

    answer = result.stdout.strip()
    if not answer:
        return FALLBACK_TOKEN
    return answer

def handle(prompt):
    session = load()
    effective_query = contextualize(prompt, session)
    mode = classify(prompt, session)

    if mode == "WEB":
        print("🌐 Web Search\n")
        try:
            answer, _ = search(effective_query)
        except Exception as error:
            answer = f"Web Search gagal: {error}"
        print(answer)
        remember(prompt, answer, "WEB", effective_query)
        return answer

    answer = run_local(effective_query, session)

    if FALLBACK_TOKEN.lower() in answer.lower():
        print("🌐 Informasi perlu diverifikasi. Mencari di web...\n")
        try:
            answer, _ = search(effective_query)
            mode = "WEB"
        except Exception as error:
            answer = (
                "Saya belum dapat memastikan jawabannya dan verifikasi web "
                f"gagal: {error}"
            )
            mode = "LOCAL"
    else:
        print("💬 Chat\n")

    print(answer)
    remember(prompt, answer, mode, effective_query)
    return answer
PY

cat > "$ROOT/main.py" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
sys.path.insert(0, str(ROOT))

from core.memory import clear, load
from core.router import handle

VERSION = (ROOT / "version").read_text().strip()

def show_help():
    print("Perintah:")
    print("/help     Bantuan")
    print("/new      Mulai percakapan baru")
    print("/memory   Lihat konteks aktif")
    print("/status   Status sistem")
    print("/version  Versi JiJi")
    print("/doctor   Diagnostik")
    print("/clear    Bersihkan layar")
    print("/exit     Keluar")

def internal(command):
    cmd = command.strip().lower()

    if cmd == "/help":
        show_help()
    elif cmd == "/new":
        clear()
        print("Percakapan baru dimulai.")
    elif cmd == "/memory":
        session = load()
        print("Topik :", session.get("last_query") or "Belum ada")
        print("Mode  :", session.get("last_mode") or "-")
    elif cmd == "/status":
        print(f"JiJi Lite v{VERSION}")
        print("Chat   : gemma3:4b")
        print("Web    : Tavily")
        print("Memory : Active")
        print("Router : Reliability Layer")
    elif cmd == "/version":
        print(f"JiJi Lite v{VERSION}")
    elif cmd == "/doctor":
        subprocess.run(["python3", str(ROOT / "core" / "doctor.py")])
    elif cmd == "/clear":
        print("\033c", end="")
    else:
        return False
    return True

def process(prompt):
    if prompt.startswith("/") and internal(prompt):
        return
    handle(prompt)

if len(sys.argv) > 1:
    process(" ".join(sys.argv[1:]))
    raise SystemExit

print(f"╭─ JiJi Lite v{VERSION} ─────────────────────╮")
print("│ Status : Ready                            │")
print("╰───────────────────────────────────────────╯")
print()
print("Apa yang ingin Anda lakukan?")
print()

while True:
    try:
        question = input("JiJi ❯ ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSampai jumpa.")
        break

    if not question:
        continue
    if question.lower() in ("/exit", "exit", "quit", "keluar"):
        print("Sampai jumpa.")
        break

    process(question)
    print()
PY

cat > "$CORE/selftest.py" <<'PY'
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
PY

echo "0.4.4" > "$ROOT/version"

cat >> "$ROOT/CHANGELOG.md" <<'EOF'

## v0.4.4
- Conversation memory
- Context-aware follow-up
- Smart LOCAL/WEB router
- Automatic web fallback
- Reliability and anti-hallucination rules
- Internal commands restored
- Deterministic router self-tests
EOF

chmod +x "$ROOT/main.py" "$CORE/web.py" "$CORE/selftest.py"

echo
echo "Menjalankan validasi sintaks..."
python3 -m py_compile \
  "$ROOT/main.py" \
  "$CORE/memory.py" \
  "$CORE/router.py" \
  "$CORE/web.py" \
  "$CORE/selftest.py"

echo
echo "Menjalankan self-test..."
cd "$ROOT"
python3 -m core.selftest

echo
echo "Menjalankan doctor..."
python3 "$CORE/doctor.py"

echo
echo "JiJi Lite v0.4.4 berhasil dipasang."
