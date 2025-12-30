"""SQLite implementation of TranscriptionRepository"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ....domain.repositories.transcription_repository import TranscriptionRepository
from ....domain.entities.transcription import Transcription, TranscriptionStatus
from ....domain.exceptions.domain_exception import RepositoryException
from ..models.transcription_model import TranscriptionModel, TranscriptionStatusEnum


class SQLiteTranscriptionRepository(TranscriptionRepository):
    """
    SQLite implementation of the TranscriptionRepository interface.

    Implements persistence operations for Transcription entities using SQLAlchemy.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _to_entity(self, model: TranscriptionModel) -> Transcription:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: SQLAlchemy TranscriptionModel

        Returns:
            Transcription domain entity
        """
        return Transcription(
            id=model.id,
            audio_file_id=model.audio_file_id,
            text=model.text,
            status=TranscriptionStatus(model.status.value),
            language=model.language,
            duration_seconds=model.duration_seconds,
            created_at=model.created_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
            model=model.model,
            processing_time_seconds=model.processing_time_seconds,
            # LLM Enhancement fields
            enable_llm_enhancement=model.enable_llm_enhancement,
            enhanced_text=model.enhanced_text,
            llm_processing_time_seconds=model.llm_processing_time_seconds,
            llm_enhancement_status=model.llm_enhancement_status,
            llm_error_message=model.llm_error_message
        )

    def _to_model(self, entity: Transcription) -> TranscriptionModel:
        """
        Convert domain entity to SQLAlchemy model.

        Args:
            entity: Transcription domain entity

        Returns:
            SQLAlchemy TranscriptionModel
        """
        return TranscriptionModel(
            id=entity.id,
            audio_file_id=entity.audio_file_id,
            text=entity.text,
            status=TranscriptionStatusEnum(entity.status.value),
            language=entity.language,
            duration_seconds=entity.duration_seconds,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
            error_message=entity.error_message,
            model=entity.model,
            processing_time_seconds=entity.processing_time_seconds,
            # LLM Enhancement fields
            enable_llm_enhancement=entity.enable_llm_enhancement,
            enhanced_text=entity.enhanced_text,
            llm_processing_time_seconds=entity.llm_processing_time_seconds,
            llm_enhancement_status=entity.llm_enhancement_status,
            llm_error_message=entity.llm_error_message
        )

    async def create(self, transcription: Transcription) -> Transcription:
        """Create new transcription record"""
        try:
            model = self._to_model(transcription)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            return self._to_entity(model)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryException(f"Failed to create transcription: {str(e)}")

    async def get_by_id(self, transcription_id: str) -> Optional[Transcription]:
        """Retrieve transcription by ID"""
        try:
            model = self.db.query(TranscriptionModel).filter(
                TranscriptionModel.id == transcription_id
            ).first()
            return self._to_entity(model) if model else None
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to retrieve transcription: {str(e)}")

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transcription]:
        """Retrieve all transcriptions with pagination"""
        try:
            models = self.db.query(TranscriptionModel)\
                .order_by(TranscriptionModel.created_at.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [self._to_entity(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to retrieve transcriptions: {str(e)}")

    async def update(self, transcription: Transcription) -> Transcription:
        """Update existing transcription"""
        try:
            model = self.db.query(TranscriptionModel).filter(
                TranscriptionModel.id == transcription.id
            ).first()

            if not model:
                raise RepositoryException(f"Transcription {transcription.id} not found")

            # Update fields
            model.text = transcription.text
            model.status = TranscriptionStatusEnum(transcription.status.value)
            model.language = transcription.language
            model.duration_seconds = transcription.duration_seconds
            model.completed_at = transcription.completed_at
            model.error_message = transcription.error_message
            model.processing_time_seconds = transcription.processing_time_seconds
            # LLM Enhancement fields
            model.enable_llm_enhancement = transcription.enable_llm_enhancement
            model.enhanced_text = transcription.enhanced_text
            model.llm_processing_time_seconds = transcription.llm_processing_time_seconds
            model.llm_enhancement_status = transcription.llm_enhancement_status
            model.llm_error_message = transcription.llm_error_message

            self.db.commit()
            self.db.refresh(model)
            return self._to_entity(model)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryException(f"Failed to update transcription: {str(e)}")

    async def delete(self, transcription_id: str) -> bool:
        """Delete transcription by ID"""
        try:
            result = self.db.query(TranscriptionModel).filter(
                TranscriptionModel.id == transcription_id
            ).delete()
            self.db.commit()
            return result > 0
        except SQLAlchemyError as e:
            self.db.rollback()
            raise RepositoryException(f"Failed to delete transcription: {str(e)}")

    async def get_by_audio_file_id(self, audio_file_id: str) -> List[Transcription]:
        """Retrieve all transcriptions for a specific audio file"""
        try:
            models = self.db.query(TranscriptionModel).filter(
                TranscriptionModel.audio_file_id == audio_file_id
            ).order_by(TranscriptionModel.created_at.desc()).all()
            return [self._to_entity(model) for model in models]
        except SQLAlchemyError as e:
            raise RepositoryException(
                f"Failed to retrieve transcriptions for audio file: {str(e)}"
            )
