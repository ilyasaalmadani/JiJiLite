from pathlib import Path

ROOT = Path.home() / "JiJiLite"

def current():
    return (ROOT / "version").read_text().strip()
