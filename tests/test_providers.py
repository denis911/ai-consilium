import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from council.schemas import ConsiliumQueryInput, ModelResponsePayload
from council.providers import LLMProviderEngine, DEFAULT_MODELS, OPENROUTER_FREE_MODELS


@pytest.mark.asyncio
async def test_query_single_provider_success():
    engine = LLMProviderEngine(default_timeout=5.0)

    mock_choice = MagicMock()
    mock_choice.message.content = "DuckDB is a fast, embedded analytical database."
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 20

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion, \
         patch("litellm.completion_cost", return_value=0.001):
        mock_acompletion.return_value = mock_response

        messages = [{"role": "user", "content": "What is DuckDB?"}]
        payload = await engine._query_single_provider("gpt-4o", messages)

        assert payload.model_name == "gpt-4o"
        assert payload.response_text == "DuckDB is a fast, embedded analytical database."
        assert payload.status == "success"
        assert payload.prompt_tokens == 50
        assert payload.completion_tokens == 20
        assert payload.cost_usd == 0.001
        assert payload.latency_ms > 0


@pytest.mark.asyncio
async def test_query_single_provider_timeout_isolation():
    engine = LLMProviderEngine(default_timeout=0.1)

    async def slow_completion(*args, **kwargs):
        await asyncio.sleep(0.5)
        return MagicMock()

    with patch("litellm.acompletion", side_effect=slow_completion):
        messages = [{"role": "user", "content": "Hello"}]
        payload = await engine._query_single_provider("gpt-4o", messages, timeout=0.1)

        assert payload.model_name == "gpt-4o"
        assert payload.status == "timeout"
        assert "timed out" in payload.response_text


@pytest.mark.asyncio
async def test_query_single_provider_error_isolation():
    engine = LLMProviderEngine(default_timeout=5.0)

    with patch("litellm.acompletion", side_effect=ValueError("Invalid API key")):
        messages = [{"role": "user", "content": "Hello"}]
        payload = await engine._query_single_provider("gpt-4o", messages)

        assert payload.model_name == "gpt-4o"
        assert payload.status == "error"
        assert "Invalid API key" in payload.response_text


@pytest.mark.asyncio
async def test_query_concurrently_mixed_results():
    engine = LLMProviderEngine(default_timeout=5.0)

    query_input = ConsiliumQueryInput(
        query="Compare SQLite vs DuckDB",
        context_chunks=["Context snippet 1"],
        selected_models=["gpt-4o", "claude-3-5-haiku-20241022"],
    )

    async def mock_acompletion_side_effect(model, messages, **kwargs):
        if "gpt-4o" in model:
            mock_resp = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "GPT-4o response"
            mock_resp.choices = [mock_choice]
            mock_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=10)
            return mock_resp
        else:
            raise RuntimeError("API unavailable")

    with patch("litellm.acompletion", side_effect=mock_acompletion_side_effect):
        results = await engine.query_concurrently(query_input)

        assert len(results) == 2
        gpt4_res = next(r for r in results if r.model_name == "gpt-4o")
        claude_res = next(r for r in results if r.model_name == "claude-3-5-haiku-20241022")

        assert gpt4_res.status == "success"
        assert gpt4_res.response_text == "GPT-4o response"

        assert claude_res.status == "error"
        assert "API unavailable" in claude_res.response_text


def test_get_effective_models_selection():
    engine = LLMProviderEngine()

    # Explicit models requested
    assert engine.get_effective_models(requested_models=["custom/model"]) == ["custom/model"]

    # Explicit free tier requested
    assert engine.get_effective_models(use_free_tier=True) == OPENROUTER_FREE_MODELS

    # Auto-detection when only OPENROUTER_API_KEY is present
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=True):
        assert engine.get_effective_models() == OPENROUTER_FREE_MODELS

    # Primary key present returns filtered models matching available keys
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test", "OPENAI_API_KEY": "sk-proj-test"}, clear=True):
        assert engine.get_effective_models() == ["gpt-4o"]


@pytest.mark.asyncio
async def test_openrouter_free_tier_query_execution():
    engine = LLMProviderEngine(default_timeout=5.0)
    query_input = ConsiliumQueryInput(query="Test OpenRouter fallback")

    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OpenRouter free model answer"
    mock_resp.choices = [mock_choice]
    mock_resp.usage = MagicMock(prompt_tokens=15, completion_tokens=25)

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_resp

        results = await engine.query_concurrently(query_input, use_free_tier=True)

        assert len(results) == 5
        assert all(r.status == "success" for r in results)
        assert results[0].model_name == OPENROUTER_FREE_MODELS[0]
        assert results[0].response_text == "OpenRouter free model answer"

        # Verify extra headers were passed for OpenRouter models
        call_kwargs = mock_acompletion.call_args.kwargs
        assert "extra_headers" in call_kwargs
        assert call_kwargs["extra_headers"]["X-Title"] == "AI Consilium Dual-Engine Consensus Agent"
