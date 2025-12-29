"""Use case for retrieving transcription history"""
from typing import List, Dict

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ..dto.transcription_dto import TranscriptionDTO


class GetTranscriptionHistoryUseCase:
    """
    Use case for retrieving paginated transcription history.
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

    async def execute(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[TranscriptionDTO]:
        """
        Retrieve paginated transcription history with audio file information.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of TranscriptionDTO objects with audio_file_original_filename and audio_file_uploaded_at populated
        """
        transcriptions = await self.transcription_repo.get_all(limit, offset)

        # Get unique audio file IDs
        audio_file_ids = {t.audio_file_id for t in transcriptions}

        # Fetch all audio files in one go
        audio_files_map = {}  # audio_file_id -> AudioFile entity
        for audio_file_id in audio_file_ids:
            audio_file = await self.audio_file_repo.get_by_id(audio_file_id)
            if audio_file:
                audio_files_map[audio_file_id] = audio_file

        # Convert to DTOs and populate audio file information
        result = []
        for t in transcriptions:
            dto = TranscriptionDTO.from_entity(t)
            audio_file = audio_files_map.get(t.audio_file_id)
            if audio_file:
                dto.audio_file_original_filename = audio_file.original_filename
                dto.audio_file_uploaded_at = audio_file.uploaded_at
            result.append(dto)

        return result
