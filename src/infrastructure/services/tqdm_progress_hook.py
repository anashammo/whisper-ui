"""Custom tqdm wrapper to capture Whisper model download progress"""
from tqdm import tqdm as original_tqdm
from typing import Optional
import threading


class TqdmProgressHook(original_tqdm):
    """
    Custom tqdm class that intercepts progress updates and forwards them
    to the download tracker synchronously (thread-safe).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model_name: Optional[str] = None
        self._tracker = None
        self._lock = threading.Lock()

    def set_tracking(self, model_name: str, tracker):
        """Set the model name and tracker for progress updates"""
        self._model_name = model_name
        self._tracker = tracker

    def update(self, n=1):
        """Override update to capture progress"""
        result = super().update(n)

        # Update our download tracker if configured
        if self._model_name and self._tracker and self.total:
            try:
                # The tracker is thread-safe, so we can call it directly
                # Note: We don't await since we're in a sync context
                with self._lock:
                    if self._model_name in self._tracker._progress:
                        progress_pct = (self.n / self.total * 100) if self.total > 0 else 0
                        self._tracker._progress[self._model_name].bytes_downloaded = int(self.n)
                        self._tracker._progress[self._model_name].total_bytes = int(self.total)
                        self._tracker._progress[self._model_name].progress = progress_pct
            except Exception as e:
                # Don't let tracking errors break the download
                print(f"Warning: Failed to update download progress: {e}")

        return result
