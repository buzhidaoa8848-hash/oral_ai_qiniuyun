"""Application configuration — loaded from environment / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    database_url: str = "sqlite:///./scenetalk.db"

    # ── App ───────────────────────────────────────────────────
    app_name: str = "SceneTalk AI"
    debug: bool = True

    # ── Mock mode ─────────────────────────────────────────────
    # When True, all LLM calls use MockProvider — no API keys needed.
    mock_mode: bool = True

    # ── Provider selection ────────────────────────────────────
    llm_provider: str = "mock"       # mock | openai | deepseek | qwen
    stt_provider: str = "mock"
    tts_provider: str = "mock"
    pronunciation_provider: str = "mock"

    # ── API keys ──────────────────────────────────────────────
    openai_api_key: str = ""
    dashscope_api_key: str = ""
    deepseek_api_key: str = ""
    azure_speech_key: str = ""
    azure_speech_region: str = ""

    # ── Background tasks (optional) ───────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
