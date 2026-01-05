"""API router for transcription endpoints"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
import os

from src.domain.value_objects.model_info import MODEL_VALIDATION_PATTERN
from src.presentation.api.dependencies import (
    get_transcribe_audio_use_case,
    get_transcription_use_case,
    get_transcription_history_use_case,
    get_delete_transcription_use_case
)
from src.presentation.api.schemas.transcription_schema import (
    TranscriptionResponse,
    TranscriptionListResponse
)
from src.application.use_cases.transcribe_audio_use_case import TranscribeAudioUseCase
from src.application.use_cases.get_transcription_use_case import GetTranscriptionUseCase
from src.application.use_cases.get_transcription_history_use_case import GetTranscriptionHistoryUseCase
from src.application.use_cases.delete_transcription_use_case import DeleteTranscriptionUseCase
from src.application.dto.audio_upload_dto import AudioUploadDTO
from src.infrastructure.persistence.repositories.sqlite_audio_file_repository import SQLiteAudioFileRepository
from src.infrastructure.persistence.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/transcriptions",
    response_model=TranscriptionResponse,
    status_code=201,
    summary="Upload and transcribe audio file",
    description="Upload an audio file and transcribe it using Whisper. Supported formats: MP3, WAV, M4A, FLAC, OGG, WEBM."
)
async def create_transcription(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Query(
        None,
        description="Language code (e.g., 'en', 'es', 'fr'). If not specified, language will be auto-detected.",
        max_length=10
    ),
    model: Optional[str] = Query(
        "base",
        description="Whisper model to use: tiny, base, small, medium, large, turbo. Default is 'base'.",
        pattern=MODEL_VALIDATION_PATTERN
    ),
    enable_llm_enhancement: bool = Query(
        False,
        description="Enable LLM enhancement for this transcription (grammar, formatting, filler removal)"
    ),
    vad_filter: bool = Query(
        False,
        description="Enable Voice Activity Detection (filters silence, improves accuracy)"
    ),
    enable_tashkeel: bool = Query(
        False,
        description="Enable Arabic Tashkeel (diacritization) during LLM enhancement. Only applies when enable_llm_enhancement=true and text is Arabic."
    ),
    use_case: TranscribeAudioUseCase = Depends(get_transcribe_audio_use_case)
):
    """
    Upload and transcribe an audio file.

    - **file**: Audio file (MP3, WAV, M4A, FLAC, OGG, WEBM)
    - **language**: Optional language code for transcription

    Returns the transcription with status, text, and metadata.
    """
    try:
        # Read file content
        content = await file.read()

        # Create DTO
        upload_dto = AudioUploadDTO(
            filename=file.filename or "unknown",
            file_content=content,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
            language=language,
            model=model or "base",
            enable_llm_enhancement=enable_llm_enhancement,
            vad_filter=vad_filter,
            enable_tashkeel=enable_tashkeel
        )

        # Debug logging
        print(f"[DEBUG] Upload DTO: enable_llm_enhancement={upload_dto.enable_llm_enhancement}, model={upload_dto.model}")

        # Execute use case
        transcription_dto = await use_case.execute(upload_dto)

        # Map to response schema
        return TranscriptionResponse.from_dto(transcription_dto)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.get(
    "/transcriptions",
    response_model=TranscriptionListResponse,
    summary="Get transcription history",
    description="Retrieve paginated list of all transcriptions."
)
async def get_transcriptions(
    limit: int = Query(
        100,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of results to skip"
    ),
    use_case: GetTranscriptionHistoryUseCase = Depends(get_transcription_history_use_case)
):
    """
    Get paginated transcription history.

    - **limit**: Maximum number of results (1-100)
    - **offset**: Number of results to skip

    Returns list of transcriptions with pagination metadata.
    """
    try:
        transcription_dtos = await use_case.execute(limit, offset)

        return TranscriptionListResponse(
            items=[TranscriptionResponse.from_dto(dto) for dto in transcription_dtos],
            total=len(transcription_dtos),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transcriptions: {str(e)}"
        )


@router.get(
    "/transcriptions/{transcription_id}",
    response_model=TranscriptionResponse,
    summary="Get specific transcription",
    description="Retrieve a specific transcription by ID."
)
async def get_transcription(
    transcription_id: str,
    use_case: GetTranscriptionUseCase = Depends(get_transcription_use_case)
):
    """
    Get a specific transcription by ID.

    - **transcription_id**: Unique identifier of the transcription

    Returns the transcription details.
    """
    try:
        transcription_dto = await use_case.execute(transcription_id)

        if not transcription_dto:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription {transcription_id} not found"
            )

        return TranscriptionResponse.from_dto(transcription_dto)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transcription: {str(e)}"
        )


@router.delete(
    "/transcriptions/{transcription_id}",
    status_code=204,
    summary="Delete transcription",
    description="Delete a transcription and its associated audio file."
)
async def delete_transcription(
    transcription_id: str,
    use_case: DeleteTranscriptionUseCase = Depends(get_delete_transcription_use_case)
):
    """
    Delete a transcription and its associated audio file.

    - **transcription_id**: Unique identifier of the transcription

    Returns 204 No Content on success, 404 if not found.
    """
    try:
        success = await use_case.execute(transcription_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription {transcription_id} not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete transcription: {str(e)}"
        )


@router.get(
    "/transcriptions/{transcription_id}/audio",
    summary="Get audio file",
    description="Stream or download the original audio file for a transcription."
)
async def get_audio_file(
    transcription_id: str,
    download: bool = Query(
        False,
        description="If true, sets Content-Disposition to attachment for download"
    ),
    db: Session = Depends(get_db)
):
    """
    Get the audio file for a specific transcription.

    - **transcription_id**: Unique identifier of the transcription
    - **download**: If True, force download instead of inline playback

    Returns the audio file (streaming or download).
    """
    try:
        # Get transcription to find audio file ID
        from src.infrastructure.persistence.repositories.sqlite_transcription_repository import SQLiteTranscriptionRepository
        transcription_repo = SQLiteTranscriptionRepository(db)
        transcription = await transcription_repo.get_by_id(transcription_id)

        if not transcription:
            raise HTTPException(
                status_code=404,
                detail=f"Transcription {transcription_id} not found"
            )

        # Get audio file
        audio_file_repo = SQLiteAudioFileRepository(db)
        audio_file = await audio_file_repo.get_by_id(transcription.audio_file_id)

        if not audio_file or not audio_file.file_path:
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found for transcription {transcription_id}"
            )

        # Check if file exists on disk
        if not os.path.exists(audio_file.file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Audio file does not exist on disk"
            )

        # Determine Content-Disposition header and media type
        # If download=true, use "attachment" to force download
        # Otherwise, use "inline" for browser playback
        headers = {}
        response_media_type = audio_file.mime_type  # Default to original

        if download:
            # Safely handle None filename with proper extension fallback
            if audio_file.original_filename:
                download_filename = audio_file.original_filename
            else:
                # Derive extension from file_path or default to .wav
                from pathlib import Path
                ext = Path(audio_file.file_path).suffix or '.wav'
                download_filename = f"download{ext}"

            # Check if we need to convert .webm to .wav
            if download_filename.lower().endswith('.webm'):
                download_filename = download_filename[:-5] + '.wav'
                # Update media type to match the new extension
                response_media_type = 'audio/wav'

            headers["Content-Disposition"] = f'attachment; filename="{download_filename}"'

        # Return file
        return FileResponse(
            path=audio_file.file_path,
            media_type=response_media_type,
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audio file: {str(e)}"
        )
