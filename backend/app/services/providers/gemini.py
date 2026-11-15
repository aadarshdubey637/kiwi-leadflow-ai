from app.services.providers.base import LLMProvider, LLMResult, ProviderError


class GeminiProvider(LLMProvider):
    name = "gemini"
    _URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        key = self._require_key()
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        }
        # Key goes in a header (not the URL) so it can never leak through URL logging.
        data = await self._post_json(
            self._URL.format(model=self.model), {"x-goog-api-key": key}, payload
        )
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError("gemini returned no content (possibly blocked by safety filters)") from e
        usage = data.get("usageMetadata") or {}
        return LLMResult(
            text=text,
            input_tokens=int(usage.get("promptTokenCount", 0)),
            output_tokens=int(usage.get("candidatesTokenCount", 0)),
            provider=self.name,
            model=self.model,
        )
