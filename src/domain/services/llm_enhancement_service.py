"""Domain service interface for LLM enhancement"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMEnhancementService(ABC):
    """
    Abstract interface for LLM enhancement service.

    This service is responsible for enhancing transcription text using
    a local Language Learning Model (LLM). The enhancement includes:
    - Grammar and punctuation correction
    - Formatting and structure improvement
    - Filler word removal

    Following Clean Architecture principles, this is a domain interface
    that will be implemented in the infrastructure layer.
    """

    @abstractmethod
    async def enhance_transcription(
        self,
        text: str,
        language: Optional[str] = None,
        enable_tashkeel: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance transcription text using LLM.

        Args:
            text: Original transcription text from Whisper
            language: Optional language code (e.g., 'en', 'es', 'fr', 'ar')
            enable_tashkeel: Whether to add Arabic diacritics (only applies if text is Arabic)

        Returns:
            Dictionary containing:
                - enhanced_text (str): The enhanced transcription
                - metadata (dict): Additional metadata about the enhancement

        Raises:
            ValueError: If text is empty or invalid
            Exception: If LLM service fails (connection, timeout, etc.)
        """
        pass
