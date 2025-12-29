"""OpenAI Whisper service implementation with GPU acceleration"""
import whisper
import torch
from typing import Dict, List, Optional
import asyncio
from functools import partial
import os
import sys

from ...domain.services.speech_recognition_service import SpeechRecognitionService
from ...domain.exceptions.domain_exception import ServiceException
from ...domain.value_objects.model_info import get_model_size_bytes
from ..config.settings import Settings
from .model_download_tracker import download_tracker
from .tqdm_progress_hook import TqdmProgressHook


def get_audio_duration(audio_file_path: str) -> float:
    """
    Extract audio duration from file without full transcription.

    Args:
        audio_file_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        Exception: If audio file cannot be loaded
    """
    import os

    # Verify file exists
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found at path: {audio_file_path}")

    # Get file size for debugging
    file_size = os.path.getsize(audio_file_path)
    print(f"Loading audio file: {audio_file_path} (size: {file_size} bytes)")

    try:
        # Load audio using whisper's audio loading (handles various formats)
        # Convert to absolute path for better compatibility on Windows
        abs_path = os.path.abspath(audio_file_path)
        audio = whisper.load_audio(abs_path)

        # Whisper loads at 16kHz sample rate
        duration = len(audio) / whisper.audio.SAMPLE_RATE

        print(f"Audio duration extracted: {duration:.2f} seconds")
        return duration

    except Exception as e:
        raise Exception(f"Failed to load audio from {audio_file_path}: {type(e).__name__}: {str(e)}")


class WhisperService(SpeechRecognitionService):
    """
    OpenAI Whisper implementation of speech recognition service.

    This service uses the openai-whisper library to transcribe audio files
    with GPU acceleration support.
    """

    def __init__(self, settings: Settings):
        """
        Initialize Whisper service with configuration.

        Args:
            settings: Application settings containing Whisper configuration
        """
        self.settings = settings
        self.models = {}  # Cache for loaded models
        self.device = None
        self._initialize_device()

    def _initialize_device(self) -> None:
        """
        Initialize the device (GPU or CPU) for Whisper models.

        Determines whether to use GPU (CUDA) or CPU based on availability
        and configuration settings.
        """
        if self.settings.whisper_device == "cuda" and torch.cuda.is_available():
            self.device = "cuda"
            print(f"GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            self.device = "cpu"
            if self.settings.whisper_device == "cuda":
                print("Warning: CUDA requested but not available. Falling back to CPU.")

    def is_model_cached(self, model_name: str) -> bool:
        """
        Check if a model is already downloaded/cached locally.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is cached, False if it needs to be downloaded
        """
        # Check if already loaded in memory
        if model_name in self.models:
            return True

        # Check if model file exists in Whisper's cache directory
        try:
            # On Windows, cache is in %USERPROFILE%\.cache\whisper
            # On Unix, cache is in ~/.cache/whisper
            home = os.path.expanduser("~")
            cache_dir = os.path.join(home, ".cache", "whisper")
            model_file = f"{model_name}.pt"
            model_path = os.path.join(cache_dir, model_file)
            exists = os.path.exists(model_path)
            print(f"Checking model cache: {model_path} - exists: {exists}")
            return exists
        except Exception as e:
            print(f"Error checking model cache: {e}")
            return False

    async def _load_model_async(self, model_name: str = "base"):
        """
        Load a specific Whisper model asynchronously with progress tracking.

        Args:
            model_name: Name of the model (tiny, base, small, medium, large)

        Returns:
            Loaded Whisper model

        Raises:
            ServiceException: If model loading fails
        """
        # Check if model is already loaded in memory
        if model_name in self.models:
            print(f"Using cached Whisper model '{model_name}'")
            await download_tracker.mark_cached(model_name)
            return self.models[model_name]

        # Check if model needs to be downloaded
        is_cached = self.is_model_cached(model_name)

        if is_cached:
            print(f"Model '{model_name}' found in cache, loading...")
            await download_tracker.mark_cached(model_name)
        else:
            print(f"Model '{model_name}' not cached, will download...")
            # Get estimated model size from centralized configuration
            try:
                estimated_size = get_model_size_bytes(model_name)
            except KeyError:
                # Fallback to base model size if invalid model name
                estimated_size = 150 * 1024 * 1024
            await download_tracker.start_download(model_name, estimated_size)

            # Monkey-patch tqdm in the whisper module to capture download progress
            original_tqdm = whisper.tqdm

            def create_hooked_tqdm(*args, **kwargs):
                """Create a tqdm instance with our progress hook"""
                instance = TqdmProgressHook(*args, **kwargs)
                instance.set_tracking(model_name, download_tracker)
                return instance

            whisper.tqdm = create_hooked_tqdm

        try:
            # Load model in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None,
                partial(whisper.load_model, model_name, self.device)
            )

            self.models[model_name] = model
            print(f"Whisper model '{model_name}' loaded successfully on {self.device}")

            if not is_cached:
                # Restore original tqdm
                if hasattr(whisper, 'tqdm'):
                    whisper.tqdm = original_tqdm
                await download_tracker.complete_download(model_name)

            return model

        except Exception as e:
            if not is_cached:
                # Restore original tqdm on error
                if 'original_tqdm' in locals():
                    whisper.tqdm = original_tqdm
                await download_tracker.set_error(model_name, str(e))
            raise ServiceException(f"Failed to load Whisper model '{model_name}': {str(e)}")

    def _load_model(self, model_name: str = "base"):
        """
        Synchronous wrapper for _load_model_async (for backward compatibility).

        Args:
            model_name: Name of the model (tiny, base, small, medium, large)

        Returns:
            Loaded Whisper model
        """
        # For sync calls, just load directly without progress tracking
        if model_name in self.models:
            return self.models[model_name]

        model = whisper.load_model(model_name, device=self.device)
        self.models[model_name] = model
        return model

    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        model_name: str = "base"
    ) -> Dict[str, any]:
        """
        Transcribe audio file using Whisper.

        Whisper's transcribe method is CPU/GPU-bound and synchronous,
        so we run it in a thread pool to avoid blocking the event loop.

        Args:
            audio_file_path: Path to the audio file on disk
            language: Optional language code (e.g., 'en', 'es', 'fr')
            model_name: Whisper model to use (tiny, base, small, medium, large)

        Returns:
            Dictionary with transcription results:
                - text: Transcribed text
                - language: Detected or specified language
                - duration: Audio duration in seconds
                - model: Model used for transcription

        Raises:
            ServiceException: If transcription fails
        """
        try:
            # Load the specified model with progress tracking
            model = await self._load_model_async(model_name)

            # Run transcription in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                partial(
                    self._transcribe_sync,
                    audio_file_path,
                    language,
                    model
                )
            )
            result['model'] = model_name  # Add model info to result
            return result

        except Exception as e:
            raise ServiceException(f"Transcription failed: {str(e)}")

    def _transcribe_sync(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        model = None
    ) -> Dict[str, any]:
        """
        Synchronous transcription method (runs in thread pool).

        Args:
            audio_file_path: Path to audio file
            language: Optional language code
            model: Whisper model to use

        Returns:
            Dictionary with transcription results
        """
        # Prepare transcription options
        options = {
            "fp16": self.device == "cuda",  # Use FP16 for GPU, FP32 for CPU
            "language": language if language else None,
        }

        # Perform transcription
        result = model.transcribe(audio_file_path, **options)

        # Extract and return relevant information
        return {
            "text": result["text"].strip(),
            "language": result.get("language", language or "unknown"),
            "duration": result.get("duration", 0.0)
        }

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO language codes supported by Whisper
        """
        # Whisper supports 99 languages
        return list(whisper.tokenizer.LANGUAGES.keys())

    def is_language_supported(self, language_code: str) -> bool:
        """
        Check if a language code is supported.

        Args:
            language_code: ISO language code to check

        Returns:
            True if language is supported
        """
        return language_code in self.get_supported_languages()

    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.settings.whisper_model,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "supported_languages_count": len(self.get_supported_languages())
        }
