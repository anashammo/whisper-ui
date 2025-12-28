"""Initialize database with tables"""
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
