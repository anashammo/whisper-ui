"""Migration script to add model column to transcriptions table"""
import sqlite3
import os

# Database path
home = os.path.expanduser("~")
repo_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(repo_path, "whisper_transcriptions.db")

print(f"Migrating database at: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if model column exists
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'model' in columns:
        print("✓ model column already exists!")
    else:
        print("Adding model column to transcriptions table...")
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN model VARCHAR(50)")
        conn.commit()
        print("✓ Successfully added model column!")

    # Verify the column was added
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"\nCurrent columns in transcriptions table: {', '.join(columns)}")

except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nMigration complete!")
