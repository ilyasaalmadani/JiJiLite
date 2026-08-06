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
