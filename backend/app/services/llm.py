import time
import json
import re
from typing import Type, TypeVar, Optional, List
from pydantic import BaseModel
import google.generativeai as genai
from backend.app.core.config import settings

T = TypeVar("T", bound=BaseModel)


class TokenBudgetExceededError(Exception):
    """Raised when the prompt token estimation exceeds safety thresholds."""
    pass


class RateLimiter:
    """Sliding-window rate limiter ensuring API requests do not exceed max RPM."""

    def __init__(self, max_rpm: int = 15):
        self.max_rpm = max_rpm
        self.timestamps: List[float] = []

    def _purge_expired(self, now: float) -> None:
        cutoff = now - 60.0
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    def get_wait_seconds(self) -> float:
        now = time.time()
        self._purge_expired(now)
        if len(self.timestamps) < self.max_rpm:
            return 0.0
        oldest = self.timestamps[0]
        return max(0.0, 60.0 - (now - oldest))

    def acquire(self, blocking: bool = True) -> bool:
        now = time.time()
        self._purge_expired(now)
        if len(self.timestamps) < self.max_rpm:
            self.timestamps.append(now)
            return True

        if not blocking:
            return False

        wait_time = self.get_wait_seconds()
        if wait_time > 0:
            time.sleep(wait_time)
        self._purge_expired(time.time())
        self.timestamps.append(time.time())
        return True


class LLMService:
    """
    Robust Gemini 3 Flash / 1.5 Flash client wrapper with:
    - Sliding-window RPM rate-limiting to prevent quota exhaustion
    - Token budget guard
    - Exponential backoff retry on transient errors
    - Pydantic structured output parsing
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        max_prompt_tokens: int = 8000,
        max_rpm: int = 15,
        retry_attempts: int = 3,
        retry_backoff: float = 1.5,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.max_prompt_tokens = max_prompt_tokens
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff
        self.rate_limiter = RateLimiter(max_rpm=max_rpm)

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception:
                pass

    def estimate_tokens(self, text: str) -> int:
        """Heuristic token count estimation (~4 characters or ~1.3 tokens per word)."""
        words = len(text.split())
        return int(words * 1.3)

    def _get_model(self) -> genai.GenerativeModel:
        return genai.GenerativeModel(self.model_name)

    def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        tokens = self.estimate_tokens(prompt)
        if tokens > self.max_prompt_tokens:
            raise TokenBudgetExceededError(
                f"Prompt estimated at {tokens} tokens exceeds safety limit of {self.max_prompt_tokens}"
            )

        self.rate_limiter.acquire(blocking=True)

        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                model = self._get_model()
                generation_config = {}
                if max_tokens:
                    generation_config["max_output_tokens"] = max_tokens
                response = model.generate_content(prompt, generation_config=generation_config or None)
                if response and hasattr(response, "text"):
                    return response.text.strip()
                raise RuntimeError("Empty response received from LLM")
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    sleep_time = self.retry_backoff * (2 ** attempt)
                    time.sleep(sleep_time)

        raise last_error

    def generate_structured_json(self, prompt: str, schema: Type[T]) -> T:
        system_instruction = (
            f"\nYou must return ONLY a raw, valid JSON object matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}\n"
            f"Do not include any Markdown formatting, backticks, or extra commentary."
        )
        full_prompt = f"{prompt}\n\n{system_instruction}"
        raw_text = self.generate_text(full_prompt)

        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

        data = json.loads(cleaned)
        return schema.model_validate(data)


class OpenRouterUnavailableError(Exception):
    """Raised when OpenRouter API is unreachable or no API key is provided."""
    pass


class OpenRouterService:
    """
    OpenRouter API client supporting OpenRouter free-tier models:
    - meta-llama/llama-3.3-70b-instruct:free
    - google/gemini-2.0-flash-exp:free
    - deepseek/deepseek-r1:free
    Includes rate-limiting, error handling, and graceful fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        max_prompt_tokens: int = 8000,
        max_rpm: int = 15,
        timeout: float = 20.0,
    ):
        self.api_key = api_key if api_key is not None else settings.OPENROUTER_API_KEY
        self.model_name = model_name or settings.OPENROUTER_MODEL
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.max_prompt_tokens = max_prompt_tokens
        self.timeout = timeout
        self.rate_limiter = RateLimiter(max_rpm=max_rpm)

    def is_configured(self) -> bool:
        """Returns True if an OpenRouter API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Sends chat completion request to OpenRouter.
        Raises OpenRouterUnavailableError if unconfigured or unreachable.
        """
        if not self.is_configured():
            raise OpenRouterUnavailableError("OpenRouter API key is not configured.")

        import httpx

        self.rate_limiter.acquire(blocking=True)

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "LearnSync AI",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    raise OpenRouterUnavailableError(
                        f"OpenRouter API error {response.status_code}: {response.text}"
                    )
                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise OpenRouterUnavailableError("No choices returned in OpenRouter response.")
                content = choices[0].get("message", {}).get("content", "")
                return content.strip()
        except OpenRouterUnavailableError:
            raise
        except Exception as e:
            raise OpenRouterUnavailableError(f"OpenRouter request failed: {str(e)}") from e

    def generate_structured_json(self, prompt: str, schema: Type[T]) -> T:
        """Enforces structured JSON extraction matching Pydantic schema."""
        system_instruction = (
            f"\nYou must return ONLY a raw, valid JSON object matching this schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}\n"
            f"Do not include any Markdown formatting, backticks, or extra commentary."
        )
        full_prompt = f"{prompt}\n\n{system_instruction}"
        raw_text = self.generate_text(full_prompt)

        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

        data = json.loads(cleaned)
        return schema.model_validate(data)


# Default global instances
llm_service = LLMService()
openrouter_service = OpenRouterService()


def generate_text_with_fallback(prompt: str, max_tokens: Optional[int] = None) -> str:
    """
    Executes text generation using primary provider (gemini or openrouter)
    with immediate seamless failover to secondary provider if available.
    """
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    last_err = None

    if provider == "gemini":
        if settings.GEMINI_API_KEY:
            try:
                return llm_service.generate_text(prompt, max_tokens=max_tokens)
            except Exception as e:
                last_err = e
        if openrouter_service.is_configured():
            try:
                return openrouter_service.generate_text(prompt, max_tokens=max_tokens)
            except Exception as e:
                last_err = e
    else:
        if openrouter_service.is_configured():
            try:
                return openrouter_service.generate_text(prompt, max_tokens=max_tokens)
            except Exception as e:
                last_err = e
        if settings.GEMINI_API_KEY:
            try:
                return llm_service.generate_text(prompt, max_tokens=max_tokens)
            except Exception as e:
                last_err = e

    if last_err:
        raise last_err
    raise RuntimeError("No LLM provider is configured.")

