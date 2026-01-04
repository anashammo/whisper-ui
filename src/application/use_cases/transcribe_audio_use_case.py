"""Use case for transcribing audio files"""
from datetime import datetime
import uuid
import time
from typing import Optional

from ...domain.entities.transcription import Transcription, TranscriptionStatus
from ...domain.entities.audio_file import AudioFile
from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.repositories.audio_file_repository import AudioFileRepository
from ...domain.services.speech_recognition_service import SpeechRecognitionService
from ...domain.services.llm_enhancement_service import LLMEnhancementService
from ..interfaces.file_storage_interface import FileStorageInterface
from ..dto.audio_upload_dto import AudioUploadDTO
from ..dto.transcription_dto import TranscriptionDTO


class TranscribeAudioUseCase:
    """
    Use case for orchestrating audio transcription workflow.

    This use case coordinates the entire transcription process:
    1. Validate audio file
    2. Store file to disk
    3. Create and persist audio file entity
    4. Create and persist transcription entity
    5. Perform transcription using Whisper
    6. Update transcription with results
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        audio_file_repository: AudioFileRepository,
        speech_recognition_service: SpeechRecognitionService,
        file_storage: FileStorageInterface,
        llm_enhancement_service: LLMEnhancementService,
        max_file_size_mb: int = 25,
        max_duration_seconds: int = 30
    ):
        """
        Initialize use case with dependencies.

        Args:
            transcription_repository: Repository for transcriptions
            audio_file_repository: Repository for audio files
            speech_recognition_service: Service for speech-to-text
            file_storage: Service for file storage
            llm_enhancement_service: Service for LLM enhancement
            max_file_size_mb: Maximum allowed file size in MB
            max_duration_seconds: Maximum allowed audio duration in seconds
        """
        self.transcription_repo = transcription_repository
        self.audio_file_repo = audio_file_repository
        self.speech_service = speech_recognition_service
        self.file_storage = file_storage
        self.llm_service = llm_enhancement_service
        self.max_file_size_mb = max_file_size_mb
        self.max_duration_seconds = max_duration_seconds

    async def execute(self, upload_dto: AudioUploadDTO) -> TranscriptionDTO:
        """
        Execute the transcription workflow.

        Args:
            upload_dto: Data transfer object containing upload information

        Returns:
            TranscriptionDTO with transcription results

        Raises:
            ValueError: If validation fails
            ServiceException: If transcription fails
        """
        # Step 1: Create audio file entity
        audio_file = AudioFile(
            id=str(uuid.uuid4()),
            original_filename=upload_dto.filename,
            file_path="",  # Will be set after storage
            file_size_bytes=upload_dto.file_size,
            mime_type=upload_dto.mime_type,
            duration_seconds=None,
            uploaded_at=datetime.utcnow()
        )

        # Step 2: Validate audio file using business rules (without duration yet)
        audio_file.validate_file_type()
        audio_file.validate_file_size(max_size_mb=self.max_file_size_mb)

        # Step 3: Store audio file to disk
        file_path = await self.file_storage.save(
            upload_dto.file_content,
            audio_file.id,
            audio_file.original_filename
        )
        audio_file.file_path = file_path

        # Step 3.5: Extract audio duration and validate
        try:
            # Verify file exists before extracting duration
            if not self.file_storage.exists(file_path):
                raise ValueError(f"File was not saved properly: {file_path}")

            # Log file path for debugging
            print(f"Extracting duration from: {file_path}")

            duration = self.speech_service.get_audio_duration(file_path)
            audio_file.duration_seconds = duration

            # Validate duration
            audio_file.validate_duration(max_duration_seconds=self.max_duration_seconds)
        except ValueError as e:
            # Clean up file if duration validation fails
            await self.file_storage.delete(file_path)
            raise e
        except Exception as e:
            # Clean up file if duration extraction fails
            await self.file_storage.delete(file_path)
            raise ValueError(f"Failed to extract audio duration from {file_path}: {str(e)}")

        # Step 4: Persist audio file entity
        saved_audio_file = await self.audio_file_repo.create(audio_file)

        # Step 5: Create transcription entity
        transcription = Transcription(
            id=str(uuid.uuid4()),
            audio_file_id=saved_audio_file.id,
            text=None,
            status=TranscriptionStatus.PENDING,
            language=upload_dto.language,
            duration_seconds=saved_audio_file.duration_seconds or 0.0,
            created_at=datetime.utcnow(),
            completed_at=None,
            error_message=None,
            model=upload_dto.model or "base",
            enable_llm_enhancement=upload_dto.enable_llm_enhancement,
            vad_filter_used=upload_dto.vad_filter
        )

        # Step 6: Persist transcription (PENDING status)
        saved_transcription = await self.transcription_repo.create(transcription)

        # Step 7: Process transcription
        try:
            # Mark as processing
            saved_transcription.mark_as_processing()
            await self.transcription_repo.update(saved_transcription)

            # Measure Whisper processing time
            start_time = time.time()

            # Perform speech recognition using faster-whisper
            result = await self.speech_service.transcribe(
                file_path,
                upload_dto.language,
                upload_dto.model or "base",
                upload_dto.vad_filter
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Update transcription with results
            # Note: Don't pass duration from Whisper as we already have the correct
            # duration from the audio file extraction
            saved_transcription.complete(
                text=result['text'],
                language=result['language'],
                processing_time=processing_time
            )

            # Step 7.5: If LLM enhancement enabled, enhance the transcription
            print(f"[DEBUG] Checking LLM enhancement: enable_llm_enhancement={upload_dto.enable_llm_enhancement}")
            if upload_dto.enable_llm_enhancement:
                print("[DEBUG] LLM enhancement is enabled, starting enhancement...")
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
                    # User still gets the original Whisper transcription
                    saved_transcription.fail_llm_enhancement(str(llm_error))

        except Exception as e:
            # Mark as failed if transcription fails
            saved_transcription.fail(str(e))

        # Step 8: Final update with results or error
        final_transcription = await self.transcription_repo.update(saved_transcription)

        # Step 9: Convert to DTO and return
        return TranscriptionDTO.from_entity(final_transcription)
