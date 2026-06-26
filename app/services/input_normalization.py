import re


def normalize_manual_text(raw_text: str | None) -> str:
    return (raw_text or "").strip().casefold().replace(",", ".")


def parse_first_int(raw_text: str | None) -> int:
    text = normalize_manual_text(raw_text)
    match = re.search(r"-?\d+", text)
    if not match:
        raise ValueError("integer value not found")
    return int(match.group(0))


def parse_first_float(raw_text: str | None) -> float:
    text = normalize_manual_text(raw_text)
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        raise ValueError("float value not found")
    return float(match.group(0))
