"""
Migration script to add enable_tashkeel column to transcriptions table.

This migration adds support for Arabic Tashkeel (diacritization) tracking.
The enable_tashkeel column stores whether Arabic diacritics should be added
during LLM enhancement.

Usage:
    python scripts/migrations/migrate_add_tashkeel.py

Database Changes:
    - Adds 'enable_tashkeel' column to 'transcriptions' table
    - Type: BOOLEAN, default: FALSE, NOT NULL

Notes:
    - Safe to run multiple times (checks if column exists)
    - Works with both SQLite (local dev) and PostgreSQL (Docker)
    - Existing transcriptions default to enable_tashkeel = FALSE
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def get_database_url():
    """Get database URL from environment or default to SQLite."""
    import os
    from dotenv import load_dotenv

    # Load environment variables
    env_path = project_root / "src" / "presentation" / "api" / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Check for PostgreSQL configuration (Docker)
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")

    if postgres_user and postgres_password and postgres_db:
        return f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:5432/{postgres_db}"

    # Default to SQLite (local development)
    db_path = project_root / "whisper_transcriptions.db"
    return f"sqlite:///{db_path}"


def column_exists(engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """Run the migration to add enable_tashkeel column."""
    database_url = get_database_url()

    print(f"Database: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Check if column already exists
            if column_exists(engine, "transcriptions", "enable_tashkeel"):
                print("✓ Column 'enable_tashkeel' already exists. Migration skipped.")
                return

            # Determine SQL syntax based on database type
            if "postgresql" in database_url:
                # PostgreSQL syntax
                sql = text("""
                    ALTER TABLE transcriptions
                    ADD COLUMN enable_tashkeel BOOLEAN NOT NULL DEFAULT FALSE
                """)
            else:
                # SQLite syntax
                sql = text("""
                    ALTER TABLE transcriptions
                    ADD COLUMN enable_tashkeel BOOLEAN NOT NULL DEFAULT 0
                """)

            conn.execute(sql)
            conn.commit()

            print("✓ Successfully added 'enable_tashkeel' column to transcriptions table")
            print("  - Type: BOOLEAN")
            print("  - Default: FALSE")
            print("  - Existing records: set to FALSE")

    except (OperationalError, ProgrammingError) as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add Arabic Tashkeel (Diacritization) Column")
    print("=" * 60)
    migrate()
    print("=" * 60)
