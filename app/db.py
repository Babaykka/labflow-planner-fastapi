from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, scoped_session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
DATABASE_URL = str(settings.database_url)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
db_session_factory = scoped_session(
    sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = db_session_factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    __import__("app.models")
    Base.metadata.create_all(bind=engine)
