"""Use case for deleting transcriptions"""
from typing import Optional

from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ..interfaces.file_storage_interface import FileStorageInterface


class DeleteTranscriptionUseCase:
    """
    Use case for deleting a transcription.

    This use case:
    1. Retrieves the transcription
    2. Checks if this is the last transcription for the audio file
    3. Deletes the transcription entity
    4. If this was the last transcription, also deletes the audio file and its storage
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

        # Get all transcriptions for this audio file to check if this is the last one
        all_transcriptions = await self.transcription_repo.get_by_audio_file_id(
            transcription.audio_file_id
        )

        # Delete transcription entity first
        success = await self.transcription_repo.delete(transcription_id)

        # Only delete audio file if this was the last transcription
        if len(all_transcriptions) == 1:
            # This was the last transcription, delete the audio file
            audio_file = await self.audio_file_repo.get_by_id(transcription.audio_file_id)

            if audio_file:
                # Delete audio file from storage
                if audio_file.file_path:
                    try:
                        await self.file_storage.delete(audio_file.file_path)
                    except Exception as e:
                        # Log but don't fail if file doesn't exist
                        print(f"Warning: Failed to delete audio file: {e}")

                # Delete audio file entity
                await self.audio_file_repo.delete(transcription.audio_file_id)

        return success
