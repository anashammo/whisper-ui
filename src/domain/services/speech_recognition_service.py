"""Speech recognition service interface - Domain layer contract"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class SpeechRecognitionService(ABC):
    """
    Abstract service interface for speech recognition operations.

    This interface defines the contract for speech-to-text conversion
    that infrastructure layer must implement (e.g., using Whisper).
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text.

        Args:
            audio_file_path: Path to the audio file on disk
            language: Optional language code (e.g., 'en', 'es', 'fr')
                     If None, language will be auto-detected

        Returns:
            Dictionary containing:
                - text (str): Transcribed text
                - language (str): Detected or specified language code
                - duration (float): Audio duration in seconds

        Raises:
            TranscriptionError: If transcription fails
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO language codes (e.g., ['en', 'es', 'fr', ...])
        """
        pass

    @abstractmethod
    def is_language_supported(self, language_code: str) -> bool:
        """
        Check if a language code is supported.

        Args:
            language_code: ISO language code to check

        Returns:
            True if language is supported, False otherwise
        """
        pass
