"""Pydantic schemas for API request/response models"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TranscriptionResponse(BaseModel):
    """API response schema for transcription"""
    id: str
    audio_file_id: str
    text: Optional[str] = None
    status: str
    language: Optional[str] = None
    duration_seconds: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    model: Optional[str] = None
    audio_file_original_filename: Optional[str] = None
    audio_file_uploaded_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None

    # LLM Enhancement fields
    enable_llm_enhancement: bool = False
    enhanced_text: Optional[str] = None
    llm_processing_time_seconds: Optional[float] = None
    llm_enhancement_status: Optional[str] = None
    llm_error_message: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "audio_file_id": "660e8400-e29b-41d4-a716-446655440001",
                "text": "This is the transcribed text from the audio file.",
                "status": "completed",
                "language": "en",
                "model": "base",
                "duration_seconds": 45.3,
                "processing_time_seconds": 12.84,
                "created_at": "2025-12-28T10:30:00Z",
                "completed_at": "2025-12-28T10:30:15Z",
                "error_message": None
            }
        }

    @classmethod
    def from_dto(cls, dto):
        """
        Convert DTO to API response schema.

        Args:
            dto: TranscriptionDTO instance

        Returns:
            TranscriptionResponse instance
        """
        return cls(
            id=dto.id,
            audio_file_id=dto.audio_file_id,
            text=dto.text,
            status=dto.status,
            language=dto.language,
            duration_seconds=dto.duration_seconds,
            created_at=dto.created_at,
            completed_at=dto.completed_at,
            error_message=dto.error_message,
            model=dto.model,
            audio_file_original_filename=dto.audio_file_original_filename,
            audio_file_uploaded_at=dto.audio_file_uploaded_at,
            processing_time_seconds=dto.processing_time_seconds,
            # LLM Enhancement fields
            enable_llm_enhancement=dto.enable_llm_enhancement,
            enhanced_text=dto.enhanced_text,
            llm_processing_time_seconds=dto.llm_processing_time_seconds,
            llm_enhancement_status=dto.llm_enhancement_status,
            llm_error_message=dto.llm_error_message
        )


class TranscriptionListResponse(BaseModel):
    """Paginated list of transcriptions"""
    items: List[TranscriptionResponse]
    total: int
    limit: int
    offset: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 10,
                "limit": 100,
                "offset": 0
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    error_type: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Transcription not found",
                "error_type": "NotFound"
            }
        }
