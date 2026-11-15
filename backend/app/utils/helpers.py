import re
import unicodedata

from app.core.config import get_settings

MAX_MESSAGE_CHARS = 5000

# Phrases that suggest a customer is trying to steer the model instead of describing a project.
_INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above) (instructions|prompts?|rules)",
    r"disregard (all |any )?(the )?(previous|prior|above|system)",
    r"(reveal|show|print|repeat).{0,30}(system prompt|instructions|api key)",
    r"you are now\b",
    r"act as (an? )?(?!customer)",
    r"</?(customer_message|system)>",
    r"\bjailbreak\b",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_customer_text(text: str) -> str:
    """Treat customer text as untrusted: drop control chars, neutralise our delimiter tags, cap length."""
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    text = re.sub(r"</?\s*customer_message\s*>", "[tag removed]", text, flags=re.IGNORECASE)
    return text.strip()[:MAX_MESSAGE_CHARS]


def detect_prompt_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(text))


def scrub_secrets(text: str) -> str:
    """Remove any configured API key / JWT secret from text before it is logged or stored."""
    s = get_settings()
    for secret in (s.gemini_api_key, s.groq_api_key, s.jwt_secret, s.admin_password, s.smtp_password):
        if secret and len(secret) >= 6:
            text = text.replace(secret, "***")
    return text


def is_mostly_latin(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    return sum(c.isascii() for c in letters) / len(letters) >= 0.8
