"""Use case for retrieving a single transcription"""
from typing import Optional

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ..dto.transcription_dto import TranscriptionDTO


class GetTranscriptionUseCase:
    """
    Use case for retrieving a specific transcription by ID.
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        audio_file_repository: AudioFileRepository
    ):
        """
        Initialize use case with dependencies.

        Args:
            transcription_repository: Repository for transcriptions
            audio_file_repository: Repository for audio files
        """
        self.transcription_repo = transcription_repository
        self.audio_file_repo = audio_file_repository

    async def execute(self, transcription_id: str) -> Optional[TranscriptionDTO]:
        """
        Retrieve transcription by ID with audio file information.

        Args:
            transcription_id: Unique identifier of the transcription

        Returns:
            TranscriptionDTO if found, None otherwise
        """
        transcription = await self.transcription_repo.get_by_id(transcription_id)

        if not transcription:
            return None

        # Convert to DTO
        dto = TranscriptionDTO.from_entity(transcription)

        # Populate audio file information
        audio_file = await self.audio_file_repo.get_by_id(transcription.audio_file_id)
        if audio_file:
            dto.audio_file_original_filename = audio_file.original_filename
            dto.audio_file_uploaded_at = audio_file.uploaded_at

        return dto
