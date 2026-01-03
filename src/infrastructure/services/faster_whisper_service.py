"""faster-whisper service implementation with GPU acceleration and VAD support"""
import torch
from faster_whisper import WhisperModel
from typing import Dict, List, Optional
import asyncio
from functools import partial
import os

from ...domain.services.speech_recognition_service import SpeechRecognitionService
from ...domain.exceptions.domain_exception import ServiceException
from ...domain.value_objects.model_info import get_model_size_bytes
from ..config.settings import Settings
from .model_download_tracker import download_tracker


def get_audio_duration(audio_file_path: str) -> float:
    """
    Extract audio duration from file using PyAV (bundled with faster-whisper).

    Args:
        audio_file_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        Exception: If audio file cannot be loaded
    """
    import av

    # Verify file exists
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found at path: {audio_file_path}")

    # Get file size for debugging
    file_size = os.path.getsize(audio_file_path)
    print(f"Loading audio file: {audio_file_path} (size: {file_size} bytes)")

    try:
        # Use PyAV to extract duration (bundled with faster-whisper)
        abs_path = os.path.abspath(audio_file_path)
        with av.open(abs_path) as container:
            # Get the audio stream
            stream = container.streams.audio[0]
            # Calculate duration from stream metadata
            if stream.duration is not None and stream.time_base is not None:
                duration = float(stream.duration * stream.time_base)
            else:
                # Fallback: decode the entire file to get duration
                duration = float(container.duration) / 1000000.0  # Convert from microseconds

        print(f"Audio duration extracted: {duration:.2f} seconds")
        return duration

    except Exception as e:
        raise Exception(f"Failed to load audio from {audio_file_path}: {type(e).__name__}: {str(e)}")


# Supported languages (ISO 639-1 codes) - from faster-whisper/Whisper
SUPPORTED_LANGUAGES = [
    "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs",
    "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi",
    "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy",
    "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb",
    "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt",
    "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru",
    "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw",
    "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi",
    "yi", "yo", "zh", "yue"
]


class FasterWhisperService(SpeechRecognitionService):
    """
    faster-whisper implementation of speech recognition service.

    Uses CTranslate2 backend for improved performance (up to 4x faster than OpenAI Whisper).
    Supports Voice Activity Detection (VAD) to filter silence and improve accuracy.
    """

    def __init__(self, settings: Settings):
        """
        Initialize faster-whisper service with configuration.

        Args:
            settings: Application settings containing Whisper configuration
        """
        self.settings = settings
        self.models: Dict[str, WhisperModel] = {}  # Cache for loaded models
        self.device: Optional[str] = None
        self.compute_type: Optional[str] = None
        self._initialize_device()

    def _initialize_device(self) -> None:
        """
        Initialize the device (GPU or CPU) and compute type for faster-whisper.

        Determines whether to use GPU (CUDA) or CPU based on availability
        and configuration settings. Sets appropriate compute type for each.
        """
        if self.settings.whisper_device == "cuda" and torch.cuda.is_available():
            self.device = "cuda"
            self.compute_type = "float16"  # FP16 for GPU (faster, lower memory)
            print(f"GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            print(f"Using compute type: {self.compute_type}")
        else:
            self.device = "cpu"
            self.compute_type = "int8"  # INT8 quantization for CPU (faster)
            if self.settings.whisper_device == "cuda":
                print("Warning: CUDA requested but not available. Falling back to CPU.")
            print(f"Using CPU with compute type: {self.compute_type}")

    def is_model_cached(self, model_name: str) -> bool:
        """
        Check if a model is already downloaded/cached locally.

        faster-whisper uses HuggingFace Hub for model storage. Models are cached
        in ~/.cache/huggingface/hub/ directory.

        Args:
            model_name: Name of the model to check (tiny, base, small, medium, large, turbo)

        Returns:
            True if model is cached, False if it needs to be downloaded
        """
        # Check if already loaded in memory
        if model_name in self.models:
            return True

        try:
            # Try to check HuggingFace cache
            from huggingface_hub import try_to_load_from_cache

            # Map model names to HuggingFace repo IDs
            repo_map = {
                "tiny": "Systran/faster-whisper-tiny",
                "tiny.en": "Systran/faster-whisper-tiny.en",
                "base": "Systran/faster-whisper-base",
                "base.en": "Systran/faster-whisper-base.en",
                "small": "Systran/faster-whisper-small",
                "small.en": "Systran/faster-whisper-small.en",
                "medium": "Systran/faster-whisper-medium",
                "medium.en": "Systran/faster-whisper-medium.en",
                "large": "Systran/faster-whisper-large-v3",
                "large-v1": "Systran/faster-whisper-large-v1",
                "large-v2": "Systran/faster-whisper-large-v2",
                "large-v3": "Systran/faster-whisper-large-v3",
                "turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
                "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
            }

            repo_id = repo_map.get(model_name, f"Systran/faster-whisper-{model_name}")

            # Check if model.bin exists in cache (main model file)
            cached = try_to_load_from_cache(repo_id, "model.bin")
            if cached is not None:
                print(f"Model '{model_name}' found in HuggingFace cache")
                return True

            print(f"Model '{model_name}' not found in cache")
            return False

        except Exception as e:
            print(f"Error checking model cache: {e}")
            return False

    async def _load_model_async(self, model_name: str = "base") -> WhisperModel:
        """
        Load a specific faster-whisper model asynchronously with progress tracking.

        Args:
            model_name: Name of the model (tiny, base, small, medium, large, turbo)

        Returns:
            Loaded WhisperModel instance

        Raises:
            ServiceException: If model loading fails
        """
        # Check if model is already loaded in memory
        if model_name in self.models:
            print(f"Using cached faster-whisper model '{model_name}'")
            await download_tracker.mark_cached(model_name)
            return self.models[model_name]

        # Check if model needs to be downloaded
        is_cached = self.is_model_cached(model_name)

        if is_cached:
            print(f"Model '{model_name}' found in cache, loading...")
            await download_tracker.mark_cached(model_name)
        else:
            print(f"Model '{model_name}' not cached, will download from HuggingFace Hub...")
            # Get estimated model size from centralized configuration
            try:
                estimated_size = get_model_size_bytes(model_name)
            except KeyError:
                # Fallback to base model size if invalid model name
                estimated_size = 150 * 1024 * 1024
            await download_tracker.start_download(model_name, estimated_size)

        try:
            # Load model in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None,
                partial(self._load_model_sync, model_name)
            )

            self.models[model_name] = model
            print(f"faster-whisper model '{model_name}' loaded successfully on {self.device}")

            if not is_cached:
                await download_tracker.complete_download(model_name)

            return model

        except Exception as e:
            if not is_cached:
                await download_tracker.set_error(model_name, str(e))
            raise ServiceException(f"Failed to load faster-whisper model '{model_name}': {str(e)}")

    def _load_model_sync(self, model_name: str) -> WhisperModel:
        """
        Synchronously load a faster-whisper model.

        Args:
            model_name: Name of the model

        Returns:
            Loaded WhisperModel instance
        """
        return WhisperModel(
            model_name,
            device=self.device,
            compute_type=self.compute_type
        )

    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        model_name: str = "base",
        vad_filter: bool = False
    ) -> Dict[str, any]:
        """
        Transcribe audio file using faster-whisper with optional VAD.

        faster-whisper's transcribe method is CPU/GPU-bound and synchronous,
        so we run it in a thread pool to avoid blocking the event loop.

        Args:
            audio_file_path: Path to the audio file on disk
            language: Optional language code (e.g., 'en', 'es', 'fr')
            model_name: faster-whisper model to use (tiny, base, small, medium, large, turbo)
            vad_filter: Whether to enable Voice Activity Detection

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
                    model,
                    vad_filter
                )
            )
            result['model'] = model_name  # Add model info to result
            return result

        except Exception as e:
            raise ServiceException(f"Transcription failed: {str(e)}")

    def _transcribe_sync(
        self,
        audio_file_path: str,
        language: Optional[str],
        model: WhisperModel,
        vad_filter: bool
    ) -> Dict[str, any]:
        """
        Synchronous transcription method (runs in thread pool).

        Args:
            audio_file_path: Path to audio file
            language: Optional language code
            model: faster-whisper WhisperModel to use
            vad_filter: Whether to enable VAD

        Returns:
            Dictionary with transcription results
        """
        # Prepare VAD parameters if enabled
        vad_parameters = None
        if vad_filter:
            vad_parameters = {
                "min_silence_duration_ms": 500,  # Minimum silence duration to split
                "speech_pad_ms": 200,  # Padding around speech segments
            }

        # Perform transcription
        # Note: faster-whisper returns a generator of segments and transcription info
        segments, info = model.transcribe(
            audio_file_path,
            language=language,
            beam_size=5,
            vad_filter=vad_filter,
            vad_parameters=vad_parameters
        )

        # Collect all segment text (segments is a generator)
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts).strip()

        # Return results
        return {
            "text": full_text if full_text else "(No speech detected)",
            "language": info.language,
            "duration": info.duration
        }

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO language codes supported by faster-whisper
        """
        return SUPPORTED_LANGUAGES.copy()

    def is_language_supported(self, language_code: str) -> bool:
        """
        Check if a language code is supported.

        Args:
            language_code: ISO language code to check

        Returns:
            True if language is supported
        """
        return language_code in SUPPORTED_LANGUAGES

    def get_audio_duration(self, audio_file_path: str) -> float:
        """
        Extract audio duration from file using PyAV.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Duration in seconds

        Raises:
            FileNotFoundError: If audio file not found
            Exception: If audio file cannot be loaded
        """
        return get_audio_duration(audio_file_path)

    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about the service configuration.

        Returns:
            Dictionary with model and device information
        """
        return {
            "model_name": self.settings.whisper_model,
            "device": self.device,
            "compute_type": self.compute_type,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "supported_languages_count": len(SUPPORTED_LANGUAGES),
            "backend": "faster-whisper (CTranslate2)"
        }
