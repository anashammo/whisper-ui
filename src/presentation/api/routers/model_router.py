"""Model management API endpoints"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Dict
import asyncio
import json

from ....domain.value_objects.model_info import get_all_models, get_model_info
from ....infrastructure.services.faster_whisper_service import FasterWhisperService
from ....infrastructure.services.model_download_tracker import download_tracker
from ..dependencies import get_whisper_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/status/{model_name}")
async def get_model_status(
    model_name: str,
    whisper_service: FasterWhisperService = Depends(get_whisper_service)
) -> Dict:
    """
    Check the status of a Whisper model.

    Returns:
        - is_cached: Whether the model is already downloaded
        - is_loaded: Whether the model is loaded in memory
        - download_progress: Current download progress (if downloading)
    """
    is_loaded = model_name in whisper_service.models
    is_cached = whisper_service.is_model_cached(model_name)
    progress = await download_tracker.get_progress(model_name)

    response = {
        "model_name": model_name,
        "is_cached": is_cached,
        "is_loaded": is_loaded,
    }

    if progress:
        response["download_progress"] = {
            "status": progress.status,
            "progress": progress.progress,
            "bytes_downloaded": progress.bytes_downloaded,
            "total_bytes": progress.total_bytes,
            "error_message": progress.error_message
        }

    return response


@router.get("/download-progress/{model_name}")
async def stream_download_progress(model_name: str):
    """
    Stream download progress for a model using Server-Sent Events (SSE).

    This endpoint keeps the connection open and sends progress updates
    as they become available.
    """
    async def event_generator():
        """Generate SSE events with download progress"""
        try:
            # Send initial status
            progress = await download_tracker.get_progress(model_name)
            if progress:
                yield f"data: {json.dumps({'status': progress.status, 'progress': progress.progress, 'bytes_downloaded': progress.bytes_downloaded, 'total_bytes': progress.total_bytes})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'unknown', 'progress': 0})}\n\n"

            # Poll for updates every 500ms
            max_duration = 300  # 5 minutes max
            elapsed = 0
            while elapsed < max_duration:
                progress = await download_tracker.get_progress(model_name)

                if progress:
                    data = {
                        'status': progress.status,
                        'progress': progress.progress,
                        'bytes_downloaded': progress.bytes_downloaded,
                        'total_bytes': progress.total_bytes
                    }

                    if progress.error_message:
                        data['error_message'] = progress.error_message

                    yield f"data: {json.dumps(data)}\n\n"

                    # Stop streaming if completed or error
                    if progress.status in ['completed', 'cached', 'error']:
                        break
                else:
                    # No progress info, might be cached or not started
                    yield f"data: {json.dumps({'status': 'unknown', 'progress': 0})}\n\n"

                await asyncio.sleep(0.5)
                elapsed += 0.5

            # Send final completion message
            yield f"data: {json.dumps({'status': 'done'})}\n\n"

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@router.get("/available")
async def get_available_models() -> Dict:
    """
    Get list of available Whisper models with their information.

    Returns model specifications from centralized configuration in
    domain.value_objects.model_info module.
    """
    models = [model.to_dict() for model in get_all_models()]
    return {"models": models}
