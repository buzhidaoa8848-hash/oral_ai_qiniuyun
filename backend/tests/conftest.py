"""Shared pytest fixtures.

Uses an in-memory SQLite database with StaticPool so all connections
within a test share the same database.
"""

import pytest

# Import models so SQLModel.metadata is populated before table creation.
import app.models as _  # noqa: F401


@pytest.fixture
def client(monkeypatch):
    """TestClient whose entire app uses an in-memory test DB."""
    from sqlalchemy.pool import StaticPool

    # Patch the database URL BEFORE importing app modules.
    monkeypatch.setattr(
        "app.config.settings.database_url",
        "sqlite://",
    )

    # Re-create the engine with StaticPool so all connections share
    # the same in-memory database.
    from sqlmodel import create_engine
    from app import config as _cfg
    import app.database as _db

    _db.engine = create_engine(
        _cfg.settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables on the new engine.
    from app.database import create_db_and_tables

    create_db_and_tables()

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c

    # Cleanup
    from sqlmodel import SQLModel

    SQLModel.metadata.drop_all(_db.engine)


@pytest.fixture
def session():
    """Standalone session for model tests (uses its own in-memory DB)."""
    from sqlalchemy.pool import StaticPool
    from sqlmodel import SQLModel, Session, create_engine

    eng = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        yield s
