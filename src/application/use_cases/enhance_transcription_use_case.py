"""Use case for enhancing transcription with LLM

This module implements the business logic for enhancing completed transcriptions
using a local Language Learning Model (LLM).
"""
import time
from typing import Optional

from ...domain.entities.transcription import Transcription
from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.services.llm_enhancement_service import LLMEnhancementService
from ..dto.transcription_dto import TranscriptionDTO


class EnhanceTranscriptionUseCase:
    """
    Use case for enhancing transcription text using LLM.

    This use case orchestrates the LLM enhancement workflow:
    1. Validates transcription can be enhanced
    2. Marks transcription as processing
    3. Calls LLM enhancement service
    4. Updates transcription with enhanced text or error
    5. Handles failures gracefully (allows retry)
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        llm_enhancement_service: LLMEnhancementService
    ):
        """
        Initialize use case with dependencies.

        Args:
            transcription_repository: Repository for transcriptions
            llm_enhancement_service: Service for LLM enhancement
        """
        self.transcription_repo = transcription_repository
        self.llm_service = llm_enhancement_service

    async def execute(self, transcription_id: str) -> TranscriptionDTO:
        """
        Execute LLM enhancement workflow.

        Args:
            transcription_id: ID of transcription to enhance

        Returns:
            TranscriptionDTO with enhanced text or error

        Raises:
            ValueError: If transcription not found or cannot be enhanced
        """
        # Step 1: Get transcription
        transcription = await self.transcription_repo.get_by_id(transcription_id)
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        # Step 2: Validate can be enhanced
        if not transcription.can_be_enhanced():
            raise ValueError(
                f"Transcription cannot be enhanced. "
                f"Reasons: "
                f"LLM enabled={transcription.enable_llm_enhancement}, "
                f"status={transcription.status.value}, "
                f"has_text={transcription.text is not None}, "
                f"enhancement_status={transcription.llm_enhancement_status}"
            )

        # Step 3: Mark as processing
        transcription.mark_llm_processing()
        await self.transcription_repo.update(transcription)

        # Step 4: Perform enhancement
        try:
            # Measure processing time
            start_time = time.time()

            # Call LLM enhancement service
            result = await self.llm_service.enhance_transcription(
                text=transcription.text,
                language=transcription.language
            )

            processing_time = time.time() - start_time

            # Step 5: Update with results
            transcription.complete_llm_enhancement(
                enhanced_text=result['enhanced_text'],
                processing_time=processing_time
            )

        except Exception as e:
            # Step 5 (error path): Mark as failed but keep original text
            transcription.fail_llm_enhancement(str(e))

        # Step 6: Final update
        final_transcription = await self.transcription_repo.update(transcription)

        # Step 7: Convert to DTO and return
        return TranscriptionDTO.from_entity(final_transcription)
