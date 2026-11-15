import json
import re


class JSONParseError(ValueError):
    pass


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def parse_json_object(text: str) -> dict:
    """Parse an LLM reply into a dict. Tolerates code fences and chatter around the JSON,
    but raises JSONParseError if no valid JSON object can be recovered."""
    if not text or not text.strip():
        raise JSONParseError("empty response")
    cleaned = _FENCE_RE.sub("", text.strip().lstrip("﻿")).strip()
    candidates = [cleaned]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        candidates.append(cleaned[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
        raise JSONParseError("JSON root must be an object")
    raise JSONParseError("response is not valid JSON")
