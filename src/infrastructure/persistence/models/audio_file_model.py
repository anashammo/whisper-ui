"""SQLAlchemy model for AudioFile entity"""
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class AudioFileModel(Base):
    """
    SQLAlchemy ORM model for audio files.

    Maps to the 'audio_files' table in the database.
    """
    __tablename__ = "audio_files"

    id = Column(String, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False, unique=True)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    duration_seconds = Column(Float, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship with transcriptions
    transcriptions = relationship(
        "TranscriptionModel",
        back_populates="audio_file",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<AudioFileModel(id={self.id}, "
            f"filename={self.original_filename}, "
            f"size={self.file_size_bytes})>"
        )
