"""API router for health check endpoints"""
from fastapi import APIRouter, Depends
from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.api.dependencies import get_whisper_service
from src.infrastructure.services.faster_whisper_service import FasterWhisperService

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running and healthy."
)
async def health_check():
    """
    Health check endpoint.

    Returns basic status information about the API.
    """
    return {
        "status": "healthy",
        "message": "Whisper Transcription API is running"
    }


@router.get(
    "/info",
    summary="System information",
    description="Get information about the system and loaded models."
)
async def system_info(
    whisper_service: FasterWhisperService = Depends(get_whisper_service),
    settings: Settings = Depends(get_settings)
):
    """
    Get system information.

    Returns information about the loaded Whisper model and configuration.
    """
    model_info = whisper_service.get_model_info()

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "whisper_model": model_info,
        "max_file_size_mb": settings.max_file_size_mb,
        "supported_languages_count": len(whisper_service.get_supported_languages())
    }
