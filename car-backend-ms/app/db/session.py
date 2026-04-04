from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()

_is_sqlite = "sqlite" in settings.DATABASE_URL

engine = create_engine(
    settings.DATABASE_URL,
    **({"connect_args": {"check_same_thread": False}} if _is_sqlite else {}),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
