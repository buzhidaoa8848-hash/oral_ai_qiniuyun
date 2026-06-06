"""Pronunciation evaluation providers with graceful fallback."""

import logging

from .base import BasePronunciationProvider
from .fallback_pronunciation import FallbackPronunciationProvider
from .azure_pronunciation import AzurePronunciationProvider

logger = logging.getLogger("scenetalk.providers.pronunciation")


def get_pronunciation_provider() -> BasePronunciationProvider:
    """Return the configured pronunciation provider with graceful fallback."""
    from ...config import settings

    if settings.mock_mode:
        logger.info("Pronunciation provider: fallback (MOCK_MODE=true)")
        return FallbackPronunciationProvider()

    provider_name = settings.pronunciation_provider.lower()
    logger.info(f"Pronunciation provider requested: {provider_name}")

    if provider_name == "azure":
        if settings.azure_speech_key and settings.azure_speech_region:
            logger.info(
                f"Pronunciation provider: azure (region={settings.azure_speech_region})"
            )
            return AzurePronunciationProvider(
                key=settings.azure_speech_key,
                region=settings.azure_speech_region,
            )
        else:
            logger.warning(
                "Pronunciation provider: azure selected but AZURE_SPEECH_KEY "
                "or AZURE_SPEECH_REGION is empty → falling back to fallback"
            )
            return FallbackPronunciationProvider()

    logger.info(f"Pronunciation provider: fallback (unknown provider '{provider_name}')")
    return FallbackPronunciationProvider()
