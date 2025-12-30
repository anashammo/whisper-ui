"""Dependency injection container for FastAPI"""
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session

from ...infrastructure.config.settings import Settings, get_settings
from ...infrastructure.persistence.database import get_db
from ...infrastructure.services.whisper_service import WhisperService
from ...infrastructure.services.llm_enhancement_service_impl import LLMEnhancementServiceImpl
from ...infrastructure.storage.local_file_storage import LocalFileStorage
from ...infrastructure.persistence.repositories.sqlite_transcription_repository import SQLiteTranscriptionRepository
from ...infrastructure.persistence.repositories.sqlite_audio_file_repository import SQLiteAudioFileRepository
from ...application.use_cases.transcribe_audio_use_case import TranscribeAudioUseCase
from ...application.use_cases.get_transcription_use_case import GetTranscriptionUseCase
from ...application.use_cases.get_transcription_history_use_case import GetTranscriptionHistoryUseCase
from ...application.use_cases.delete_transcription_use_case import DeleteTranscriptionUseCase
from ...application.use_cases.retranscribe_audio_use_case import RetranscribeAudioUseCase
from ...application.use_cases.get_audio_file_transcriptions_use_case import GetAudioFileTranscriptionsUseCase
from ...application.use_cases.delete_audio_file_use_case import DeleteAudioFileUseCase
from ...application.use_cases.enhance_transcription_use_case import EnhanceTranscriptionUseCase


# Singleton services (loaded once and reused)
@lru_cache()
def get_whisper_service() -> WhisperService:
    """
    Get Whisper service singleton.

    Whisper model is loaded once and reused across requests
    for performance.

    Returns:
        WhisperService instance
    """
    settings = get_settings()
    return WhisperService(settings)


@lru_cache()
def get_file_storage() -> LocalFileStorage:
    """
    Get file storage service singleton.

    Returns:
        LocalFileStorage instance
    """
    settings = get_settings()
    return LocalFileStorage(settings)


@lru_cache()
def get_llm_enhancement_service() -> LLMEnhancementServiceImpl:
    """
    Get LLM enhancement service singleton.

    LLM client is initialized once and reused across requests
    for performance.

    Returns:
        LLMEnhancementServiceImpl instance
    """
    settings = get_settings()
    return LLMEnhancementServiceImpl(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        temperature=settings.llm_temperature
    )


# Use case factory functions with dependency injection
def get_transcribe_audio_use_case(
    db: Session = Depends(get_db),
    whisper_service: WhisperService = Depends(get_whisper_service),
    file_storage: LocalFileStorage = Depends(get_file_storage),
    llm_service: LLMEnhancementServiceImpl = Depends(get_llm_enhancement_service),
    settings: Settings = Depends(get_settings)
) -> TranscribeAudioUseCase:
    """
    Create TranscribeAudioUseCase with all dependencies injected.

    Args:
        db: Database session
        whisper_service: Whisper service for transcription
        file_storage: File storage service
        llm_service: LLM enhancement service
        settings: Application settings

    Returns:
        TranscribeAudioUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)

    return TranscribeAudioUseCase(
        transcription_repository=transcription_repo,
        audio_file_repository=audio_file_repo,
        speech_recognition_service=whisper_service,
        file_storage=file_storage,
        llm_enhancement_service=llm_service,
        max_file_size_mb=settings.max_file_size_mb,
        max_duration_seconds=settings.max_duration_seconds
    )


def get_transcription_use_case(
    db: Session = Depends(get_db)
) -> GetTranscriptionUseCase:
    """
    Create GetTranscriptionUseCase with dependencies injected.

    Args:
        db: Database session

    Returns:
        GetTranscriptionUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)
    return GetTranscriptionUseCase(transcription_repo, audio_file_repo)


def get_transcription_history_use_case(
    db: Session = Depends(get_db)
) -> GetTranscriptionHistoryUseCase:
    """
    Create GetTranscriptionHistoryUseCase with dependencies injected.

    Args:
        db: Database session

    Returns:
        GetTranscriptionHistoryUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)
    return GetTranscriptionHistoryUseCase(transcription_repo, audio_file_repo)


def get_delete_transcription_use_case(
    db: Session = Depends(get_db),
    file_storage: LocalFileStorage = Depends(get_file_storage)
) -> DeleteTranscriptionUseCase:
    """
    Create DeleteTranscriptionUseCase with dependencies injected.

    Args:
        db: Database session
        file_storage: File storage service

    Returns:
        DeleteTranscriptionUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)

    return DeleteTranscriptionUseCase(
        transcription_repository=transcription_repo,
        audio_file_repository=audio_file_repo,
        file_storage=file_storage
    )


def get_retranscribe_audio_use_case(
    db: Session = Depends(get_db),
    whisper_service: WhisperService = Depends(get_whisper_service),
    llm_service: LLMEnhancementServiceImpl = Depends(get_llm_enhancement_service)
) -> RetranscribeAudioUseCase:
    """
    Create RetranscribeAudioUseCase with dependencies injected.

    Args:
        db: Database session
        whisper_service: Whisper service for transcription
        llm_service: LLM enhancement service

    Returns:
        RetranscribeAudioUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)

    return RetranscribeAudioUseCase(
        transcription_repository=transcription_repo,
        audio_file_repository=audio_file_repo,
        speech_recognition_service=whisper_service,
        llm_enhancement_service=llm_service
    )


def get_audio_file_transcriptions_use_case(
    db: Session = Depends(get_db)
) -> GetAudioFileTranscriptionsUseCase:
    """
    Create GetAudioFileTranscriptionsUseCase with dependencies injected.

    Args:
        db: Database session

    Returns:
        GetAudioFileTranscriptionsUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)

    return GetAudioFileTranscriptionsUseCase(
        transcription_repository=transcription_repo,
        audio_file_repository=audio_file_repo
    )


def get_delete_audio_file_use_case(
    db: Session = Depends(get_db),
    file_storage: LocalFileStorage = Depends(get_file_storage)
) -> DeleteAudioFileUseCase:
    """
    Create DeleteAudioFileUseCase with dependencies injected.

    Args:
        db: Database session
        file_storage: File storage service

    Returns:
        DeleteAudioFileUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)

    return DeleteAudioFileUseCase(
        audio_file_repository=audio_file_repo,
        transcription_repository=transcription_repo,
        file_storage=file_storage
    )


def get_enhance_transcription_use_case(
    db: Session = Depends(get_db),
    llm_service: LLMEnhancementServiceImpl = Depends(get_llm_enhancement_service)
) -> EnhanceTranscriptionUseCase:
    """
    Create EnhanceTranscriptionUseCase with dependencies injected.

    Args:
        db: Database session
        llm_service: LLM enhancement service

    Returns:
        EnhanceTranscriptionUseCase instance
    """
    transcription_repo = SQLiteTranscriptionRepository(db)
    return EnhanceTranscriptionUseCase(transcription_repo, llm_service)
