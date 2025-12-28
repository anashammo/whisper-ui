"""Model download progress tracking"""
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import threading


@dataclass
class DownloadProgress:
    """Represents download progress for a model"""
    model_name: str
    status: str  # 'downloading', 'completed', 'cached', 'error'
    progress: float  # 0.0 to 100.0
    bytes_downloaded: int
    total_bytes: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ModelDownloadTracker:
    """
    Singleton class to track model download progress across the application.
    Thread-safe for use in both sync and async contexts.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the tracker"""
        self._progress: Dict[str, DownloadProgress] = {}
        self._lock = threading.Lock()

    async def start_download(self, model_name: str, total_bytes: int = 0):
        """Mark a model download as started"""
        with self._lock:
            self._progress[model_name] = DownloadProgress(
                model_name=model_name,
                status='downloading',
                progress=0.0,
                bytes_downloaded=0,
                total_bytes=total_bytes,
                started_at=datetime.utcnow()
            )

    async def update_progress(self, model_name: str, bytes_downloaded: int, total_bytes: int):
        """Update download progress for a model"""
        with self._lock:
            if model_name in self._progress:
                progress_pct = (bytes_downloaded / total_bytes * 100) if total_bytes > 0 else 0
                self._progress[model_name].bytes_downloaded = bytes_downloaded
                self._progress[model_name].total_bytes = total_bytes
                self._progress[model_name].progress = progress_pct

    async def complete_download(self, model_name: str):
        """Mark a model download as completed"""
        with self._lock:
            if model_name in self._progress:
                self._progress[model_name].status = 'completed'
                self._progress[model_name].progress = 100.0
                self._progress[model_name].completed_at = datetime.utcnow()

    async def mark_cached(self, model_name: str):
        """Mark a model as already cached (no download needed)"""
        with self._lock:
            self._progress[model_name] = DownloadProgress(
                model_name=model_name,
                status='cached',
                progress=100.0,
                bytes_downloaded=0,
                total_bytes=0
            )

    async def set_error(self, model_name: str, error_message: str):
        """Mark a model download as failed"""
        with self._lock:
            if model_name in self._progress:
                self._progress[model_name].status = 'error'
                self._progress[model_name].error_message = error_message

    async def get_progress(self, model_name: str) -> Optional[DownloadProgress]:
        """Get current progress for a model"""
        with self._lock:
            return self._progress.get(model_name)

    async def clear_progress(self, model_name: str):
        """Clear progress tracking for a model"""
        with self._lock:
            if model_name in self._progress:
                del self._progress[model_name]


# Global singleton instance
download_tracker = ModelDownloadTracker()
