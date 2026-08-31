import pytest
import time
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field
from backend.app.services.llm import LLMService, RateLimiter, TokenBudgetExceededError


class SampleStructuredOutput(BaseModel):
    summary: str
    confidence: float
    topics: list[str] = Field(default_factory=list)


def test_rate_limiter_throttles_requests():
    """Verify that RateLimiter tracks timestamps and prevents exceeding RPM."""
    limiter = RateLimiter(max_rpm=3)
    # 3 allowed immediately
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    assert limiter.acquire() is True
    # 4th request within same second should be blocked or return wait time > 0
    assert limiter.acquire(blocking=False) is False
    assert limiter.get_wait_seconds() > 0


def test_llm_token_budget_guard():
    """Verify that requests exceeding safety token limits are caught."""
    service = LLMService(api_key="test-key", max_prompt_tokens=100)
    huge_prompt = "word " * 500  # ~500 tokens, exceeds 100 limit
    with pytest.raises(TokenBudgetExceededError):
        service.generate_text(prompt=huge_prompt)


@patch("backend.app.services.llm.genai")
def test_llm_generate_structured_json_success(mock_genai):
    """Verify structured JSON output parsed into Pydantic model."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"summary": "Test summary", "confidence": 0.95, "topics": ["recursion", "trees"]}'
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    service = LLMService(api_key="valid-key")
    result = service.generate_structured_json(
        prompt="Summarize the concept of recursion",
        schema=SampleStructuredOutput,
    )

    assert isinstance(result, SampleStructuredOutput)
    assert result.summary == "Test summary"
    assert result.confidence == 0.95
    assert "recursion" in result.topics


@patch("backend.app.services.llm.genai")
def test_llm_retry_on_transient_error(mock_genai):
    """Verify exponential backoff retry on temporary failure."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Success after retry"
    # First call raises an exception, second call succeeds
    mock_model.generate_content.side_effect = [Exception("429 Resource exhausted"), mock_response]
    mock_genai.GenerativeModel.return_value = mock_model

    service = LLMService(api_key="valid-key", retry_attempts=2, retry_backoff=0.01)
    output = service.generate_text("Test prompt")
    assert output == "Success after retry"
    assert mock_model.generate_content.call_count == 2
