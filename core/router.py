import subprocess

WEB_KEYWORDS = [
    "berita","hari ini","terbaru","update",
    "politik","ekonomi","saham","harga",
    "cuaca","presiden","menteri",
    "bitcoin","emas","2026","sekarang"
]

def handle(prompt):
    text = prompt.lower()

    if any(k in text for k in WEB_KEYWORDS):
        print("🌐 Web Search\n")
        subprocess.run([
            "python3",
            f"{__import__('os').path.expanduser('~')}/JiJiLite/core/web.py",
            prompt
        ])
        return

    print("💬 Chat\n")

    subprocess.run([
        "ollama",
        "run",
        "gemma3:4b",
        "Jawab dalam Bahasa Indonesia. Singkat, jelas, tanpa proses berpikir.\n\n"+prompt
    ])
