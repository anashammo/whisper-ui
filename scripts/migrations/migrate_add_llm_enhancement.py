"""Add LLM enhancement columns to transcriptions table

This migration adds support for LLM-based enhancement of transcriptions,
including fields for enhanced text, processing time, status, and error messages.

Run with: python scripts/migrations/migrate_add_llm_enhancement.py
"""
import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path (scripts/migrations/ -> scripts/ -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.persistence.database import engine, SessionLocal
from sqlalchemy import text, inspect


def upgrade():
    """Add LLM enhancement columns to transcriptions table"""
    print("Starting migration: Adding LLM enhancement columns...")

    # Get database inspector to check existing columns
    inspector = inspect(engine)

    try:
        # Check if the transcriptions table exists
        if 'transcriptions' not in inspector.get_table_names():
            print("ERROR: transcriptions table does not exist!")
            print("Run 'python scripts/setup/init_db.py' first to create tables.")
            return

        # Check if columns already exist (idempotent migration)
        columns = [col['name'] for col in inspector.get_columns('transcriptions')]

        if 'enable_llm_enhancement' in columns:
            print("WARNING: Columns already exist - migration already applied")
            return

        with engine.begin() as conn:

            # Add enable_llm_enhancement column
            print("Adding column: enable_llm_enhancement (BOOLEAN)...")
            conn.execute(
                text('ALTER TABLE transcriptions ADD COLUMN enable_llm_enhancement BOOLEAN DEFAULT FALSE NOT NULL')
            )

            # Add enhanced_text column
            print("Adding column: enhanced_text (TEXT)...")
            conn.execute(
                text('ALTER TABLE transcriptions ADD COLUMN enhanced_text TEXT')
            )

            # Add llm_processing_time_seconds column
            print("Adding column: llm_processing_time_seconds (REAL)...")
            conn.execute(
                text('ALTER TABLE transcriptions ADD COLUMN llm_processing_time_seconds REAL')
            )

            # Add llm_enhancement_status column
            print("Adding column: llm_enhancement_status (VARCHAR)...")
            conn.execute(
                text('ALTER TABLE transcriptions ADD COLUMN llm_enhancement_status VARCHAR(20)')
            )

            # Add llm_error_message column
            print("Adding column: llm_error_message (TEXT)...")
            conn.execute(
                text('ALTER TABLE transcriptions ADD COLUMN llm_error_message TEXT')
            )

            print("SUCCESS: Migration completed successfully!")
            print("\nAdded columns:")
            print("  - enable_llm_enhancement (BOOLEAN, DEFAULT FALSE)")
            print("  - enhanced_text (TEXT)")
            print("  - llm_processing_time_seconds (REAL)")
            print("  - llm_enhancement_status (VARCHAR(20))")
            print("  - llm_error_message (TEXT)")

    except Exception as e:
        print(f"ERROR: Migration failed: {str(e)}")
        raise


def downgrade():
    """Remove LLM enhancement columns (rollback)"""
    print("Rolling back migration: Removing LLM enhancement columns...")

    try:
        # Check database type
        db_url = str(engine.url)

        if 'sqlite' in db_url.lower():
            print("WARNING: SQLite doesn't support DROP COLUMN easily.")
            print("To rollback, restore from backup or recreate database.")
        elif 'postgresql' in db_url.lower():
            print("PostgreSQL supports DROP COLUMN, but rollback not implemented.")
            print("To rollback, manually drop columns or recreate database.")
        else:
            print(f"WARNING: Unsupported database type: {db_url}")
            print("To rollback, restore from backup or recreate database.")

    except Exception as e:
        print(f"ERROR: Rollback failed: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate database for LLM enhancement')
    parser.add_argument(
        '--downgrade',
        action='store_true',
        help='Rollback the migration'
    )

    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()
