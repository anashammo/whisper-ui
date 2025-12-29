"""Data Transfer Object for Transcription"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TranscriptionDTO:
    """
    Data Transfer Object for transcription.

    Used to transfer transcription data between layers without exposing
    domain entities directly to the presentation layer.
    """
    id: str
    audio_file_id: str
    text: Optional[str]
    status: str
    language: Optional[str]
    duration_seconds: float
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    model: Optional[str] = None
    audio_file_original_filename: Optional[str] = None  # Denormalized for convenience
    audio_file_uploaded_at: Optional[datetime] = None  # Denormalized for convenience
    processing_time_seconds: Optional[float] = None

    # LLM Enhancement fields
    enable_llm_enhancement: bool = False
    enhanced_text: Optional[str] = None
    llm_processing_time_seconds: Optional[float] = None
    llm_enhancement_status: Optional[str] = None
    llm_error_message: Optional[str] = None

    @classmethod
    def from_entity(cls, transcription):
        """
        Convert domain entity to DTO.

        Args:
            transcription: Transcription domain entity

        Returns:
            TranscriptionDTO instance
        """
        from ...domain.entities.transcription import Transcription

        return cls(
            id=transcription.id,
            audio_file_id=transcription.audio_file_id,
            text=transcription.text,
            status=transcription.status.value,
            language=transcription.language,
            duration_seconds=transcription.duration_seconds,
            created_at=transcription.created_at,
            completed_at=transcription.completed_at,
            error_message=transcription.error_message,
            model=transcription.model,
            processing_time_seconds=transcription.processing_time_seconds,
            # LLM Enhancement fields
            enable_llm_enhancement=transcription.enable_llm_enhancement,
            enhanced_text=transcription.enhanced_text,
            llm_processing_time_seconds=transcription.llm_processing_time_seconds,
            llm_enhancement_status=transcription.llm_enhancement_status,
            llm_error_message=transcription.llm_error_message
        )
