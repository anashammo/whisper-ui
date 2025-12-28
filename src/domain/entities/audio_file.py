"""AudioFile entity - Core business logic for audio files"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# Supported audio MIME types for Whisper
SUPPORTED_AUDIO_TYPES = [
    'audio/mpeg',      # MP3
    'audio/mp3',       # MP3 (alternative)
    'audio/wav',       # WAV
    'audio/x-wav',     # WAV (alternative)
    'audio/wave',      # WAV (alternative)
    'audio/mp4',       # M4A
    'audio/x-m4a',     # M4A
    'audio/m4a',       # M4A (alternative)
    'audio/ogg',       # OGG
    'audio/flac',      # FLAC
    'audio/x-flac',    # FLAC (alternative)
    'audio/webm',      # WEBM
]


@dataclass
class AudioFile:
    """
    Audio file entity with validation business rules.

    This entity encapsulates the business logic for audio file handling,
    including file type and size validation.
    """
    id: str
    original_filename: str
    file_path: str
    file_size_bytes: int
    mime_type: str
    duration_seconds: Optional[float]
    uploaded_at: datetime

    def validate_file_type(self) -> bool:
        """
        Business rule: validate that the file type is supported by Whisper.

        Returns:
            bool: True if file type is supported

        Raises:
            ValueError: If file type is not supported
        """
        if self.mime_type not in SUPPORTED_AUDIO_TYPES:
            raise ValueError(
                f"Unsupported file type: {self.mime_type}. "
                f"Supported types: {', '.join(SUPPORTED_AUDIO_TYPES)}"
            )
        return True

    def validate_file_size(self, max_size_mb: int = 25) -> bool:
        """
        Business rule: validate that the file size is within acceptable limits.

        Args:
            max_size_mb: Maximum file size in megabytes (default 25MB)

        Returns:
            bool: True if file size is acceptable

        Raises:
            ValueError: If file size exceeds the limit
        """
        max_bytes = max_size_mb * 1024 * 1024

        if self.file_size_bytes <= 0:
            raise ValueError("File size must be greater than 0")

        if self.file_size_bytes > max_bytes:
            actual_size_mb = self.file_size_bytes / (1024 * 1024)
            raise ValueError(
                f"File size ({actual_size_mb:.2f}MB) exceeds maximum "
                f"allowed size ({max_size_mb}MB)"
            )
        return True

    def validate_duration(self, max_duration_seconds: int = 30) -> bool:
        """
        Business rule: validate that the audio duration is within acceptable limits.

        Args:
            max_duration_seconds: Maximum audio duration in seconds (default 30)

        Returns:
            bool: True if duration is acceptable

        Raises:
            ValueError: If duration exceeds the limit or is not set
        """
        if self.duration_seconds is None:
            raise ValueError("Audio duration must be calculated before validation")

        if self.duration_seconds <= 0:
            raise ValueError("Audio duration must be greater than 0")

        if self.duration_seconds > max_duration_seconds:
            raise ValueError(
                f"Audio duration ({self.duration_seconds:.1f}s) exceeds maximum "
                f"allowed duration ({max_duration_seconds}s)"
            )
        return True

    def validate(self, max_size_mb: int = 25, max_duration_seconds: int = 30) -> bool:
        """
        Perform all validation checks on the audio file.

        Args:
            max_size_mb: Maximum file size in megabytes
            max_duration_seconds: Maximum audio duration in seconds

        Returns:
            bool: True if all validations pass

        Raises:
            ValueError: If any validation fails
        """
        self.validate_file_type()
        self.validate_file_size(max_size_mb)
        if self.duration_seconds is not None:
            self.validate_duration(max_duration_seconds)
        return True

    def get_file_size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.file_size_bytes / (1024 * 1024)

    def get_file_extension(self) -> str:
        """Extract file extension from original filename"""
        if '.' in self.original_filename:
            return self.original_filename.rsplit('.', 1)[1].lower()
        return ''

    def is_valid_filename(self) -> bool:
        """Check if original filename is valid"""
        if not self.original_filename or not self.original_filename.strip():
            return False
        # Check for suspicious characters
        invalid_chars = ['/', '\\', '\0', '<', '>', ':', '"', '|', '?', '*']
        return not any(char in self.original_filename for char in invalid_chars)
