"""Database service abstraction."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy.orm import Session

from db.base import Base
from db.session import build_session_factory
from services.config import Settings

LOGGER = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.session_factory = build_session_factory(settings)

    def create_schema(self) -> None:
        engine = self.session_factory.kw["bind"]
        Base.metadata.create_all(bind=engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            LOGGER.exception("database session failed")
            raise
        finally:
            session.close()
