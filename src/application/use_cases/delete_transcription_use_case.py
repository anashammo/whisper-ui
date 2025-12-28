"""Use case for deleting transcriptions"""
from typing import Optional

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ..interfaces.file_storage_interface import FileStorageInterface


class DeleteTranscriptionUseCase:
    """
    Use case for deleting a transcription and its associated audio file.

    This use case:
    1. Retrieves the transcription
    2. Retrieves the associated audio file
    3. Deletes the audio file from storage
    4. Deletes the audio file entity
    5. Deletes the transcription entity
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        audio_file_repository: AudioFileRepository,
        file_storage: FileStorageInterface
    ):
        """
        Initialize use case with dependencies.

        Args:
            transcription_repository: Repository for transcriptions
            audio_file_repository: Repository for audio files
            file_storage: Service for file storage
        """
        self.transcription_repo = transcription_repository
        self.audio_file_repo = audio_file_repository
        self.file_storage = file_storage

    async def execute(self, transcription_id: str) -> bool:
        """
        Execute the delete workflow.

        Args:
            transcription_id: ID of the transcription to delete

        Returns:
            True if deletion was successful, False if not found

        Raises:
            Exception: If deletion fails
        """
        # Get transcription
        transcription = await self.transcription_repo.get_by_id(transcription_id)
        if not transcription:
            return False

        # Get associated audio file
        audio_file = await self.audio_file_repo.get_by_id(transcription.audio_file_id)

        # Delete audio file from storage if it exists
        if audio_file and audio_file.file_path:
            try:
                await self.file_storage.delete(audio_file.file_path)
            except Exception as e:
                # Log but don't fail if file doesn't exist
                print(f"Warning: Failed to delete audio file: {e}")

        # Delete audio file entity
        if audio_file:
            await self.audio_file_repo.delete(transcription.audio_file_id)

        # Delete transcription entity
        success = await self.transcription_repo.delete(transcription_id)

        return success
