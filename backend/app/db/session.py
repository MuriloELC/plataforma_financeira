from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str | None = None) -> Engine:
    return create_engine(
        database_url or get_settings().database_url,
        pool_pre_ping=True,
    )


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
