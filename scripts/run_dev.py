"""Run development server"""
import uvicorn
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.config.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()

    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Server: {settings.api_host}:{settings.api_port}")
    print(f"Whisper Model: {settings.whisper_model}")
    print(f"Device: {settings.whisper_device}")
    print(f"API Docs: http://{settings.api_host}:{settings.api_port}/docs")
    print("\nPress CTRL+C to stop the server\n")

    uvicorn.run(
        "src.presentation.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
