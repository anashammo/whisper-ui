"""SQLAlchemy model for Transcription entity"""
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base


class TranscriptionStatusEnum(enum.Enum):
    """Database enum for transcription status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptionModel(Base):
    """
    SQLAlchemy ORM model for transcriptions.

    Maps to the 'transcriptions' table in the database.
    """
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True, index=True)
    audio_file_id = Column(
        String,
        ForeignKey("audio_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    text = Column(Text, nullable=True)
    status = Column(
        Enum(TranscriptionStatusEnum),
        default=TranscriptionStatusEnum.PENDING,
        nullable=False,
        index=True
    )
    language = Column(String(10), nullable=True)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    model = Column(String(50), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # LLM Enhancement fields
    enable_llm_enhancement = Column(Boolean, default=False, nullable=False)
    enhanced_text = Column(Text, nullable=True)
    llm_processing_time_seconds = Column(Float, nullable=True)
    llm_enhancement_status = Column(String(20), nullable=True)
    llm_error_message = Column(Text, nullable=True)

    # Relationship with audio file
    audio_file = relationship("AudioFileModel", back_populates="transcriptions")

    def __repr__(self):
        return (
            f"<TranscriptionModel(id={self.id}, "
            f"status={self.status.value}, "
            f"language={self.language})>"
        )
