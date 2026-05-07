"""Database service abstraction."""

from sqlalchemy.orm import Session

from db.base import Base
from db.session import build_session_factory
from services.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.session_factory = build_session_factory(settings)

    def create_schema(self) -> None:
        engine = self.session_factory.kw["bind"]
        Base.metadata.create_all(bind=engine)

    def session(self) -> Session:
        return self.session_factory()
