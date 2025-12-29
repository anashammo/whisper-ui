"""API router for audio file endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from src.domain.value_objects.model_info import MODEL_VALIDATION_PATTERN
from src.presentation.api.dependencies import (
    get_retranscribe_audio_use_case,
    get_audio_file_transcriptions_use_case,
    get_delete_audio_file_use_case
)
from src.presentation.api.schemas.transcription_schema import TranscriptionResponse
from src.application.use_cases.retranscribe_audio_use_case import RetranscribeAudioUseCase
from src.application.use_cases.get_audio_file_transcriptions_use_case import GetAudioFileTranscriptionsUseCase
from src.application.use_cases.delete_audio_file_use_case import DeleteAudioFileUseCase


router = APIRouter()


@router.post(
    "/audio-files/{audio_file_id}/transcriptions",
    response_model=TranscriptionResponse,
    status_code=201,
    summary="Re-transcribe existing audio file",
    description="Create a new transcription for an existing audio file using a different model. "
                "Allows users to transcribe the same audio with multiple models without re-uploading."
)
async def retranscribe_audio(
    audio_file_id: str,
    model: str = Query(..., pattern=MODEL_VALIDATION_PATTERN, description="Whisper model to use: tiny, base, small, medium, large, turbo"),
    language: Optional[str] = Query(None, max_length=10, description="Optional language code (e.g., 'en', 'es')"),
    use_case: RetranscribeAudioUseCase = Depends(get_retranscribe_audio_use_case)
):
    """
    Re-transcribe an existing audio file with a different model.

    If a completed transcription with the same model already exists, returns the existing one
    instead of creating a duplicate.
    """
    try:
        transcription_dto = await use_case.execute(audio_file_id, model, language)
        return TranscriptionResponse.from_dto(transcription_dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-transcription failed: {str(e)}")


@router.get(
    "/audio-files/{audio_file_id}/transcriptions",
    response_model=List[TranscriptionResponse],
    summary="Get all transcriptions for an audio file",
    description="Retrieve all transcriptions associated with a specific audio file, sorted by creation date (newest first)."
)
async def get_audio_file_transcriptions(
    audio_file_id: str,
    use_case: GetAudioFileTranscriptionsUseCase = Depends(get_audio_file_transcriptions_use_case)
):
    """Get all transcriptions for a specific audio file."""
    try:
        transcription_dtos = await use_case.execute(audio_file_id)
        return [TranscriptionResponse.from_dto(dto) for dto in transcription_dtos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transcriptions: {str(e)}")


@router.delete(
    "/audio-files/{audio_file_id}",
    status_code=204,
    summary="Delete audio file and all transcriptions",
    description="Delete an audio file and all associated transcriptions. This operation cannot be undone."
)
async def delete_audio_file(
    audio_file_id: str,
    use_case: DeleteAudioFileUseCase = Depends(get_delete_audio_file_use_case)
):
    """
    Delete an audio file and all its associated transcriptions.

    This will:
    - Delete the physical audio file from storage
    - Delete all transcriptions for this audio file from the database
    - Delete the audio file record from the database

    Returns 204 No Content on success.
    """
    try:
        await use_case.execute(audio_file_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete audio file: {str(e)}")
