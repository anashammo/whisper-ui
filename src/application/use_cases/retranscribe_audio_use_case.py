"""Use case for re-transcribing existing audio files with different models"""
from datetime import datetime
import uuid
from typing import Optional

from ...domain.entities.transcription import Transcription, TranscriptionStatus
from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ...domain.services.speech_recognition_service import SpeechRecognitionService
from ..dto.transcription_dto import TranscriptionDTO


class RetranscribeAudioUseCase:
    """
    Use case for creating a new transcription from an existing audio file.

    This allows users to transcribe the same audio with different models
    without re-uploading the file.
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        audio_file_repository: AudioFileRepository,
        speech_recognition_service: SpeechRecognitionService
    ):
        self.transcription_repo = transcription_repository
        self.audio_file_repo = audio_file_repository
        self.speech_service = speech_recognition_service

    async def execute(
        self,
        audio_file_id: str,
        model: str,
        language: Optional[str] = None
    ) -> TranscriptionDTO:
        """
        Execute re-transcription workflow.

        Args:
            audio_file_id: ID of existing audio file
            model: Whisper model to use (tiny, base, small, medium, large)
            language: Optional language code

        Returns:
            TranscriptionDTO with new transcription

        Raises:
            ValueError: If audio file not found
        """
        # Step 1: Verify audio file exists
        audio_file = await self.audio_file_repo.get_by_id(audio_file_id)
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")

        # Step 2: Check if transcription with this model already exists
        existing_transcriptions = await self.transcription_repo.get_by_audio_file_id(audio_file_id)
        for trans in existing_transcriptions:
            if trans.model == model and trans.status == TranscriptionStatus.COMPLETED:
                # Return existing transcription instead of creating duplicate
                return TranscriptionDTO.from_entity(trans)

        # Step 3: Create new transcription entity
        transcription = Transcription(
            id=str(uuid.uuid4()),
            audio_file_id=audio_file.id,
            text=None,
            status=TranscriptionStatus.PENDING,
            language=language,
            duration_seconds=audio_file.duration_seconds or 0.0,
            created_at=datetime.utcnow(),
            completed_at=None,
            error_message=None,
            model=model
        )

        # Step 4: Persist transcription
        saved_transcription = await self.transcription_repo.create(transcription)

        # Step 5: Perform transcription
        try:
            saved_transcription.mark_as_processing()
            await self.transcription_repo.update(saved_transcription)

            result = await self.speech_service.transcribe(
                audio_file.file_path,
                language,
                model
            )

            saved_transcription.complete(
                text=result['text'],
                language=result['language'],
                duration_seconds=result.get('duration', audio_file.duration_seconds or 0.0)
            )
        except Exception as e:
            saved_transcription.fail(str(e))

        # Step 6: Final update
        final_transcription = await self.transcription_repo.update(saved_transcription)
        return TranscriptionDTO.from_entity(final_transcription)
