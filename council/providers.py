"""
Asynchronous Multi-LLM Provider Engine for AI Consilium
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional, Any
import litellm

from council.schemas import ModelResponsePayload, ConsiliumQueryInput

logger = logging.getLogger(__name__)

# Standard frontier model identifiers for LiteLLM
DEFAULT_MODELS: List[str] = [
    "gpt-4o",
    "anthropic/claude-3-5-haiku-20241022",
    "gemini/gemini-2.5-flash",
    "perplexity/sonar",
    "xai/grok-2",
]


class LLMProviderEngine:
    """Manager for querying multiple LLM providers concurrently via LiteLLM."""

    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
        # Silence excessive verbose logs from litellm
        litellm.suppress_debug_info = True

    async def _query_single_provider(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> ModelResponsePayload:
        """Query a single LLM provider with latency tracking and error isolation."""
        timeout_val = timeout or self.default_timeout
        start_time = time.perf_counter()

        try:
            response = await asyncio.wait_for(
                litellm.acompletion(
                    model=model_name,
                    messages=messages,
                    **kwargs
                ),
                timeout=timeout_val,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Extract output text
            choices = getattr(response, "choices", [])
            response_text = ""
            if choices and len(choices) > 0:
                first_choice = choices[0]
                message = getattr(first_choice, "message", None)
                if message:
                    response_text = getattr(message, "content", "") or ""

            # Extract token usage and cost
            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

            cost_usd = 0.0
            try:
                cost_usd = float(litellm.completion_cost(completion_response=response) or 0.0)
            except Exception:
                cost_usd = 0.0

            return ModelResponsePayload(
                model_name=model_name,
                response_text=response_text,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                status="success",
            )

        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"Provider request to {model_name} timed out after {timeout_val}s.")
            return ModelResponsePayload(
                model_name=model_name,
                response_text=f"Request timed out after {timeout_val} seconds.",
                latency_ms=latency_ms,
                status="timeout",
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Provider request to {model_name} failed: {e}")
            return ModelResponsePayload(
                model_name=model_name,
                response_text=f"Error querying model: {str(e)}",
                latency_ms=latency_ms,
                status="error",
            )

    async def query_concurrently(
        self,
        query_input: ConsiliumQueryInput,
        models: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> List[ModelResponsePayload]:
        """Query multiple models concurrently using asyncio.gather()."""
        target_models = models or query_input.selected_models or DEFAULT_MODELS

        # Format system and user prompt with context if available
        user_content = query_input.query
        if query_input.context_chunks:
            context_str = "\n---\n".join(query_input.context_chunks)
            user_content = f"Reference Context:\n{context_str}\n\nUser Question:\n{query_input.query}"

        messages = [
            {"role": "system", "content": "You are an expert research analyst delivering objective, precise answers."},
            {"role": "user", "content": user_content},
        ]

        tasks = [
            self._query_single_provider(model_name=model, messages=messages, timeout=timeout)
            for model in target_models
        ]

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)
