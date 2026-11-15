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


# Shapes of real API keys (Groq, Google, OpenAI-style, xAI). Hidden from logs and error text even when the value was never
# registered as a "secret" setting, e.g. a key pasted into the wrong environment variable.
_KEY_SHAPES = re.compile(r"gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|AQ\.[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9_\-]{30,}|xai-[A-Za-z0-9]{20,}")


def looks_like_api_key(value: str) -> bool:
    return bool(_KEY_SHAPES.search(value or ""))


def scrub_secrets(text: str) -> str:
    """Remove any configured API key / JWT secret from text before it is logged or stored."""
    s = get_settings()
    for secret in (s.gemini_api_key, s.groq_api_key, s.jwt_secret, s.admin_password, s.smtp_password):
        if secret and len(secret) >= 6:
            text = text.replace(secret, "***")
    return _KEY_SHAPES.sub("***", text)


def is_mostly_latin(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    return sum(c.isascii() for c in letters) / len(letters) >= 0.8
