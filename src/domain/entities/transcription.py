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
    model: Optional[str] = None
    processing_time_seconds: Optional[float] = None

    # LLM Enhancement fields
    enable_llm_enhancement: bool = False
    enhanced_text: Optional[str] = None
    llm_processing_time_seconds: Optional[float] = None
    llm_enhancement_status: Optional[str] = None  # 'pending', 'processing', 'completed', 'failed'
    llm_error_message: Optional[str] = None

    # Voice Activity Detection (VAD) field
    vad_filter_used: bool = False  # Whether VAD was enabled during transcription

    # Arabic Tashkeel (Diacritization) field
    enable_tashkeel: bool = False  # Whether to add Arabic diacritics during LLM enhancement

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

    def complete(self, text: str, language: str, duration: float = None, processing_time: float = None) -> None:
        """
        Business rule: complete the transcription with results.

        Args:
            text: The transcribed text
            language: Detected language code
            duration: Optional duration in seconds
            processing_time: Optional processing time in seconds (time spent by Whisper)

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
        if processing_time is not None:
            self.processing_time_seconds = processing_time
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

    def can_be_enhanced(self) -> bool:
        """
        Business rule: determine if transcription can be enhanced with LLM.

        A transcription can be enhanced if:
        - LLM enhancement is enabled for this transcription
        - Transcription is completed successfully
        - Has non-empty text
        - Has not been enhanced yet OR enhancement failed (allow retry)

        Returns:
            bool: True if transcription can be enhanced
        """
        return (
            self.enable_llm_enhancement and
            self.status == TranscriptionStatus.COMPLETED and
            self.text is not None and
            self.text.strip() != "" and
            self.text != "(No speech detected)" and
            self.llm_enhancement_status in [None, 'failed']  # Not enhanced or failed (can retry)
        )

    def mark_llm_processing(self) -> None:
        """
        Business rule: mark LLM enhancement as processing.

        Raises:
            ValueError: If transcription cannot be enhanced
        """
        if not self.can_be_enhanced():
            raise ValueError(
                f"Transcription cannot be enhanced. "
                f"enable_llm_enhancement={self.enable_llm_enhancement}, "
                f"status={self.status.value}, "
                f"text={'empty' if not self.text else 'present'}, "
                f"llm_enhancement_status={self.llm_enhancement_status}"
            )
        self.llm_enhancement_status = 'processing'

    def complete_llm_enhancement(self, enhanced_text: str, processing_time: float) -> None:
        """
        Business rule: complete LLM enhancement with results.

        Args:
            enhanced_text: The enhanced transcription text from LLM
            processing_time: Time taken for LLM enhancement in seconds

        Raises:
            ValueError: If LLM enhancement is not in processing state or text is empty
        """
        if self.llm_enhancement_status != 'processing':
            raise ValueError(
                f"Cannot complete LLM enhancement in {self.llm_enhancement_status} state. "
                f"Only 'processing' enhancements can be completed."
            )

        if not enhanced_text or not enhanced_text.strip():
            raise ValueError("Enhanced text cannot be empty")

        self.enhanced_text = enhanced_text.strip()
        self.llm_processing_time_seconds = processing_time
        self.llm_enhancement_status = 'completed'
        self.llm_error_message = None

    def fail_llm_enhancement(self, error_message: str) -> None:
        """
        Business rule: mark LLM enhancement as failed with error message.

        Args:
            error_message: Description of the failure

        Raises:
            ValueError: If error message is empty
        """
        if not error_message or not error_message.strip():
            raise ValueError("Error message cannot be empty")

        self.llm_enhancement_status = 'failed'
        self.llm_error_message = error_message.strip()
        # Keep enhanced_text as None when failed

    def is_llm_enhanced(self) -> bool:
        """Check if transcription has been enhanced with LLM successfully"""
        return self.llm_enhancement_status == 'completed' and self.enhanced_text is not None
