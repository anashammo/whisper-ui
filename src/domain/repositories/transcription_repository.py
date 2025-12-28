"""Transcription repository interface - Domain layer contract"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.transcription import Transcription


class TranscriptionRepository(ABC):
    """
    Abstract repository interface for Transcription entity.

    This interface defines the contract that infrastructure layer
    must implement. Domain layer depends on this abstraction,
    not on concrete implementations (Dependency Inversion Principle).
    """

    @abstractmethod
    async def create(self, transcription: Transcription) -> Transcription:
        """
        Create a new transcription record.

        Args:
            transcription: Transcription entity to create

        Returns:
            Created transcription entity with any generated fields

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, transcription_id: str) -> Optional[Transcription]:
        """
        Retrieve transcription by ID.

        Args:
            transcription_id: Unique identifier of the transcription

        Returns:
            Transcription entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transcription]:
        """
        Retrieve all transcriptions with pagination.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of transcription entities
        """
        pass

    @abstractmethod
    async def update(self, transcription: Transcription) -> Transcription:
        """
        Update an existing transcription.

        Args:
            transcription: Transcription entity with updated fields

        Returns:
            Updated transcription entity

        Raises:
            RepositoryError: If transcription not found or update fails
        """
        pass

    @abstractmethod
    async def delete(self, transcription_id: str) -> bool:
        """
        Delete a transcription by ID.

        Args:
            transcription_id: Unique identifier of the transcription

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
    async def get_by_audio_file_id(self, audio_file_id: str) -> List[Transcription]:
        """
        Retrieve all transcriptions for a specific audio file.

        Args:
            audio_file_id: Audio file identifier

        Returns:
            List of transcription entities
        """
        pass
