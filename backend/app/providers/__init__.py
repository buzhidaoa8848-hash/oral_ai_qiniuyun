"""LLM provider abstraction — pluggable backends for scene generation.

Provider selection logic:
  1. MOCK_MODE=true  → MockProvider (always, no keys needed)
  2. llm_provider set → try that provider, fall back to mock if key missing
  3. default           → MockProvider
"""

import logging

from .base import BaseLLMProvider
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .qwen_provider import QwenProvider

logger = logging.getLogger("scenetalk.providers.llm")


def get_provider() -> BaseLLMProvider:
    """Return the configured LLM provider with graceful fallback."""
    from ..config import settings

    # ── MOCK_MODE overrides everything ────────────────────────
    if settings.mock_mode:
        logger.info("LLM provider: mock (MOCK_MODE=true)")
        return MockProvider()

    provider_name = settings.llm_provider.lower()
    logger.info(f"LLM provider requested: {provider_name}")

    # ── OpenAI ────────────────────────────────────────────────
    if provider_name == "openai":
        if settings.openai_api_key:
            logger.info("LLM provider: openai (key present)")
            return OpenAIProvider(api_key=settings.openai_api_key)
        else:
            logger.warning("LLM provider: openai selected but OPENAI_API_KEY is empty → falling back to mock")
            return MockProvider()

    # ── DeepSeek ──────────────────────────────────────────────
    elif provider_name == "deepseek":
        if settings.deepseek_api_key:
            logger.info("LLM provider: deepseek (key present)")
            return DeepSeekProvider(api_key=settings.deepseek_api_key)
        else:
            logger.warning("LLM provider: deepseek selected but DEEPSEEK_API_KEY is empty → falling back to mock")
            return MockProvider()

    # ── Qwen / DashScope ─────────────────────────────────────
    elif provider_name == "qwen":
        if settings.dashscope_api_key:
            logger.info("LLM provider: qwen (key present)")
            return QwenProvider(api_key=settings.dashscope_api_key)
        else:
            logger.warning("LLM provider: qwen selected but DASHSCOPE_API_KEY is empty → falling back to mock")
            return MockProvider()

    # ── Unknown / default ─────────────────────────────────────
    logger.info(f"LLM provider: mock (unknown provider '{provider_name}')")
    return MockProvider()
