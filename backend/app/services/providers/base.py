import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.utils.helpers import scrub_secrets


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str
    latency: float = 0.0  # seconds spent in the provider call itself (set by ai_service; excludes any queueing)


class ProviderError(Exception):
    """Any provider failure. `retryable` tells the caller whether trying the same provider again can help."""

    retryable = False


class ProviderNotConfigured(ProviderError):
    """No API key — nothing was sent."""


QUOTA_EXHAUSTED_SECONDS = 120  # a retry delay longer than this means a quota (e.g. daily), not a burst


class ProviderRateLimited(ProviderError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after
        # Short waits are worth retrying; a multi-hour wait is an exhausted quota -> use the fallback instead.
        self.quota_exhausted = retry_after is not None and retry_after > QUOTA_EXHAUSTED_SECONDS
        self.retryable = not self.quota_exhausted


class ProviderTimeout(ProviderError):
    retryable = True


class ProviderUnavailable(ProviderError):
    retryable = True


class LLMProvider(ABC):
    """Common interface — the rest of the app never knows which vendor it is talking to."""

    name: str

    def __init__(self, api_key: str | None, model: str, timeout: float, client: httpx.AsyncClient | None = None):
        self._api_key = api_key
        self.model = model
        self._timeout = timeout
        self._client = client  # injectable for tests

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        """Return the model's raw text (expected to be JSON) plus token counts."""

    def _require_key(self) -> str:
        if not self._api_key:
            raise ProviderNotConfigured(f"{self.name} API key is not configured")
        return self._api_key

    async def _post_json(self, url: str, headers: dict, payload: dict) -> dict:
        """POST and translate transport/HTTP problems into our ProviderError family."""
        owned = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as e:
            raise ProviderTimeout(f"{self.name} request timed out") from e
        except httpx.HTTPError as e:
            raise ProviderUnavailable(f"{self.name} network error: {type(e).__name__}") from e
        finally:
            if owned:
                await client.aclose()

        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else None
            if delay is None:  # Gemini puts it in the body: "retryDelay": "23s"
                m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', response.text)
                delay = float(m.group(1)) if m else None
            # Keep the provider's own explanation (e.g. "tokens per minute (TPM): Limit 8000, Used 7900 ... try again in 2s")
            # so monitoring shows WHICH limit was hit. Also read the wait time from it when no header was sent.
            detail = ""
            try:
                detail = str(response.json().get("error", {}).get("message", ""))[:200]
            except ValueError:
                pass
            if delay is None:
                m = re.search(r"try again in (\d+(?:\.\d+)?)\s*(ms|s)", detail)
                if m:
                    delay = float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)
            raise ProviderRateLimited(f"{self.name} rate limited (429)" + (f": {scrub_secrets(detail)}" if detail else ""), delay)
        if response.status_code >= 500:
            raise ProviderUnavailable(f"{self.name} server error {response.status_code}")
        if response.status_code >= 400:
            # 4xx (bad key, bad request) will not fix itself by retrying; keep the body short & scrubbed.
            raise ProviderError(f"{self.name} HTTP {response.status_code}: {scrub_secrets(response.text[:200])}")
        try:
            return response.json()
        except ValueError as e:
            raise ProviderUnavailable(f"{self.name} returned a non-JSON HTTP body") from e
