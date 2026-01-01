"""Migration script to add processing_time_seconds column to transcriptions table

This migration is database-agnostic and works with both SQLite and PostgreSQL.

Run with: python scripts/migrations/migrate_add_processing_time.py
"""
import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path (scripts/migrations/ -> scripts/ -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.persistence.database import engine
from sqlalchemy import text, inspect


def upgrade():
    """Add processing_time_seconds column to transcriptions table"""
    print("Starting migration: Adding processing_time_seconds column...")

    # Get database inspector to check existing columns
    inspector = inspect(engine)

    try:
        # Check if the transcriptions table exists
        if 'transcriptions' not in inspector.get_table_names():
            print("ERROR: transcriptions table does not exist!")
            print("Run 'python scripts/setup/init_db.py' first to create tables.")
            return

        # Get existing columns
        columns = [col['name'] for col in inspector.get_columns('transcriptions')]

        if 'processing_time_seconds' in columns:
            print("✓ processing_time_seconds column already exists - migration already applied")
            return

        # Add the column
        print("Adding column: processing_time_seconds (FLOAT)...")
        with engine.begin() as conn:
            # Use REAL for SQLite, FLOAT for PostgreSQL (both work with either)
            conn.execute(
                text('ALTER TABLE transcriptions ADD COLUMN processing_time_seconds FLOAT')
            )

        print("✓ SUCCESS: Migration completed successfully!")

        # Verify the column was added
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('transcriptions')]
        print(f"\nCurrent columns in transcriptions table: {', '.join(columns)}")

    except Exception as e:
        print(f"ERROR: Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    upgrade()
