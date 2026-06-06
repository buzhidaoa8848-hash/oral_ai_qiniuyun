"""Database engine, session factory, and table creation."""

from sqlmodel import SQLModel, Session, create_engine

from .config import settings

# ── Engine ────────────────────────────────────────────────────
# connect_args only needed for SQLite; harmless to always include.
_connect_args = {}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, echo=settings.debug, connect_args=_connect_args)


def create_db_and_tables() -> None:
    """Create all tables that don't exist yet (idempotent)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a database session."""
    with Session(engine) as session:
        yield session
