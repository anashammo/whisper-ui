"""Data Transfer Object for Audio Upload"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioUploadDTO:
    """
    Data Transfer Object for audio file uploads.

    Encapsulates all data needed for audio file upload and transcription.
    """
    filename: str
    file_content: bytes
    file_size: int
    mime_type: str
    language: Optional[str] = None
    model: Optional[str] = "base"  # Whisper model: tiny, base, small, medium, large

    def __post_init__(self):
        """Validate DTO after initialization"""
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if not self.file_content:
            raise ValueError("File content cannot be empty")
        if self.file_size <= 0:
            raise ValueError("File size must be greater than 0")
        if not self.mime_type:
            raise ValueError("MIME type cannot be empty")
