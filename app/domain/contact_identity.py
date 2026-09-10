from __future__ import annotations

import re


def normalize_email_identity(value: str | None) -> str | None:
    normalized = (value or "").strip().casefold()
    return normalized or None


def normalize_phone_identity(value: str | None) -> str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.casefold().startswith("tel:"):
        raw = raw[4:].strip()
    if any(character.isalpha() for character in raw):
        return None

    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) == 9 and digits[0] in {"2", "9"}:
        digits = "351" + digits

    if not 7 <= len(digits) <= 15:
        return None
    return "+" + digits


def contact_identity_keys(
    *,
    customer_email: str | None,
    client_phone: str | None,
    client_whatsapp: str | None,
) -> set[str]:
    keys: set[str] = set()
    email = normalize_email_identity(customer_email)
    if email is not None:
        keys.add("email:" + email)
    for value in (client_phone, client_whatsapp):
        phone = normalize_phone_identity(value)
        if phone is not None:
            keys.add("phone:" + phone)
    return keys
