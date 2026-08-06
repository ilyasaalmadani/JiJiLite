import html
import re


def clean_output(text: str) -> str:
    value = html.unescape(str(text or ""))

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    value = value.replace("\\</b>", " ")
    value = value.replace("\\<", "<")
    value = value.replace("\\>", ">")

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+([.,;:!?])",
        r"\1",
        value,
    )

    return value.strip()
