"""Audio file repository interface - Domain layer contract"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.audio_file import AudioFile


class AudioFileRepository(ABC):
    """
    Abstract repository interface for AudioFile entity.

    This interface defines the contract that infrastructure layer
    must implement for audio file persistence operations.
    """

    @abstractmethod
    async def create(self, audio_file: AudioFile) -> AudioFile:
        """
        Create a new audio file record.

        Args:
            audio_file: AudioFile entity to create

        Returns:
            Created audio file entity

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, audio_file_id: str) -> Optional[AudioFile]:
        """
        Retrieve audio file by ID.

        Args:
            audio_file_id: Unique identifier of the audio file

        Returns:
            AudioFile entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[AudioFile]:
        """
        Retrieve all audio files with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of audio file entities
        """
        pass

    @abstractmethod
    async def delete(self, audio_file_id: str) -> bool:
        """
        Delete an audio file record by ID.

        Args:
            audio_file_id: Unique identifier of the audio file

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass
