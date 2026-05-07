"""Database session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.config import Settings


def build_session_factory(settings: Settings) -> sessionmaker:
    engine = create_engine(settings.postgres_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
