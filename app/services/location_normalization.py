from __future__ import annotations

import re
from urllib.parse import quote_plus


GOOGLE_MAPS_RE = re.compile(
    r"https?://(?:www\.)?(?:google\.[^\s]+/maps|maps\.app\.goo\.gl|goo\.gl/maps)[^\s]*",
    re.IGNORECASE,
)

POSTAL_CODE_RE = re.compile(r"\b\d{4}-\d{3}\b")

COORDINATE_RE = re.compile(
    r"(?P<lat>-?\d{1,2}\.\d+)\s*,\s*(?P<lon>-?\d{1,3}\.\d+)"
)


def extract_google_maps_url(raw_text: str) -> str | None:
    match = GOOGLE_MAPS_RE.search(raw_text)
    if not match:
        return None
    return match.group(0).rstrip(".,;)")


def extract_postal_code(raw_text: str) -> str | None:
    match = POSTAL_CODE_RE.search(raw_text)
    if not match:
        return None
    return match.group(0)


def extract_coordinates(raw_text: str) -> tuple[float | None, float | None]:
    match = COORDINATE_RE.search(raw_text)
    if not match:
        return None, None

    latitude = float(match.group("lat"))
    longitude = float(match.group("lon"))

    if not (-90 <= latitude <= 90):
        return None, None

    if not (-180 <= longitude <= 180):
        return None, None

    return latitude, longitude


def build_google_maps_search_url(raw_text: str) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(raw_text)


def build_google_maps_coordinate_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


def strip_google_maps_url(raw_text: str) -> str:
    maps_url = extract_google_maps_url(raw_text)
    if maps_url is None:
        return raw_text.strip()

    return raw_text.replace(maps_url, "").strip(" \n\t,.;-")


def normalize_text_location(raw_text: str) -> dict[str, str | float | None]:
    clean = raw_text.strip()
    original_google_maps_url = extract_google_maps_url(clean)
    normalized_address = strip_google_maps_url(clean)
    postal_code = extract_postal_code(clean)

    latitude, longitude = extract_coordinates(clean)

    if latitude is not None and longitude is not None:
        map_url = build_google_maps_coordinate_url(latitude, longitude)
    elif original_google_maps_url is not None:
        map_url = original_google_maps_url
    else:
        map_url = build_google_maps_search_url(normalized_address or clean)

    return {
        "raw_text": clean,
        "original_google_maps_url": original_google_maps_url,
        "normalized_address": normalized_address or clean,
        "postal_code": postal_code,
        "latitude": latitude,
        "longitude": longitude,
        "map_url": map_url,
    }
