import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Defaults to a local SQLite file. In production we'll set DATABASE_URL to PostgreSQL.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./waste.db")

# SQLite needs this flag when FastAPI uses it from several threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


# FastAPI calls this for each request to get a database session, then closes it
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()