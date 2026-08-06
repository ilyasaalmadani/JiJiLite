#!/bin/zsh
set -e

ROOT="$HOME/JiJiLite"
CORE="$ROOT/core"
BACKUPS="$ROOT/backups"

cd "$ROOT"
mkdir -p "$CORE" "$BACKUPS" "$ROOT/memory"

echo "╭─ JiJi Lite v0.4.9 ─────────────────────╮"
echo "│ Conversation Intelligence              │"
echo "╰────────────────────────────────────────╯"
echo

STAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP="$BACKUPS/pre-v0.4.9-$STAMP.tar.gz"

echo "[1/7] Membuat backup..."

tar \
  --exclude="./backups" \
  --exclude="./cache" \
  --exclude="./logs" \
  --exclude="./.git" \
  -czf "$BACKUP" \
  -C "$ROOT" .

echo "✓ Backup selesai"

cat > "$CORE/memory.py" <<'PY'
import json
from pathlib import Path
from core.config import CONFIG

ROOT = Path.home() / "JiJiLite"
MEMORY_DIR = ROOT / "memory"
SESSION_FILE = MEMORY_DIR / "session.json"

MAX_MESSAGES = int(CONFIG.get("max_memory_messages", 12))
MAX_TEXT = 1600

def clean(value):
    return str(value or "").strip()[:MAX_TEXT]

def empty_session():
    return {
        "topic": "",
        "subtopic": "",
        "goal": "",
        "last_intent": "",
        "last_user_query": "",
        "last_effective_query": "",
        "last_answer": "",
        "last_mode": "",
        "conversation_summary": "",
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

        return {**empty_session(), **data}

    except (json.JSONDecodeError, OSError):
        return empty_session()

def save(data):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    output = {**empty_session(), **data}

    for key in (
        "topic",
        "subtopic",
        "goal",
        "last_intent",
        "last_user_query",
        "last_effective_query",
        "last_answer",
        "conversation_summary",
    ):
        output[key] = clean(output.get(key))

    history = []

    for item in output.get("history", [])[-MAX_MESSAGES:]:
        history.append({
            "role": item.get("role", ""),
            "content": clean(item.get("content")),
            "mode": item.get("mode", ""),
        })

    output["history"] = history

    SESSION_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def clear():
    save(empty_session())

def remember(
    user,
    answer,
    mode,
    effective_query=None,
    topic=None,
    subtopic=None,
    goal=None,
    intent=None,
):
    data = load()

    if topic:
        data["topic"] = clean(topic)

    if subtopic:
        data["subtopic"] = clean(subtopic)

    if goal:
        data["goal"] = clean(goal)

    if intent:
        data["last_intent"] = clean(intent)

    data["last_user_query"] = clean(user)
    data["last_effective_query"] = clean(
        effective_query or user
    )
    data["last_answer"] = clean(answer)
    data["last_mode"] = mode

    data["history"].append({
        "role": "user",
        "content": clean(user),
    })

    data["history"].append({
        "role": "assistant",
        "content": clean(answer),
        "mode": mode,
    })

    save(data)
PY

cat > "$CORE/conversation.py" <<'PY'
import re

SHORT_CONFIRMATIONS = {
    "ya",
    "iya",
    "yap",
    "oke",
    "ok",
    "baik",
    "betul",
    "benar",
    "lanjut",
    "terus",
    "silakan",
    "boleh",
}

FOLLOW_UP_MARKERS = (
    "worth it",
    "layak",
    "kenapa",
    "mengapa",
    "bagaimana",
    "gimana",
    "berapa",
    "yakin",
    "masa",
    "benarkah",
    "apa risikonya",
    "apa keuntungannya",
    "apa kekurangannya",
    "lebih rinci",
    "jelaskan lagi",
    "lanjutkan",
    "terus bagaimana",
    "kalau begitu",
    "kalau iya",
    "kalau tidak",
)

CORRECTION_MARKERS = (
    "kurang akurat",
    "tidak akurat",
    "belum akurat",
    "salah",
    "cek lagi",
    "verifikasi lagi",
    "coba cari lagi",
    "mana buktinya",
    "apa sumbernya",
)

BROAD_TOPIC_PATTERNS = (
    r"^saya (ingin|mau|butuh) (membahas|informasi tentang|tahu tentang) (.+)$",
    r"^jelaskan tentang (.+)$",
    r"^informasi tentang (.+)$",
    r"^(.{3,40})\?$",
)

def normalize(text):
    return " ".join(
        str(text or "").lower().strip().split()
    )

def extract_topic(prompt):
    text = normalize(prompt)

    for pattern in BROAD_TOPIC_PATTERNS:
        match = re.match(pattern, text)

        if match:
            topic = match.groups()[-1]
            return topic.strip(" ?.")

    if len(text.split()) <= 5:
        blocked = SHORT_CONFIRMATIONS | {
            "kenapa",
            "mengapa",
            "bagaimana",
            "gimana",
            "worth it",
        }

        if text not in blocked:
            return text.strip(" ?.")

    return ""

def is_confirmation(prompt):
    return normalize(prompt) in SHORT_CONFIRMATIONS

def is_correction(prompt):
    text = normalize(prompt)
    return any(marker in text for marker in CORRECTION_MARKERS)

def is_follow_up(prompt):
    text = normalize(prompt)

    if is_confirmation(prompt) or is_correction(prompt):
        return True

    if len(text.split()) <= 8:
        return any(marker in text for marker in FOLLOW_UP_MARKERS)

    return False

def detect_intent(prompt):
    text = normalize(prompt)

    if is_confirmation(prompt):
        return "CONFIRM"

    if is_correction(prompt):
        return "VERIFY"

    if "worth it" in text or "layak" in text:
        return "EVALUATE"

    if text.startswith(("kenapa", "mengapa")):
        return "EXPLAIN_CAUSE"

    if text.startswith(("bagaimana", "gimana")):
        return "EXPLAIN_METHOD"

    if "risiko" in text:
        return "RISK"

    if "keuntungan" in text or "manfaat" in text:
        return "BENEFIT"

    return "ASK"

def needs_clarification(prompt, session):
    text = normalize(prompt)

    if is_confirmation(prompt):
        return not bool(session.get("topic"))

    vague = (
        len(text.split()) <= 2
        and not is_follow_up(prompt)
        and not session.get("topic")
    )

    return vague

def build_effective_query(prompt, session):
    text = normalize(prompt)
    topic = session.get("topic", "").strip()
    goal = session.get("goal", "").strip()
    last_query = session.get("last_user_query", "").strip()

    if is_confirmation(prompt):
        if topic:
            return (
                f"Jelaskan lebih lanjut mengenai {topic}. "
                f"Fokus tujuan pengguna: {goal or 'memahami topik tersebut'}."
            )

        return prompt

    if is_correction(prompt):
        base = topic or last_query

        if base:
            return (
                f"Verifikasi ulang informasi mengenai {base}. "
                f"Masukan pengguna: {prompt}. "
                "Gunakan sumber yang lebih kuat dan jangan mengarang."
            )

    if is_follow_up(prompt) and topic:
        return (
            f"Topik percakapan: {topic}. "
            f"Pertanyaan lanjutan pengguna: {prompt}. "
            f"Tujuan percakapan: {goal or 'memberikan jawaban yang relevan'}."
        )

    return prompt

def update_state(prompt, session):
    topic = session.get("topic", "")
    extracted = extract_topic(prompt)

    if extracted and not is_follow_up(prompt):
        topic = extracted

    intent = detect_intent(prompt)

    goal = session.get("goal", "")

    if intent == "EVALUATE":
        goal = f"menilai kelayakan {topic or prompt}"

    elif intent == "RISK":
        goal = f"memahami risiko {topic or prompt}"

    elif intent == "BENEFIT":
        goal = f"memahami manfaat {topic or prompt}"

    elif not goal and topic:
        goal = f"memahami {topic}"

    return {
        "topic": topic,
        "subtopic": normalize(prompt) if topic else "",
        "goal": goal,
        "intent": intent,
    }
PY

cat > "$CORE/router.py" <<'PY'
from core.chat import FALLBACK_TOKEN, ask_local
from core.conversation import (
    build_effective_query,
    is_confirmation,
    is_correction,
    is_follow_up,
    needs_clarification,
    update_state,
)
from core.memory import load, remember
from core.web import search

WEB_TERMS = (
    "berita",
    "hari ini",
    "terbaru",
    "sekarang",
    "terkini",
    "update",
    "cari",
    "search",
    "sesrch",
    "web",
    "website",
    "internet",
    "online",
    "referensi",
    "sumber",
    "harga",
    "saham",
    "cuaca",
    "gempa",
    "presiden",
    "menteri",
    "gubernur",
    "bupati",
    "wali kota",
    "pemilu",
    "pilkada",
    "2025",
    "2026",
)

IDENTITY_PREFIXES = (
    "siapa ",
    "siapakah ",
    "siapa itu ",
    "siapakah itu ",
    "profil ",
    "biodata ",
)

def normalize(text):
    return " ".join(text.lower().strip().split())

def classify(prompt, session=None):
    session = session or {}
    text = normalize(prompt)

    if is_correction(prompt):
        return "WEB"

    if is_follow_up(prompt) and session.get("last_mode") == "WEB":
        return "WEB"

    if text.startswith(IDENTITY_PREFIXES):
        return "WEB"

    if any(term in text for term in WEB_TERMS):
        return "WEB"

    return "LOCAL"

def clarification_message(prompt, session):
    topic = session.get("topic", "")

    if is_confirmation(prompt) and not topic:
        return (
            "Saya belum memiliki topik yang cukup jelas. "
            "Silakan sebutkan topik yang ingin Anda lanjutkan."
        )

    return (
        "Topiknya masih cukup luas. Anda ingin membahas "
        "pengertian, peluang, modal, risiko, strategi, "
        "atau contoh penerapannya?"
    )

def answer_web(
    prompt,
    effective_query,
    state,
):
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

    remember(
        prompt,
        answer,
        mode,
        effective_query,
        topic=state["topic"],
        subtopic=state["subtopic"],
        goal=state["goal"],
        intent=state["intent"],
    )

    return answer

def handle(prompt):
    session = load()
    state = update_state(prompt, session)

    session_with_state = {
        **session,
        **state,
    }

    if needs_clarification(prompt, session_with_state):
        answer = clarification_message(
            prompt,
            session_with_state,
        )

        print("🧭 Klarifikasi\n")
        print(answer)

        remember(
            prompt,
            answer,
            "CLARIFY",
            prompt,
            topic=state["topic"],
            subtopic=state["subtopic"],
            goal=state["goal"],
            intent=state["intent"],
        )

        return answer

    effective_query = build_effective_query(
        prompt,
        session_with_state,
    )

    mode = classify(
        effective_query,
        session_with_state,
    )

    if mode == "WEB":
        return answer_web(
            prompt,
            effective_query,
            state,
        )

    answer = ask_local(
        effective_query,
        session.get("history", []),
    )

    if FALLBACK_TOKEN.lower() in answer.lower():
        print(
            "🌐 Pengetahuan lokal belum cukup. "
            "Melakukan verifikasi web...\n"
        )

        return answer_web(
            prompt,
            effective_query,
            state,
        )

    print("💬 Chat\n")
    print(answer)

    remember(
        prompt,
        answer,
        "LOCAL",
        effective_query,
        topic=state["topic"],
        subtopic=state["subtopic"],
        goal=state["goal"],
        intent=state["intent"],
    )

    return answer
PY

cat > "$CORE/conversation_test.py" <<'PY'
#!/usr/bin/env python3

from core.conversation import (
    build_effective_query,
    detect_intent,
    extract_topic,
    is_confirmation,
    is_follow_up,
    update_state,
)
from core.memory import empty_session
from core.router import classify

passed = 0

def check(condition, label):
    global passed

    if not condition:
        raise AssertionError(label)

    passed += 1
    print(f"✓ {label}")

check(
    extract_topic(
        "Saya butuh informasi tentang bisnis AI"
    ) == "bisnis ai",
    "Topik bisnis AI terdeteksi",
)

check(
    is_confirmation("ya"),
    "Jawaban ya dikenali",
)

check(
    is_confirmation("iya"),
    "Jawaban iya dikenali",
)

check(
    is_follow_up("apakah worth it"),
    "Worth it dikenali sebagai follow-up",
)

check(
    detect_intent("apakah worth it") == "EVALUATE",
    "Intent evaluasi terdeteksi",
)

session = empty_session()
session["topic"] = "bisnis AI"
session["goal"] = "memahami bisnis AI"
session["last_mode"] = "LOCAL"
session["last_user_query"] = (
    "Saya butuh informasi tentang bisnis AI"
)

effective = build_effective_query(
    "apakah worth it",
    session,
)

check(
    "bisnis AI" in effective,
    "Query follow-up membawa topik",
)

check(
    "worth it" in effective,
    "Query follow-up membawa pertanyaan",
)

confirmation = build_effective_query(
    "ya",
    session,
)

check(
    "bisnis AI" in confirmation,
    "Konfirmasi membawa topik",
)

state = update_state(
    "apakah worth it",
    session,
)

check(
    state["topic"] == "bisnis AI",
    "State mempertahankan topik",
)

check(
    state["intent"] == "EVALUATE",
    "State menyimpan intent",
)

check(
    classify(
        "berita bisnis AI hari ini",
        session,
    ) == "WEB",
    "Berita bisnis AI memakai web",
)

check(
    classify(
        effective,
        session,
    ) == "LOCAL",
    "Evaluasi umum dapat memakai lokal",
)

print()
print(
    f"Semua {passed} Conversation Intelligence tests berhasil."
)
PY

python3 - <<'PY'
from pathlib import Path

path = Path.home() / "JiJiLite/main.py"
text = path.read_text(encoding="utf-8")

old = '''        print("Topik :", session.get("last_user_query") or "Belum ada")
        print("Mode  :", session.get("last_mode") or "-")
        print("Pesan :", len(session.get("history", [])))'''

new = '''        print("Topik    :", session.get("topic") or "Belum ada")
        print("Subtopik :", session.get("subtopic") or "-")
        print("Tujuan   :", session.get("goal") or "-")
        print("Intent   :", session.get("last_intent") or "-")
        print("Mode     :", session.get("last_mode") or "-")
        print("Pesan    :", len(session.get("history", [])))'''

if old in text:
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
PY

echo "0.4.9" > "$ROOT/version"

cat >> "$ROOT/CHANGELOG.md" <<'EOF'

## v0.4.9
- Conversation Intelligence
- Topic tracking
- Intent detection
- Contextual query rewriting
- Short confirmation handling
- Smart follow-up resolution
- Clarification mode
- Structured conversation state
- Expanded conversation tests
EOF

chmod +x "$CORE/conversation_test.py"

echo
echo "[2/7] Memeriksa sintaks..."

python3 -m py_compile \
  "$ROOT/main.py" \
  "$CORE/memory.py" \
  "$CORE/conversation.py" \
  "$CORE/router.py" \
  "$CORE/conversation_test.py"

echo "✓ Sintaks valid"

echo
echo "[3/7] Menjalankan Conversation Tests..."

python3 -m core.conversation_test

echo
echo "[4/7] Menjalankan Router Tests..."

python3 -m core.selftest

echo
echo "[5/7] Menjalankan Quality Gate..."

if [ -f "$CORE/quality_test.py" ]; then
  python3 -m core.quality_test
fi

echo
echo "[6/7] Menjalankan System Doctor..."

python3 "$CORE/doctor.py"

echo
echo "[7/7] Instalasi selesai"

echo
echo "╭─ Update Berhasil ──────────────────────╮"
echo "│ JiJi Lite v0.4.9                      │"
echo "│ Conversation Intelligence Active      │"
echo "╰────────────────────────────────────────╯"
