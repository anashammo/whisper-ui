"""Transcription entity - Core business logic for transcriptions"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class TranscriptionStatus(Enum):
    """Enumeration of transcription statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Transcription:
    """
    Core transcription entity with business rules.

    This entity encapsulates the business logic for audio transcriptions,
    including status transitions and validation rules.
    """
    id: str
    audio_file_id: str
    text: Optional[str]
    status: TranscriptionStatus
    language: Optional[str]
    duration_seconds: float
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str] = None

    def mark_as_processing(self) -> None:
        """
        Business rule: can only process pending transcriptions.

        Raises:
            ValueError: If transcription is not in PENDING state
        """
        if self.status != TranscriptionStatus.PENDING:
            raise ValueError(
                f"Cannot process transcription in {self.status.value} state. "
                f"Only PENDING transcriptions can be marked as PROCESSING."
            )
        self.status = TranscriptionStatus.PROCESSING

    def complete(self, text: str, language: str, duration: float = None) -> None:
        """
        Business rule: complete the transcription with results.

        Args:
            text: The transcribed text
            language: Detected language code
            duration: Optional duration in seconds

        Raises:
            ValueError: If transcription is not in PROCESSING state
        """
        if self.status != TranscriptionStatus.PROCESSING:
            raise ValueError(
                f"Cannot complete transcription in {self.status.value} state. "
                f"Only PROCESSING transcriptions can be completed."
            )

        # Allow empty transcription (no speech detected)
        if text and text.strip():
            self.text = text.strip()
        else:
            self.text = "(No speech detected)"

        self.language = language
        if duration is not None:
            self.duration_seconds = duration
        self.status = TranscriptionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.error_message = None

    def fail(self, error_message: str) -> None:
        """
        Business rule: mark transcription as failed with error message.

        Args:
            error_message: Description of the failure
        """
        if not error_message or not error_message.strip():
            raise ValueError("Error message cannot be empty")

        self.status = TranscriptionStatus.FAILED
        self.error_message = error_message.strip()
        self.completed_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Check if transcription is completed successfully"""
        return self.status == TranscriptionStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if transcription has failed"""
        return self.status == TranscriptionStatus.FAILED

    def is_in_progress(self) -> bool:
        """Check if transcription is currently processing"""
        return self.status == TranscriptionStatus.PROCESSING

    def is_pending(self) -> bool:
        """Check if transcription is pending"""
        return self.status == TranscriptionStatus.PENDING

    def can_be_deleted(self) -> bool:
        """
        Business rule: determine if transcription can be deleted.
        Processing transcriptions should not be deleted to avoid inconsistency.
        """
        return self.status in [
            TranscriptionStatus.COMPLETED,
            TranscriptionStatus.FAILED,
            TranscriptionStatus.PENDING
        ]
