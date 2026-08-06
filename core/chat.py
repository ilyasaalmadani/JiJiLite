import subprocess
from core.config import CONFIG

SYSTEM = (
    "Anda adalah JiJi Lite. "
    "Jawab dalam Bahasa Indonesia. "
    "Singkat, jelas, langsung ke inti. "
    "Jangan tampilkan proses berpikir."
)

def ask(prompt):
    subprocess.run([
        "ollama",
        "run",
        CONFIG["chat_model"],
        f"{SYSTEM}\n\n{prompt}"
    ])
