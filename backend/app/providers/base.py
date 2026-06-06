"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Every LLM provider implements `generate_json(prompt, schema)`."""

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Send a prompt and return a JSON object matching the given schema.

        Args:
            prompt: The full system + user prompt.
            schema: JSON Schema that the output must conform to (for providers
                    that support structured output). Fallback providers may
                    ignore this and parse the raw response.

        Returns:
            A dict that passes the schema validation.
        """
        ...
