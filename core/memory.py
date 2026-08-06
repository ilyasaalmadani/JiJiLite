import json
from pathlib import Path
from core.config import CONFIG

ROOT = Path.home() / "JiJiLite"
MEMORY_DIR = ROOT / "memory"
SESSION_FILE = MEMORY_DIR / "session.json"
MAX_MESSAGES = int(CONFIG.get("max_memory_messages", 10))
MAX_ITEM_LENGTH = 1400

def empty_session():
    return {
        "topic": "",
        "last_user_query": "",
        "last_effective_query": "",
        "last_answer": "",
        "last_mode": "",
        "history": [],
    }

def clean_text(value):
    text = str(value or "").strip()
    return text[:MAX_ITEM_LENGTH]

def load():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    if not SESSION_FILE.exists():
        return empty_session()

    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return empty_session()
        return {**empty_session(), **data}
    except (json.JSONDecodeError, OSError):
        return empty_session()

def save(data):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    cleaned = {**empty_session(), **data}
    cleaned["topic"] = clean_text(cleaned.get("topic"))
    cleaned["last_user_query"] = clean_text(
        cleaned.get("last_user_query")
    )
    cleaned["last_effective_query"] = clean_text(
        cleaned.get("last_effective_query")
    )
    cleaned["last_answer"] = clean_text(
        cleaned.get("last_answer")
    )

    history = []
    for item in cleaned.get("history", [])[-MAX_MESSAGES:]:
        history.append({
            "role": item.get("role", ""),
            "content": clean_text(item.get("content")),
            "mode": item.get("mode", ""),
        })

    cleaned["history"] = history

    SESSION_FILE.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def clear():
    save(empty_session())

def remember(user, answer, mode, effective_query=None):
    data = load()

    data["topic"] = clean_text(user)
    data["last_user_query"] = clean_text(user)
    data["last_effective_query"] = clean_text(
        effective_query or user
    )
    data["last_answer"] = clean_text(answer)
    data["last_mode"] = mode

    data["history"].append({
        "role": "user",
        "content": clean_text(user),
    })

    data["history"].append({
        "role": "assistant",
        "content": clean_text(answer),
        "mode": mode,
    })

    save(data)
