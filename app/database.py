# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_quiz_app.db")

# For SQLite ensure check_same_thread False for multithreading
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# create tables utility
def create_tables():
    """
    Import models so that SQLAlchemy knows about them, then create tables using
    the Base defined in this module.
    """
    # import models (this registers model classes with Base)
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)