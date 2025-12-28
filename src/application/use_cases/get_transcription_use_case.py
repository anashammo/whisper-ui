"""Use case for retrieving a single transcription"""
from typing import Optional

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ..dto.transcription_dto import TranscriptionDTO


class GetTranscriptionUseCase:
    """
    Use case for retrieving a specific transcription by ID.
    """

    def __init__(self, transcription_repository: TranscriptionRepository):
        """
        Initialize use case with dependencies.

        Args:
            transcription_repository: Repository for transcriptions
        """
        self.transcription_repo = transcription_repository

    async def execute(self, transcription_id: str) -> Optional[TranscriptionDTO]:
        """
        Retrieve transcription by ID.

        Args:
            transcription_id: Unique identifier of the transcription

        Returns:
            TranscriptionDTO if found, None otherwise
        """
        transcription = await self.transcription_repo.get_by_id(transcription_id)

        if not transcription:
            return None

        return TranscriptionDTO.from_entity(transcription)
