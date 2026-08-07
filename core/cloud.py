import os
import sys

from google import genai
from google.genai import types


MODEL = os.environ.get(
    "JIJI_GEMINI_MODEL",
    "gemini-2.5-flash",
)

SYSTEM = """
Anda adalah JiJi Cloud, asisten AI berbahasa Indonesia.

Aturan:
1. Jawab dalam Bahasa Indonesia kecuali diminta lain.
2. Gunakan konteks pertanyaan secara tepat.
3. Jangan mengarang fakta, sumber, URL, nama, jabatan, atau angka.
4. Bila informasi tidak pasti atau membutuhkan data terbaru,
   nyatakan keterbatasannya dengan jelas.
5. Jawab langsung, natural, dan tidak bertele-tele.
""".strip()


def ask_cloud(prompt: str) -> str:
    key = os.environ.get("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan.")

    client = genai.Client(api_key=key)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            temperature=0.2,
            max_output_tokens=1200,
        ),
    )

    text = getattr(response, "text", None)

    if not text:
        raise RuntimeError(
            "Gemini tidak menghasilkan jawaban teks."
        )

    return text.strip()


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()

    if not prompt:
        print('Gunakan: jiji-cloud "pertanyaan"')
        raise SystemExit(1)

    try:
        print("☁️ JiJi Cloud\n")
        print(ask_cloud(prompt))

    except Exception as error:
        print(f"✗ JiJi Cloud gagal: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
