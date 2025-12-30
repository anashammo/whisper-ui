"""Automatically clean up orphaned transcriptions without confirmation"""
import sys
from pathlib import Path

# Add project root to path (scripts/maintenance/ -> scripts/ -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.models.transcription_model import TranscriptionModel
from src.infrastructure.persistence.models.audio_file_model import AudioFileModel

db = SessionLocal()
try:
    # Get all transcriptions
    all_transcriptions = db.query(TranscriptionModel).all()
    print(f'Total transcriptions: {len(all_transcriptions)}')

    # Get all audio file IDs
    all_audio_files = db.query(AudioFileModel).all()
    audio_file_ids = {af.id for af in all_audio_files}
    print(f'Total audio files: {len(audio_file_ids)}')
    print()

    # Find orphaned transcriptions
    orphaned = []
    for trans in all_transcriptions:
        if trans.audio_file_id not in audio_file_ids:
            orphaned.append(trans)

    print(f'Orphaned transcriptions found: {len(orphaned)}')

    if orphaned:
        print('\nOrphaned transcriptions:')
        for trans in orphaned:
            info = f'  - ID: {trans.id[:8]}... | Audio File ID: {trans.audio_file_id[:8]}... | Model: {trans.model} | Status: {trans.status.value}'
            if trans.enable_llm_enhancement:
                llm_status = trans.llm_enhancement_status or 'pending'
                info += f' | LLM: {llm_status}'
            print(info)

        print('\nDeleting orphaned transcriptions...')
        for trans in orphaned:
            db.delete(trans)
        db.commit()
        print(f'\nSuccessfully deleted {len(orphaned)} orphaned transcriptions')
    else:
        print('\nNo orphaned transcriptions found - database is clean!')

finally:
    db.close()
