"""SQLite implementation of AudioFileRepository"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ....domain.repositories.audio_file_repository import AudioFileRepository
from ....domain.entities.audio_file import AudioFile
from ....domain.exceptions.domain_exception import RepositoryException
from ..models.audio_file_model import AudioFileModel


class SQLiteAudioFileRepository(AudioFileRepository):
    """
    SQLite implementation of the AudioFileRepository interface.

    Implements persistence operations for AudioFile entities using SQLAlchemy.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _to_entity(self, model: AudioFileModel) -> AudioFile:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: SQLAlchemy AudioFileModel

        Returns:
            AudioFile domain entity
        """
        return AudioFile(
            id=model.id,
            original_filename=model.original_filename,
            file_path=model.file_path,
            file_size_bytes=model.file_size_bytes,
            mime_type=model.mime_type,
            duration_seconds=model.duration_seconds,
            uploaded_at=model.uploaded_at
        )

    def _to_model(self, entity: AudioFile) -> AudioFileModel:
        """
        Convert domain entity to SQLAlchemy model.

        Args:
            entity: AudioFile domain entity

        Returns:
            SQLAlchemy AudioFileModel
        """
        return AudioFileModel(
            id=entity.id,
            original_filename=entity.original_filename,
            file_path=entity.file_path,
            file_size_bytes=entity.file_size_bytes,
            mime_type=entity.mime_type,
            duration_seconds=entity.duration_seconds,
            uploaded_at=entity.uploaded_at
        )

    async def create(self, audio_file: AudioFile) -> AudioFile:
        """Create new audio file record"""
        try:
            model = self._to_model(audio_file)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            return self._to_entity(model)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryException(f"Failed to create audio file: {str(e)}")

    async def get_by_id(self, audio_file_id: str) -> Optional[AudioFile]:
        """Retrieve audio file by ID"""
        try:
            model = self.db.query(AudioFileModel).filter(
                AudioFileModel.id == audio_file_id
            ).first()
            return self._to_entity(model) if model else None
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to retrieve audio file: {str(e)}")

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[AudioFile]:
        """Retrieve all audio files with pagination"""
        try:
            models = self.db.query(AudioFileModel)\
                .order_by(AudioFileModel.uploaded_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [self._to_entity(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to retrieve audio files: {str(e)}")

    async def delete(self, audio_file_id: str) -> bool:
        """Delete audio file record by ID"""
        try:
            result = self.db.query(AudioFileModel).filter(
                AudioFileModel.id == audio_file_id
            ).delete()
            self.db.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryException(f"Failed to delete audio file: {str(e)}")
