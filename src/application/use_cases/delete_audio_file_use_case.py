"""Use case for deleting audio files with all associated transcriptions"""
from typing import Optional

from ...domain.repositories.audio_file_repository import AudioFileRepository
from ...domain.repositories.transcription_repository import TranscriptionRepository
from ..interfaces.file_storage_interface import FileStorageInterface


class DeleteAudioFileUseCase:
    """
    Use case for deleting an audio file and all its associated transcriptions.

    This ensures cascade deletion of all related data and cleanup of the
    physical audio file from storage.
    """

    def __init__(
        self,
        audio_file_repository: AudioFileRepository,
        transcription_repository: TranscriptionRepository,
        file_storage: FileStorageInterface
    ):
        self.audio_file_repo = audio_file_repository
        self.transcription_repo = transcription_repository
        self.file_storage = file_storage

    async def execute(self, audio_file_id: str) -> None:
        """
        Delete an audio file and all associated transcriptions.

        Args:
            audio_file_id: ID of the audio file to delete

        Raises:
            ValueError: If audio file not found
        """
        # Step 1: Verify audio file exists
        audio_file = await self.audio_file_repo.get_by_id(audio_file_id)
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")

        # Step 2: Get all transcriptions for this audio file
        transcriptions = await self.transcription_repo.get_by_audio_file_id(audio_file_id)

        # Step 3: Delete physical audio file from storage
        try:
            self.file_storage.delete_file(audio_file.file_path)
        except Exception as e:
            # Log but don't fail if file is already gone
            print(f"Warning: Could not delete physical file {audio_file.file_path}: {e}")

        # Step 4: Delete all transcriptions from database
        # Note: With CASCADE DELETE in database, this should happen automatically
        # when we delete the audio file, but we do it explicitly for clarity
        for transcription in transcriptions:
            await self.transcription_repo.delete(transcription.id)

        # Step 5: Delete audio file from database
        await self.audio_file_repo.delete(audio_file_id)
