"""Qwen (DashScope / Alibaba Cloud) LLM provider."""

from __future__ import annotations

import json
import os
from typing import Any

from .base import BaseLLMProvider


class QwenProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not set")

        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are a language-learning content creator. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        raw = response.choices[0].message.content or "{}"
        # Qwen may wrap JSON in markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
        return json.loads(raw)
