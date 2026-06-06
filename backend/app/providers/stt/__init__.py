"""STT (Speech-to-Text) provider abstraction with graceful fallback."""

import logging

from .base import BaseSTTProvider
from .mock_stt import MockSTTProvider
from .openai_stt import OpenaiSTTProvider
from .qwen_stt import QwenSTTProvider
from .tencent_stt import TencentSTTProvider

logger = logging.getLogger("scenetalk.providers.stt")


def get_stt_provider() -> BaseSTTProvider:
    """Return the configured STT provider with graceful fallback."""
    from ...config import settings

    if settings.mock_mode:
        logger.info("STT provider: mock (MOCK_MODE=true)")
        return MockSTTProvider()

    provider_name = settings.stt_provider.lower()
    logger.info(f"STT provider requested: {provider_name}")

    if provider_name == "openai":
        if settings.openai_api_key:
            logger.info("STT provider: openai (key present)")
            return OpenaiSTTProvider(api_key=settings.openai_api_key)
        else:
            logger.warning("STT provider: openai selected but OPENAI_API_KEY is empty → falling back to mock")
            return MockSTTProvider()

    elif provider_name == "qwen":
        if settings.dashscope_api_key:
            logger.info("STT provider: qwen (key present)")
            return QwenSTTProvider(api_key=settings.dashscope_api_key)
        else:
            logger.warning("STT provider: qwen selected but DASHSCOPE_API_KEY is empty → falling back to mock")
            return MockSTTProvider()

    elif provider_name == "tencent":
        logger.warning("STT provider: tencent not yet implemented → falling back to mock")
        return MockSTTProvider()

    logger.info(f"STT provider: mock (unknown provider '{provider_name}')")
    return MockSTTProvider()
