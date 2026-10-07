"""Unified LLM Router with auto-fallback, inspired by OmniRoute architecture.

All providers are accessed through the standard OpenAI Python SDK with custom base_url.
This eliminates the need for provider-specific SDKs (google-genai, groq, etc.)
and provides a single, resilient entry point for all LLM calls.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from pydantic import BaseModel, Field

logger = logging.getLogger("easyprompt.router")


# ─────────────────────────── Response Model ───────────────────────────

class CompletionResponse(BaseModel):
    """Standardized response from the router, including fallback metadata."""

    content: str
    model_used: str
    provider_used: str
    was_fallback: bool = False
    fallback_history: List[str] = Field(default_factory=list)
    latency_seconds: float = 0.0


# ─────────────────────────── Provider Registry ───────────────────────────

# Maps provider prefix to (base_url, default_headers_factory)
PROVIDER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_key": "GEMINI_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/TudorvCampean/EasyPrompt",
            "X-Title": "EasyPrompt",
        },
    },
}

# HTTP status codes that trigger auto-fallback
TRANSIENT_STATUS_CODES = {429, 404, 500, 502, 503, 504}


def parse_model_id(model_id: str) -> tuple[str, str]:
    """Parse 'provider/model-name' into (provider, model_name).

    For OpenRouter models that contain slashes in the model name
    (e.g. 'openrouter/anthropic/claude-3.5-sonnet'), the provider
    is the first segment and the model is everything after.
    """
    parts = model_id.split("/", 1)
    if len(parts) == 2:
        return parts[0].lower(), parts[1]
    raise ValueError(
        f"Invalid model_id '{model_id}'. Expected format: 'provider/model-name' "
        f"(e.g. 'gemini/gemini-3.8-flash', 'groq/llama-3.3-70b-versatile')"
    )


# ─────────────────────────── Router Client ───────────────────────────

class RouterClient:
    """Unified LLM gateway with auto-fallback across providers.

    Uses the OpenAI Python SDK with custom base_url for all providers,
    providing a single interface for Gemini, Groq, DeepSeek, and OpenRouter.
    """

    def __init__(self, api_keys: Dict[str, str]) -> None:
        """Initialize with a dict of provider -> api_key mappings.

        Args:
            api_keys: Dict mapping provider names to API keys.
                      e.g. {"gemini": "AIza...", "groq": "gsk_...", ...}
        """
        self._api_keys = {k.lower(): v for k, v in api_keys.items() if v}
        self._clients: Dict[str, OpenAI] = {}

        # Pre-build OpenAI clients for each configured provider
        for provider, key in self._api_keys.items():
            if provider in PROVIDER_REGISTRY:
                reg = PROVIDER_REGISTRY[provider]
                extra_headers = reg.get("extra_headers")
                self._clients[provider] = OpenAI(
                    api_key=key,
                    base_url=reg["base_url"],
                    default_headers=extra_headers,
                    timeout=60.0,
                )

    @property
    def available_providers(self) -> List[str]:
        """Return list of provider names that have valid API keys configured."""
        return list(self._clients.keys())

    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider has a configured and valid API key."""
        return provider.lower() in self._clients

    def filter_chain(self, model_chain: List[str]) -> List[str]:
        """Filter a model chain, keeping only models whose providers are available."""
        filtered = []
        for model_id in model_chain:
            try:
                provider, _ = parse_model_id(model_id)
                if self.is_provider_available(provider):
                    filtered.append(model_id)
            except ValueError:
                continue
        return filtered

    def complete(
        self,
        messages: List[Dict[str, str]],
        model_chain: List[str],
        temperature: float = 0.7,
    ) -> CompletionResponse:
        """Execute a completion with automatic fallback across the model chain.

        Args:
            messages: OpenAI-format messages [{"role": "...", "content": "..."}].
            model_chain: Ordered list of model IDs to try (e.g. ["gemini/gemini-3.8-flash", ...]).
            temperature: Sampling temperature.

        Returns:
            CompletionResponse with content, metadata about which model was used,
            and fallback history.

        Raises:
            RuntimeError: If all models in the chain fail.
        """
        # Filter chain to only include models whose providers have valid keys
        active_chain = self.filter_chain(model_chain)

        if not active_chain:
            available = ", ".join(self.available_providers) if self.available_providers else "none"
            raise RuntimeError(
                f"No models available in the fallback chain. "
                f"Configured providers: [{available}]. "
                f"Requested chain: {model_chain}. "
                f"Please add API keys in your .env file."
            )

        fallback_history: List[str] = []
        last_error: Optional[Exception] = None

        for idx, model_id in enumerate(active_chain):
            provider, model_name = parse_model_id(model_id)
            client = self._clients.get(provider)

            if client is None:
                fallback_history.append(f"{model_id} (no API key)")
                continue

            start = time.perf_counter()
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                )
                elapsed = time.perf_counter() - start
                content = response.choices[0].message.content or ""

                if idx > 0:
                    logger.warning(
                        "Auto-fallback activated: %s → %s (%.2fs)",
                        active_chain[0], model_id, elapsed,
                    )

                return CompletionResponse(
                    content=content,
                    model_used=model_name,
                    provider_used=provider,
                    was_fallback=idx > 0,
                    fallback_history=fallback_history,
                    latency_seconds=elapsed,
                )

            except RateLimitError as e:
                elapsed = time.perf_counter() - start
                reason = f"{model_id} (429 Rate Limit, {elapsed:.1f}s)"
                fallback_history.append(reason)
                logger.warning("Rate limited on %s, trying next fallback...", model_id)
                last_error = e

            except APITimeoutError as e:
                elapsed = time.perf_counter() - start
                reason = f"{model_id} (Timeout, {elapsed:.1f}s)"
                fallback_history.append(reason)
                logger.warning("Timeout on %s, trying next fallback...", model_id)
                last_error = e

            except APIConnectionError as e:
                elapsed = time.perf_counter() - start
                reason = f"{model_id} (Connection Error, {elapsed:.1f}s)"
                fallback_history.append(reason)
                logger.warning("Connection error on %s, trying next fallback...", model_id)
                last_error = e

            except APIError as e:
                elapsed = time.perf_counter() - start
                status = getattr(e, "status_code", "error")
                reason = f"{model_id} (HTTP {status}, {elapsed:.1f}s)"
                fallback_history.append(reason)
                logger.warning(
                    "Error %s on %s, trying next fallback...",
                    status, model_id,
                )
                last_error = e

            except Exception as e:
                elapsed = time.perf_counter() - start
                reason = f"{model_id} (Unexpected: {type(e).__name__}, {elapsed:.1f}s)"
                fallback_history.append(reason)
                logger.error("Unexpected error on %s: %s", model_id, e)
                last_error = e

        # All models exhausted
        raise RuntimeError(
            f"All models in the fallback chain failed. "
            f"History: {fallback_history}. "
            f"Last error: {last_error}"
        )
