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
