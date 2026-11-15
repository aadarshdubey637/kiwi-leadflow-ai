import re

_PHONE_RE = re.compile(r"^\+?\d{7,15}$")


def normalize_phone(value: str) -> str:
    """Strip common formatting (spaces, dashes, brackets, dots) and validate E.164-ish length."""
    cleaned = re.sub(r"[\s\-().]", "", value.strip())
    if not _PHONE_RE.match(cleaned):
        raise ValueError("Invalid phone number: use 7-15 digits, optional leading +")
    return cleaned
