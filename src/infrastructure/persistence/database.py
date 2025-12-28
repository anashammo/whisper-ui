"""Database configuration and session management using SQLAlchemy"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from ..config.settings import get_settings

# Get settings
settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=settings.debug  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Yields a database session and ensures it's closed after use.
    This should be used with FastAPI's Depends() for dependency injection.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This function should be called on application startup
    to ensure all tables exist.
    """
    # Import all models here to ensure they're registered with Base
    from .models import transcription_model, audio_file_model

    # Create all tables
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    Only use this for testing or resetting the database.
    """
    Base.metadata.drop_all(bind=engine)


def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data!
    Only use this for testing or development.
    """
    drop_db()
    init_db()
