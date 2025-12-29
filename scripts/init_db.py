"""
Initialize the Whisper transcription database.

This script creates the SQLite database with all required tables for the
Whisper transcription system. It is idempotent - safe to run multiple times
without deleting existing data.

Tables Created:
    - audio_files: Stores uploaded audio file metadata
      - id, original_filename, file_path, duration_seconds, uploaded_at,
        file_size_bytes, mime_type

    - transcriptions: Stores transcription results with status tracking
      - id, audio_file_id (FK), model, text, status, language,
        duration_seconds, created_at, completed_at, error_message,
        processing_time_seconds

Database Location:
    - Default: ./whisper_transcriptions.db (project root)
    - Configurable via DATABASE_URL environment variable

Usage:
    python scripts/init_db.py

Exit Codes:
    0: Success - Database initialized or already exists
    1: Failure - Error during initialization

Examples:
    # Initialize database with default settings
    python scripts/init_db.py

    # Database will be created if it doesn't exist
    # Existing data will NOT be deleted
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.persistence.database import init_db


if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully!")
        print("✓ All tables created")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
