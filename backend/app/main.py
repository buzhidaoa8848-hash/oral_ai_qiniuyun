"""SceneTalk AI — FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from . import database
from .routers import health, materials, profiles, reports, scenes, sessions, voice
from .seed import seed_if_empty
from sqlmodel import Session

# ── Logging setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)-7s] %(name)s — %(message)s",
    stream=sys.stdout,
)
# Silence noisy SQLAlchemy logs unless debugging
if not settings.debug:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("scenetalk")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables and seed built-in scenes on startup."""
    logger.info("=" * 55)
    logger.info(f"App: {settings.app_name} v0.1.0")
    logger.info(f"MOCK_MODE: {settings.mock_mode}")
    logger.info(f"Providers: LLM={settings.llm_provider} STT={settings.stt_provider} "
                f"TTS={settings.tts_provider} Pron={settings.pronunciation_provider}")
    logger.info(f"DB: {settings.database_url[:40]}...")
    logger.info("=" * 55)

    database.create_db_and_tables()
    with Session(database.engine) as session:
        seed_if_empty(session)

    # Import task_queue to trigger Redis detection
    from . import task_queue as _  # noqa: F401

    logger.info("Startup complete — ready to accept requests")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered language learning through scene-based conversation cards",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────
frontend_origins = [
    origin.strip()
    for origin in settings.frontend_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=False,  # 不需要 cookie/auth token
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(profiles.router)
app.include_router(materials.router)
app.include_router(scenes.router)
app.include_router(sessions.router)
app.include_router(voice.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    return {"message": "SceneTalk AI backend is running"}
