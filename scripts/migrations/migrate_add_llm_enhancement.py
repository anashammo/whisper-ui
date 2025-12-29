"""Add LLM enhancement columns to transcriptions table

This migration adds support for LLM-based enhancement of transcriptions,
including fields for enhanced text, processing time, status, and error messages.

Run with: python scripts/migrations/migrate_add_llm_enhancement.py
"""
import sys
from pathlib import Path

# Add project root to path (scripts/migrations/ -> scripts/ -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.persistence.database import engine, SessionLocal
from sqlalchemy import text


def upgrade():
    """Add LLM enhancement columns to transcriptions table"""
    print("Starting migration: Adding LLM enhancement columns...")

    try:
        with engine.begin() as conn:
            # Check if columns already exist (idempotent migration)
            result = conn.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('transcriptions') "
                     "WHERE name='enable_llm_enhancement'")
            )
            column_exists = result.fetchone()[0] > 0

            if column_exists:
                print("WARNING: Columns already exist - migration already applied")
                return

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
        with engine.begin() as conn:
            # SQLite doesn't support DROP COLUMN in older versions
            # We'll need to recreate the table without these columns
            print("WARNING: SQLite doesn't support DROP COLUMN easily.")
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
