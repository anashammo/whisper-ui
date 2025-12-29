"""Check database status"""
import sys
from pathlib import Path

# Add project root to path (scripts/maintenance/ -> scripts/ -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.models.transcription_model import TranscriptionModel
from src.infrastructure.persistence.models.audio_file_model import AudioFileModel

db = SessionLocal()
try:
    # Get all audio files
    audio_files = db.query(AudioFileModel).all()
    print(f'Total audio files: {len(audio_files)}')
    print()

    for af in audio_files[:3]:  # Show first 3
        print(f'Audio File ID: {af.id}')
        print(f'  Filename: {af.original_filename}')
        print(f'  Duration: {af.duration_seconds}s')

        # Get transcriptions for this audio file
        transcriptions = db.query(TranscriptionModel).filter(TranscriptionModel.audio_file_id == af.id).all()
        print(f'  Transcriptions: {len(transcriptions)}')
        for t in transcriptions:
            print(f'    - {t.id[:8]}... | Model: {t.model} | Status: {t.status} | Duration: {t.duration_seconds}s')
        print()
finally:
    db.close()
