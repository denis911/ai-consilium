import os
import pytest
from council.providers import LLMProviderEngine, DEFAULT_MODELS, OPENROUTER_FREE_MODELS
from council.synthesizer import LLMJudgeSynthesizer, JUDGE_FALLBACK_CHAIN


def test_effective_models_filters_by_present_keys(monkeypatch):
    engine = LLMProviderEngine()

    # If no keys are present
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    models = engine.get_effective_models()
    assert len(models) > 0

    # If only OPENAI_API_KEY is present
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-openai")
    openai_models = engine.get_effective_models()
    assert "o3-mini" in openai_models
    assert "anthropic/claude-sonnet-5" not in openai_models


def test_judge_fallback_chain_defined():
    assert len(JUDGE_FALLBACK_CHAIN) >= 3
    assert "gemini/gemini-2.5-flash" in JUDGE_FALLBACK_CHAIN
    assert "o3-mini" in JUDGE_FALLBACK_CHAIN
