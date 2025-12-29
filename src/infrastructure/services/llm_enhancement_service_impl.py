"""Implementation of LLM enhancement service

This module provides the concrete implementation of the LLMEnhancementService
domain interface using LangGraph and local LLM.
"""
from typing import Dict, Any, Optional

from ...domain.services.llm_enhancement_service import LLMEnhancementService
from ...presentation.agent.llm_client import LLMClient
from ...presentation.agent.enhancement_agent import EnhancementAgent


class LLMEnhancementServiceImpl(LLMEnhancementService):
    """
    Implementation of LLM enhancement using LangGraph agent.

    This service uses a local LLM (via Ollama, LM Studio, etc.) to enhance
    Whisper transcriptions by improving grammar, formatting, and removing filler words.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 60,
        temperature: float = 0.3
    ):
        """
        Initialize LLM enhancement service.

        Args:
            base_url: LLM API base URL (e.g., http://localhost:11434/v1)
            model: LLM model name (e.g., llama3, mistral)
            timeout: Request timeout in seconds
            temperature: LLM temperature for generation (0.0-1.0)
        """
        self.llm_client = LLMClient(
            base_url=base_url,
            model=model,
            timeout=timeout,
            temperature=temperature
        )
        self.agent = EnhancementAgent(self.llm_client)

    async def enhance_transcription(
        self,
        text: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance transcription using LLM agent.

        This method validates input, delegates to the LangGraph agent,
        and returns enhanced text with metadata.

        Args:
            text: Original transcription text from Whisper
            language: Optional language code

        Returns:
            Dictionary containing:
                - enhanced_text (str): The enhanced transcription
                - metadata (dict): Additional information about the enhancement

        Raises:
            ValueError: If input text is empty
            Exception: If LLM enhancement fails (connection, timeout, etc.)
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Transcription text cannot be empty")

        # Delegate to agent
        return await self.agent.enhance(text, language)
