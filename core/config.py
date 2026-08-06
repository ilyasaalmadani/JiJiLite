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
