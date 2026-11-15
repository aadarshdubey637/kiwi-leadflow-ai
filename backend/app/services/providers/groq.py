from app.services.providers.base import LLMProvider, LLMResult, ProviderError


class GroqProvider(LLMProvider):
    name = "groq"
    # Output cap per call: our JSON answers are ~300-500 tokens; this stops a runaway reply eating the rate limit.
    MAX_OUTPUT_TOKENS = 1500

    def __init__(self, *args, reasoning_effort: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._reasoning_effort = reasoning_effort
    _URL = "https://api.groq.com/openai/v1/chat/completions"  # OpenAI-compatible API

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        key = self._require_key()
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.model.startswith("openai/gpt-oss"):
            # Reasoning models "think" before answering and those tokens count against Groq's per-minute limit.
            # Structured extraction does not need deep reasoning, so default to "low" (faster, ~5x fewer tokens).
            payload["max_completion_tokens"] = self.MAX_OUTPUT_TOKENS
            if self._reasoning_effort:
                payload["reasoning_effort"] = self._reasoning_effort
        data = await self._post_json(self._URL, {"Authorization": f"Bearer {key}"}, payload)
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError("groq returned no content") from e
        usage = data.get("usage") or {}
        return LLMResult(
            text=text,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            provider=self.name,
            model=self.model,
        )
