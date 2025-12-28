"""FastAPI application initialization"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.presentation.api.routers import transcription_router, health_router, model_router, audio_file_router
from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup: Add ffmpeg to PATH
    project_root = Path(__file__).parent.parent.parent.parent
    ffmpeg_bin = project_root / "ffmpeg-8.0.1-essentials_build" / "bin"
    if ffmpeg_bin.exists():
        os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")
        print(f"Added ffmpeg to PATH: {ffmpeg_bin}")
    else:
        print(f"Warning: ffmpeg not found at {ffmpeg_bin}")

    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")

    yield

    # Shutdown: Cleanup if needed
    print("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Voice-to-text transcription API using OpenAI Whisper",
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health_router.router,
    prefix=settings.api_prefix,
    tags=["health"]
)

app.include_router(
    transcription_router.router,
    prefix=settings.api_prefix,
    tags=["transcriptions"]
)

app.include_router(
    model_router.router,
    prefix=settings.api_prefix,
    tags=["models"]
)

app.include_router(
    audio_file_router.router,
    prefix=settings.api_prefix,
    tags=["audio-files"]
)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Whisper Transcription API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
        "info": f"{settings.api_prefix}/info"
    }
