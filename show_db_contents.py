"""Show current database contents""" 
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
            print()
    else:
        print('  (No audio files in database)')

    # Check for transcriptions
    all_trans = db.query(TranscriptionModel).all()
    print(f'\nTotal transcriptions: {len(all_trans)}')

finally:
    db.close()
