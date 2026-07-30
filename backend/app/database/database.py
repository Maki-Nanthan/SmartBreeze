from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.base import Base


def get_engine(db_url: str | None = None):
    database_url = db_url or settings.database_url
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def get_session_factory(db_url: str | None = None):
    return sessionmaker(bind=get_engine(db_url), autocommit=False, autoflush=False)


def init_db(db_url: str | None = None) -> None:
    import app.models.persistence  # noqa: F401
    Base.metadata.create_all(bind=get_engine(db_url))
