"""Use case for retrieving all transcriptions for an audio file"""
from typing import List

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ..dto.transcription_dto import TranscriptionDTO


class GetAudioFileTranscriptionsUseCase:
    """Use case for retrieving all transcriptions for a specific audio file."""

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        audio_file_repository: AudioFileRepository
    ):
        self.transcription_repo = transcription_repository
        self.audio_file_repo = audio_file_repository

    async def execute(self, audio_file_id: str) -> List[TranscriptionDTO]:
        """
        Get all transcriptions for an audio file.

        Args:
            audio_file_id: ID of the audio file

        Returns:
            List of TranscriptionDTO objects sorted by created_at DESC

        Raises:
            ValueError: If audio file not found
        """
        # Verify audio file exists
        audio_file = await self.audio_file_repo.get_by_id(audio_file_id)
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")

        # Get all transcriptions for this audio file
        transcriptions = await self.transcription_repo.get_by_audio_file_id(audio_file_id)
        return [TranscriptionDTO.from_entity(t) for t in transcriptions]
