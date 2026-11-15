from dataclasses import dataclass

from app.schemas.ai_analysis import AIExtraction


@dataclass
class SentimentIntent:
    sentiment: str
    intent: str


def analyse(extraction: AIExtraction) -> SentimentIntent:
    """Sentiment & intent come from the same validated LLM call (one request instead of three).
    This step enforces the allowed sentiment values and a clean, bounded intent label."""
    sentiment = extraction.sentiment if extraction.sentiment in {"Positive", "Neutral", "Negative"} else "Neutral"
    return SentimentIntent(sentiment=sentiment, intent=extraction.intent.strip()[:200])
