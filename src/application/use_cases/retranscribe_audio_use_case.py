"""Use case for re-transcribing existing audio files with different models"""
from datetime import datetime
import uuid
import time
from typing import Optional

from ...domain.entities.transcription import Transcription, TranscriptionStatus
from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ...domain.services.speech_recognition_service import SpeechRecognitionService
from ...domain.services.llm_enhancement_service import LLMEnhancementService
from ..dto.transcription_dto import TranscriptionDTO


class RetranscribeAudioUseCase:
    """
    Use case for creating a new transcription from an existing audio file.

    This allows users to transcribe the same audio with different models
    without re-uploading the file.
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        audio_file_repository: AudioFileRepository,
        speech_recognition_service: SpeechRecognitionService,
        llm_enhancement_service: LLMEnhancementService
    ):
        self.transcription_repo = transcription_repository
        self.audio_file_repo = audio_file_repository
        self.speech_service = speech_recognition_service
        self.llm_service = llm_enhancement_service

    async def execute(
        self,
        audio_file_id: str,
        model: str,
        language: Optional[str] = None,
        enable_llm_enhancement: bool = False
    ) -> TranscriptionDTO:
        """
        Execute re-transcription workflow.

        Args:
            audio_file_id: ID of existing audio file
            model: Whisper model to use (tiny, base, small, medium, large)
            language: Optional language code

        Returns:
            TranscriptionDTO with new transcription

        Raises:
            ValueError: If audio file not found
        """
        # Step 1: Verify audio file exists
        audio_file = await self.audio_file_repo.get_by_id(audio_file_id)
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")

        # Step 2: Check if transcription with this model already exists
        existing_transcriptions = await self.transcription_repo.get_by_audio_file_id(audio_file_id)
        for trans in existing_transcriptions:
            if trans.model == model and trans.status == TranscriptionStatus.COMPLETED:
                # Return existing transcription instead of creating duplicate
                return TranscriptionDTO.from_entity(trans)

        # Step 3: Create new transcription entity
        transcription = Transcription(
            id=str(uuid.uuid4()),
            audio_file_id=audio_file.id,
            text=None,
            status=TranscriptionStatus.PENDING,
            language=language,
            duration_seconds=audio_file.duration_seconds or 0.0,
            created_at=datetime.utcnow(),
            completed_at=None,
            error_message=None,
            model=model,
            enable_llm_enhancement=enable_llm_enhancement
        )

        # Step 4: Persist transcription
        saved_transcription = await self.transcription_repo.create(transcription)

        # Step 5: Perform transcription
        try:
            saved_transcription.mark_as_processing()
            await self.transcription_repo.update(saved_transcription)

            # Measure Whisper processing time
            start_time = time.time()

            result = await self.speech_service.transcribe(
                audio_file.file_path,
                language,
                model
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            saved_transcription.complete(
                text=result['text'],
                language=result['language'],
                duration=result.get('duration') or audio_file.duration_seconds or 0.0,
                processing_time=processing_time
            )

            # Step 5.5: If LLM enhancement enabled, enhance the transcription
            if enable_llm_enhancement:
                try:
                    # Mark LLM enhancement as processing
                    saved_transcription.mark_llm_processing()
                    await self.transcription_repo.update(saved_transcription)

                    # Measure LLM processing time
                    llm_start_time = time.time()

                    # Call LLM enhancement service
                    llm_result = await self.llm_service.enhance_transcription(
                        text=saved_transcription.text,
                        language=saved_transcription.language
                    )

                    llm_processing_time = time.time() - llm_start_time

                    # Complete LLM enhancement
                    saved_transcription.complete_llm_enhancement(
                        enhanced_text=llm_result['enhanced_text'],
                        processing_time=llm_processing_time
                    )

                except Exception as llm_error:
                    # If LLM fails, mark it but don't fail the whole transcription
                    saved_transcription.fail_llm_enhancement(str(llm_error))

        except Exception as e:
            saved_transcription.fail(str(e))

        # Step 6: Final update
        final_transcription = await self.transcription_repo.update(saved_transcription)
        return TranscriptionDTO.from_entity(final_transcription)
