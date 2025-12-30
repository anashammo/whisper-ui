"""API router for LLM enhancement endpoints"""
from fastapi import APIRouter, Depends, HTTPException

from src.presentation.api.dependencies import get_enhance_transcription_use_case
from src.presentation.api.schemas.transcription_schema import TranscriptionResponse
from src.application.use_cases.enhance_transcription_use_case import EnhanceTranscriptionUseCase


router = APIRouter()


@router.post(
    "/transcriptions/{transcription_id}/enhance",
    response_model=TranscriptionResponse,
    summary="Enhance transcription with LLM",
    description="Enhance completed transcription using local LLM for grammar correction, formatting, and filler word removal"
)
async def enhance_transcription(
    transcription_id: str,
    use_case: EnhanceTranscriptionUseCase = Depends(get_enhance_transcription_use_case)
):
    """
    Enhance a completed transcription with LLM.

    This endpoint:
    - Validates the transcription can be enhanced (must be completed, LLM enabled)
    - Calls local LLM to enhance the text
    - Returns the enhanced transcription with processing time

    Args:
        transcription_id: ID of transcription to enhance

    Returns:
        TranscriptionResponse with enhanced text

    Raises:
        400: If transcription cannot be enhanced
        404: If transcription not found
        500: If enhancement fails
    """
    try:
        transcription_dto = await use_case.execute(transcription_id)
        return TranscriptionResponse.from_dto(transcription_dto)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )
