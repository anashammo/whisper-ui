"""Use case for retrieving transcription history"""
from typing import List

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ..dto.transcription_dto import TranscriptionDTO


class GetTranscriptionHistoryUseCase:
    """
    Use case for retrieving paginated transcription history.
    """

    def __init__(self, transcription_repository: TranscriptionRepository):
        """
        Initialize use case with dependencies.

        Args:
            transcription_repository: Repository for transcriptions
        """
        self.transcription_repo = transcription_repository

    async def execute(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[TranscriptionDTO]:
        """
        Retrieve paginated transcription history.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of TranscriptionDTO objects
        """
        transcriptions = await self.transcription_repo.get_all(limit, offset)
        return [TranscriptionDTO.from_entity(t) for t in transcriptions]
