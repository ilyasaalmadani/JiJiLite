import json
from pathlib import Path

ROOT = Path.home() / "JiJiLite"

with open(ROOT / "config/router.json") as f:
    CONFIG = json.load(f)
