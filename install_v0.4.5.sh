#!/bin/zsh
set -e

ROOT="$HOME/JiJiLite"
CORE="$ROOT/core"
MEMORY="$ROOT/memory"
BACKUPS="$ROOT/backups"

cd "$ROOT"

echo "╭─ JiJi Lite v0.4.5 Installer ───────────╮"
echo "│ Reliable Conversation Edition          │"
echo "╰────────────────────────────────────────╯"
echo

mkdir -p "$CORE" "$MEMORY" "$BACKUPS"

STAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILE="$BACKUPS/pre-v0.4.5-$STAMP.tar.gz"

echo "[1/8] Membuat backup..."

tar \
  --exclude="./backups" \
  --exclude="./cache" \
  --exclude="./logs" \
  --exclude="./.git" \
  -czf "$BACKUP_FILE" \
  -C "$ROOT" .

echo "✓ Backup: $BACKUP_FILE"

cat > "$CORE/config.py" <<'PY'
import json
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
CONFIG_FILE = ROOT / "config" / "router.json"

DEFAULT_CONFIG = {
    "chat_model": "gemma3:4b",
    "fast_model": "llama3.2:3b",
    "max_memory_messages": 12,
    "web_max_results": 5,
}

def load_config():
    config = dict(DEFAULT_CONFIG)

    if CONFIG_FILE.exists():
        try:
            saved = json.loads(
                CONFIG_FILE.read_text(encoding="utf-8")
            )
            if isinstance(saved, dict):
                config.update(saved)
        except (json.JSONDecodeError, OSError):
            pass

    return config

CONFIG = load_config()
PY

cat > "$CORE/memory.py" <<'PY'
import json
from pathlib import Path
from core.config import CONFIG

ROOT = Path.home() / "JiJiLite"
MEMORY_DIR = ROOT / "memory"
SESSION_FILE = MEMORY_DIR / "session.json"
MAX_MESSAGES = int(CONFIG.get("max_memory_messages", 12))

def empty_session():
    return {
        "topic": "",
        "last_user_query": "",
        "last_effective_query": "",
        "last_answer": "",
        "last_mode": "",
        "history": [],
    }

def load():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    if not SESSION_FILE.exists():
        return empty_session()

    try:
        data = json.loads(
            SESSION_FILE.read_text(encoding="utf-8")
        )

        if not isinstance(data, dict):
            return empty_session()

        # Migrasi memory versi lama.
        if not data.get("last_user_query"):
            data["last_user_query"] = data.get("last_query", "")

        return {**empty_session(), **data}

    except (json.JSONDecodeError, OSError):
        return empty_session()

def save(data):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    history = data.get("history", [])
    data["history"] = history[-MAX_MESSAGES:]

    SESSION_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def clear():
    save(empty_session())

def remember(user, answer, mode, effective_query=None):
    data = load()

    data["topic"] = user
    data["last_user_query"] = user
    data["last_effective_query"] = effective_query or user
    data["last_answer"] = answer
    data["last_mode"] = mode

    data["history"].append({
        "role": "user",
        "content": user,
    })

    data["history"].append({
        "role": "assistant",
        "content": answer,
        "mode": mode,
    })

    save(data)
PY

cat > "$CORE/chat.py" <<'PY'
import subprocess
from core.config import CONFIG

CHAT_MODEL = CONFIG.get("chat_model", "gemma3:4b")
FALLBACK_TOKEN = "WEB_SEARCH_NEEDED"

SYSTEM_PROMPT = """
Anda adalah JiJi Lite, asisten AI lokal berbahasa Indonesia.

ATURAN MUTLAK:
1. Selalu jawab dalam Bahasa Indonesia.
2. Jangan mengarang nama, jabatan, organisasi, tanggal, angka,
   berita, kutipan, URL, sumber, biografi, atau peristiwa.
3. Jangan membuat referensi atau tautan palsu.
4. Bila informasi bersifat terbaru, identitas seseorang tidak dikenal,
   fakta meragukan, atau memerlukan verifikasi, jawab hanya:
   WEB_SEARCH_NEEDED
5. Bedakan fakta, analisis, perkiraan, dan opini.
6. Jangan mengaku sudah mencari internet apabila belum melakukannya.
7. Jangan tampilkan proses berpikir internal.
8. Jawab singkat, jelas, dan langsung ke inti.
""".strip()

def ask_local(prompt, history=None):
    history = history or []

    context_lines = []
    for item in history[-6:]:
        role = item.get("role", "")
        content = item.get("content", "")
        context_lines.append(f"{role}: {content}")

    context = "\n".join(context_lines)

    full_prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Konteks percakapan:\n{context}\n\n"
        f"Pertanyaan pengguna:\n{prompt}"
    )

    result = subprocess.run(
        ["ollama", "run", CHAT_MODEL, full_prompt],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return FALLBACK_TOKEN

    answer = result.stdout.strip()

    if not answer:
        return FALLBACK_TOKEN

    return answer
PY

cat > "$CORE/web.py" <<'PY'
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
PY

cat > "$CORE/router.py" <<'PY'
from core.chat import FALLBACK_TOKEN, ask_local
from core.memory import load, remember
from core.web import search

WEB_TERMS = (
    "berita", "hari ini", "terbaru", "sekarang", "update",
    "cari", "search", "sesrch", "telusuri", "web", "website",
    "internet", "browsing", "online", "referensi", "sumber",
    "harga", "saham", "cuaca", "gempa", "presiden", "menteri",
    "gubernur", "bupati", "wali kota", "dpr", "pemilu",
    "pilkada", "2025", "2026",
)

IDENTITY_PREFIXES = (
    "siapa ",
    "siapakah ",
    "siapa itu ",
    "siapakah itu ",
    "profil ",
    "biodata ",
)

FOLLOW_UP_TERMS = (
    "kurang akurat",
    "tidak akurat",
    "belum akurat",
    "salah",
    "cek lagi",
    "coba cek lagi",
    "verifikasi lagi",
    "telusuri lagi",
    "yang tadi",
    "maksud saya",
    "lebih rinci",
    "jelaskan lagi",
    "apa sumbernya",
    "dari mana sumbernya",
)

CURRENT_FACT_TERMS = (
    "saat ini",
    "sekarang",
    "terkini",
    "terbaru",
    "masih menjabat",
    "menjabat apa",
    "siapa menjabat",
)

def normalize(text):
    return " ".join(text.lower().strip().split())

def is_follow_up(prompt):
    text = normalize(prompt)
    return any(term in text for term in FOLLOW_UP_TERMS)

def contextualize(prompt, session):
    if not is_follow_up(prompt):
        return prompt

    last_user_query = session.get("last_user_query", "")

    if not last_user_query:
        return prompt

    return (
        f"Verifikasi ulang pertanyaan berikut secara lebih akurat: "
        f"{last_user_query}. "
        f"Masukan lanjutan pengguna: {prompt}. "
        "Bandingkan beberapa sumber kredibel dan jelaskan "
        "jika terdapat ketidakpastian."
    )

def classify(prompt, session=None):
    session = session or {}
    text = normalize(prompt)

    if is_follow_up(prompt):
        if session.get("last_mode") == "WEB":
            return "WEB"
        if session.get("last_user_query"):
            return "LOCAL"

    if text.startswith(IDENTITY_PREFIXES):
        return "WEB"

    if any(term in text for term in CURRENT_FACT_TERMS):
        return "WEB"

    if any(term in text for term in WEB_TERMS):
        return "WEB"

    return "LOCAL"

def answer_web(prompt, effective_query):
    print("🌐 Web Search\n")

    try:
        answer, _ = search(effective_query)
        mode = "WEB"
    except Exception as error:
        answer = (
            "Saya belum dapat melakukan verifikasi web. "
            f"Detail: {error}"
        )
        mode = "ERROR"

    print(answer)
    remember(prompt, answer, mode, effective_query)
    return answer

def handle(prompt):
    session = load()
    effective_query = contextualize(prompt, session)
    mode = classify(prompt, session)

    if mode == "WEB":
        return answer_web(prompt, effective_query)

    answer = ask_local(
        effective_query,
        session.get("history", []),
    )

    if FALLBACK_TOKEN.lower() in answer.lower():
        print(
            "🌐 Pengetahuan lokal belum cukup. "
            "Melakukan verifikasi web...\n"
        )
        return answer_web(prompt, effective_query)

    print("💬 Chat\n")
    print(answer)

    remember(
        prompt,
        answer,
        "LOCAL",
        effective_query,
    )

    return answer
PY

cat > "$ROOT/main.py" <<'PY'
#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
sys.path.insert(0, str(ROOT))

from core.config import CONFIG
from core.memory import clear, load
from core.router import handle

VERSION = (ROOT / "version").read_text().strip()

def show_help():
    print("Perintah JiJi:")
    print("/help      Tampilkan bantuan")
    print("/new       Mulai percakapan baru")
    print("/memory    Lihat konteks aktif")
    print("/status    Lihat status sistem")
    print("/version   Lihat versi")
    print("/doctor    Jalankan pemeriksaan")
    print("/clear     Bersihkan layar")
    print("/exit      Keluar")

def run_internal(command):
    cmd = command.strip().lower()

    if cmd in ("/help", "help"):
        show_help()

    elif cmd == "/new":
        clear()
        print("Percakapan baru dimulai.")

    elif cmd == "/memory":
        session = load()
        print(
            "Topik :",
            session.get("last_user_query") or "Belum ada",
        )
        print(
            "Mode  :",
            session.get("last_mode") or "-",
        )
        print(
            "Pesan :",
            len(session.get("history", [])),
        )

    elif cmd == "/status":
        print(f"JiJi Lite v{VERSION}")
        print(
            "Chat   :",
            CONFIG.get("chat_model", "gemma3:4b"),
        )
        print("Web    : Tavily + Indonesian Synthesis")
        print("Memory : Active")
        print("Router : Smart Fallback")
        print("Safety : Reliability Layer")

    elif cmd == "/version":
        print(f"JiJi Lite v{VERSION}")

    elif cmd == "/doctor":
        subprocess.run([
            "python3",
            str(ROOT / "core" / "doctor.py"),
        ])

    elif cmd == "/clear":
        print("\033c", end="")

    else:
        return False

    return True

def process(prompt):
    if run_internal(prompt):
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

    if question.lower() in (
        "/exit", "exit", "quit", "keluar"
    ):
        print("Sampai jumpa.")
        break

    process(question)
    print()
PY

cat > "$CORE/doctor.py" <<'PY'
#!/usr/bin/env python3

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path.home() / "JiJiLite"

checks = []

def check(name, condition):
    checks.append((name, bool(condition)))

check("Python", shutil.which("python3"))
check("Ollama", shutil.which("ollama"))
check("Git", shutil.which("git"))
check("Version", (ROOT / "version").exists())
check("Main", (ROOT / "main.py").exists())
check("Router", (ROOT / "core/router.py").exists())
check("Chat", (ROOT / "core/chat.py").exists())
check("Web", (ROOT / "core/web.py").exists())
check("Memory", (ROOT / "core/memory.py").exists())
check(
    "Tavily Config",
    (ROOT / "config/tavily.conf").exists(),
)

try:
    result = subprocess.run(
        ["ollama", "list"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    check("Ollama Service", result.returncode == 0)
except OSError:
    check("Ollama Service", False)

try:
    session = ROOT / "memory/session.json"
    if session.exists():
        json.loads(session.read_text(encoding="utf-8"))
    check("Memory Database", True)
except (json.JSONDecodeError, OSError):
    check("Memory Database", False)

print("╭─ JiJi Lite System Doctor ──────────────╮")
for name, status in checks:
    symbol = "✓" if status else "✗"
    print(f"│ {symbol} {name:<35}│")
print("╰────────────────────────────────────────╯")

failed = [name for name, status in checks if not status]

if failed:
    print()
    print("System membutuhkan perhatian:")
    for item in failed:
        print("-", item)
    raise SystemExit(1)

print()
print("✓ System Healthy")
PY

cat > "$CORE/selftest.py" <<'PY'
#!/usr/bin/env python3

from core.memory import empty_session
from core.router import classify, contextualize

def expect(actual, expected, label):
    if actual != expected:
        raise AssertionError(
            f"{label}: {actual!r} != {expected!r}"
        )
    print(f"✓ {label}")

web_session = empty_session()
web_session["last_user_query"] = (
    "Siapakah Ilyas Akbar Almadani?"
)
web_session["last_mode"] = "WEB"

local_session = empty_session()
local_session["last_user_query"] = (
    "Jelaskan pengertian demokrasi"
)
local_session["last_mode"] = "LOCAL"

expect(
    classify("Apa itu demokrasi?"),
    "LOCAL",
    "Pertanyaan umum memakai lokal",
)

expect(
    classify("Berita politik hari ini"),
    "WEB",
    "Berita memakai web",
)

expect(
    classify("Siapakah Juliyatmono?"),
    "WEB",
    "Identitas memakai web",
)

expect(
    classify("Cari di website"),
    "WEB",
    "Instruksi web terdeteksi",
)

expect(
    classify("Kurang akurat", web_session),
    "WEB",
    "Follow-up web mempertahankan mode",
)

expect(
    classify("Jelaskan lagi", local_session),
    "LOCAL",
    "Follow-up lokal mempertahankan mode",
)

rewritten = contextualize(
    "Kurang akurat",
    web_session,
)

if "Ilyas Akbar Almadani" not in rewritten:
    raise AssertionError(
        "Contextual follow-up kehilangan topik."
    )

print("✓ Follow-up membawa topik sebelumnya")
print()
print("Semua self-test v0.4.5 berhasil.")
PY

echo "0.4.5" > "$ROOT/version"

cat >> "$ROOT/CHANGELOG.md" <<'EOF'

## v0.4.5
- Indonesian Web Synthesis
- Multi-source web summarization
- Stronger anti-hallucination policy
- Improved contextual memory
- Fixed recursive follow-up queries
- Smart local-to-web fallback
- Expanded internal commands
- Expanded System Doctor
- Full router self-test
EOF

chmod +x \
  "$ROOT/main.py" \
  "$CORE/web.py" \
  "$CORE/doctor.py" \
  "$CORE/selftest.py"

echo
echo "[2/8] Memeriksa sintaks Python..."

python3 -m py_compile \
  "$ROOT/main.py" \
  "$CORE/config.py" \
  "$CORE/memory.py" \
  "$CORE/chat.py" \
  "$CORE/web.py" \
  "$CORE/router.py" \
  "$CORE/doctor.py" \
  "$CORE/selftest.py"

echo "✓ Sintaks valid"

echo
echo "[3/8] Menjalankan self-test router..."

cd "$ROOT"
python3 -m core.selftest

echo
echo "[4/8] Menjalankan System Doctor..."

python3 "$CORE/doctor.py"

echo
echo "[5/8] Memeriksa model lokal..."

ollama list | grep -q "gemma3:4b" || {
  echo "✗ Model gemma3:4b tidak ditemukan."
  exit 1
}

echo "✓ gemma3:4b tersedia"

echo
echo "[6/8] Memeriksa konfigurasi Tavily..."

grep -q '^TAVILY_API_KEY=' "$ROOT/config/tavily.conf" || {
  echo "✗ API key Tavily tidak ditemukan."
  exit 1
}

echo "✓ Tavily terkonfigurasi"

echo
echo "[7/8] Membersihkan bytecode lama..."

find "$ROOT" \
  -type d \
  -name "__pycache__" \
  -prune \
  -exec rm -rf {} + 2>/dev/null || true

echo "✓ Cache Python dibersihkan"

echo
echo "[8/8] Instalasi selesai"

echo
echo "╭─ Update Berhasil ──────────────────────╮"
echo "│ JiJi Lite v0.4.5                      │"
echo "│ Indonesian Reliable Conversation      │"
echo "╰────────────────────────────────────────╯"
