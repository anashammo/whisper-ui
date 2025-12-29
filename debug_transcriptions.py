"""Debug script to check transcriptions and audio files in database""" 
import asyncio
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.repositories.sqlite_transcription_repository import SQLiteTranscriptionRepository
from src.infrastructure.persistence.repositories.sqlite_audio_file_repository import SQLiteAudioFileRepository


async def main():
    db = SessionLocal()
    try:
        transcription_repo = SQLiteTranscriptionRepository(db)
        audio_file_repo = SQLiteAudioFileRepository(db)

        # Get all transcriptions
        all_transcriptions = await transcription_repo.get_all(limit=100)
        print(f"\n{'='*60}")
        print(f"Total Transcriptions: {len(all_transcriptions)}")
        print(f"{'='*60}\n")

        # Group by audio file
        by_audio_file = {}
        for trans in all_transcriptions:
            if trans.audio_file_id not in by_audio_file:
                by_audio_file[trans.audio_file_id] = []
            by_audio_file[trans.audio_file_id].append(trans)

        # Show details for each audio file
        for audio_file_id, transcriptions in by_audio_file.items():
            print(f"\nAudio File ID: {audio_file_id}")
            print(f"  Number of transcriptions: {len(transcriptions)}")

            # Try to get audio file details
            try:
                audio_file = await audio_file_repo.get_by_id(audio_file_id)
                if audio_file:
                    print(f"  Original filename: {audio_file.original_filename}")
                    print(f"  Uploaded at: {audio_file.uploaded_at}")
                else:
                    print(f"  [WARNING] Audio file NOT FOUND in database!")
            except Exception as e:
                print(f"  [ERROR] getting audio file: {e}")

            # Show transcription details
            print(f"  Transcriptions:")
            for trans in transcriptions:
                print(f"    - {trans.model or 'unknown'}: {trans.status} (ID: {trans.id})")

        print(f"\n{'='*60}")
        print("Summary:")
        print(f"  Total audio files: {len(by_audio_file)}")
        print(f"  Total transcriptions: {len(all_transcriptions)}")
        print(f"{'='*60}\n")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
