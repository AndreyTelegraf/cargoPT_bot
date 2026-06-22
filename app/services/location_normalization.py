from __future__ import annotations

import re
from urllib.parse import quote_plus


GOOGLE_MAPS_RE = re.compile(
    r"https?://(?:www\.)?(?:google\.[^\s]+/maps|maps\.app\.goo\.gl|goo\.gl/maps)[^\s]*",
    re.IGNORECASE,
)


def extract_google_maps_url(raw_text: str) -> str | None:
    match = GOOGLE_MAPS_RE.search(raw_text)
    if not match:
        return None
    return match.group(0).rstrip(".,;)")


def build_google_maps_search_url(raw_text: str) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(raw_text)


def build_google_maps_coordinate_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


def normalize_text_location(raw_text: str) -> tuple[str, str]:
    clean = raw_text.strip()
    maps_url = extract_google_maps_url(clean) or build_google_maps_search_url(clean)
    return clean, maps_url
