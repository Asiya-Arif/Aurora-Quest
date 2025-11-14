from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config_quest import settings
import importlib

# Try to create engine using configured DATABASE_URL. If the required DB driver
# isn't installed (e.g. psycopg2 for Postgres), fall back to a local sqlite
# file so the app can run in development without requiring system DB drivers.

def _make_engine():
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        return engine
    except ModuleNotFoundError as exc:
        # Likely missing DB driver (psycopg2). Fall back to sqlite file.
        print("WARNING: DB driver not found; falling back to sqlite for development.")
        return create_engine("sqlite:///./local_dev.db", connect_args={"check_same_thread": False})

engine = _make_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
