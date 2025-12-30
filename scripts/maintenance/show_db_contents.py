"""Show current database contents"""
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

    if audio_files:
        print('\nAudio files:')
        for af in audio_files:
            print(f'  - ID: {af.id[:16]}...')
            print(f'    Filename: {af.original_filename}')
            print(f'    Uploaded: {af.uploaded_at}')

            # Get transcriptions for this audio file
            transcriptions = db.query(TranscriptionModel).filter(
                TranscriptionModel.audio_file_id == af.id
            ).all()
            print(f'    Transcriptions: {len(transcriptions)}')
            for t in transcriptions:
                print(f'      * {t.model} - {t.status.value}')
                # Show LLM enhancement info if enabled
                if t.enable_llm_enhancement:
                    llm_status = t.llm_enhancement_status or 'pending'
                    print(f'        LLM: {llm_status}', end='')
                    if t.llm_processing_time_seconds:
                        print(f' ({t.llm_processing_time_seconds:.2f}s)', end='')
                    if t.enhanced_text:
                        print(f' - Enhanced text length: {len(t.enhanced_text)}', end='')
                    if t.llm_error_message:
                        print(f' - Error: {t.llm_error_message[:50]}...', end='')
                    print()
            print()
    else:
        print('  (No audio files in database)')

    # Check for transcriptions
    all_trans = db.query(TranscriptionModel).all()
    print(f'\nTotal transcriptions: {len(all_trans)}')

finally:
    db.close()
