"""
Database wiring for the backend service.

PostgreSQL is the target for the real deployment (and what docker-compose
starts), but DATABASE_URL falls back to a local SQLite file so the service
still boots with zero infrastructure — useful when a teammate just wants to
run the API, and for the integration tests.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./criminal_db.sqlite3")

# check_same_thread is a SQLite-only argument; passing it to psycopg2 errors out.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Safe to call repeatedly."""
    from app import models  # noqa: F401  (registers the mappers before create_all)

    Base.metadata.create_all(bind=engine)
