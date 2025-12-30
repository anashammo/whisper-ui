# LLM Enhancement Feature - Implementation Plan

**Branch**: `feature/llm-enhancement`
**Created**: 2025-12-30

## Overview

This document outlines the complete implementation plan for integrating a local LLM (via Ollama/LM Studio) to enhance Whisper transcription output using the LangGraph framework.

## Requirements Summary

### User Requirements
1. **LLM Integration**: Use local LLM compatible with OpenAI API standards (Ollama/LM Studio)
2. **Framework**: Use LangGraph for LLM integration
3. **Architecture**: Create `src/presentation/agent/` folder for LangGraph agent
4. **Enhancement Opt-In**: User chooses during upload/recording/re-transcription whether to enable LLM enhancement
5. **UI Display**:
   - Show "Enhanced with LLM: Yes/No" field in Transcription Information
   - If opted in: Show both original Whisper text AND enhanced LLM text in separate areas
   - If opted out: Show only original Whisper text
6. **Enhancement Trigger**: Manual - User clicks "Enhance with LLM" button on completed transcriptions
7. **Processing Time**: Track and display LLM enhancement processing time

### Technical Decisions (from clarifying questions)
- **Enhancement Type**: Grammar/punctuation correction + formatting/structure + filler word removal
- **Error Handling**: Keep original text, show error message, allow retry
- **Re-enhancement**: Once only (no multiple enhancements)
- **LLM Config**: Environment variable `LLM_BASE_URL` in `.env` file
- **LangGraph Usage**: Simple single LLM call with prompt (not complex multi-agent)
- **Timeout**: 60 seconds for LLM requests
- **UI Behavior**: Checkbox during upload controls whether enhancement section is visible

---

## Architecture Impact Analysis

### 1. Database Layer (SQLite)

**File**: `src/infrastructure/persistence/models/transcription_model.py`

**Changes**:
```python
# Add new columns to TranscriptionModel
enable_llm_enhancement = Column(Boolean, default=False, nullable=False)
enhanced_text = Column(Text, nullable=True)
llm_processing_time_seconds = Column(Float, nullable=True)
llm_enhancement_status = Column(String(20), nullable=True)  # 'pending', 'processing', 'completed', 'failed'
llm_error_message = Column(Text, nullable=True)
```

**Migration Required**: Yes - database migration script needed

---

### 2. Domain Layer

#### 2.1 Domain Entity: Transcription

**File**: `src/domain/entities/transcription.py`

**Changes**:
```python
@dataclass
class Transcription:
    # Existing fields...
    enable_llm_enhancement: bool = False
    enhanced_text: Optional[str] = None
    llm_processing_time_seconds: Optional[float] = None
    llm_enhancement_status: Optional[str] = None  # 'pending', 'processing', 'completed', 'failed'
    llm_error_message: Optional[str] = None

    # New business methods
    def can_be_enhanced(self) -> bool:
        """Check if transcription can be enhanced with LLM"""
        return (
            self.enable_llm_enhancement and
            self.status == TranscriptionStatus.COMPLETED and
            self.text is not None and
            self.llm_enhancement_status in [None, 'failed']  # Can retry if failed
        )

    def mark_llm_processing(self) -> None:
        """Mark LLM enhancement as processing"""
        if not self.can_be_enhanced():
            raise ValueError("Transcription cannot be enhanced")
        self.llm_enhancement_status = 'processing'

    def complete_llm_enhancement(self, enhanced_text: str, processing_time: float) -> None:
        """Complete LLM enhancement"""
        if self.llm_enhancement_status != 'processing':
            raise ValueError("LLM enhancement is not in processing state")
        self.enhanced_text = enhanced_text.strip()
        self.llm_processing_time_seconds = processing_time
        self.llm_enhancement_status = 'completed'
        self.llm_error_message = None

    def fail_llm_enhancement(self, error_message: str) -> None:
        """Mark LLM enhancement as failed"""
        if not error_message or not error_message.strip():
            raise ValueError("Error message cannot be empty")
        self.llm_enhancement_status = 'failed'
        self.llm_error_message = error_message.strip()
```

#### 2.2 Domain Service Interface: LLM Enhancement Service

**New File**: `src/domain/services/llm_enhancement_service.py`

```python
"""Interface for LLM enhancement service"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMEnhancementService(ABC):
    """Abstract interface for LLM enhancement service"""

    @abstractmethod
    async def enhance_transcription(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance transcription text using LLM.

        Args:
            text: Original transcription text from Whisper
            language: Optional language code

        Returns:
            Dict with 'enhanced_text' and 'metadata'

        Raises:
            ServiceException: If enhancement fails
        """
        pass
```

---

### 3. Application Layer

#### 3.1 New DTO Fields

**File**: `src/application/dto/transcription_dto.py`

**Changes**:
```python
@dataclass
class TranscriptionDTO:
    # Existing fields...
    enable_llm_enhancement: bool = False
    enhanced_text: Optional[str] = None
    llm_processing_time_seconds: Optional[float] = None
    llm_enhancement_status: Optional[str] = None
    llm_error_message: Optional[str] = None
```

**File**: `src/application/dto/audio_upload_dto.py`

**Changes**:
```python
@dataclass
class AudioUploadDTO:
    # Existing fields...
    enable_llm_enhancement: bool = False  # New field
```

#### 3.2 Modified Use Cases

**File**: `src/application/use_cases/transcribe_audio_use_case.py`

**Changes**:
- Accept `enable_llm_enhancement` parameter from DTO
- Set field on Transcription entity creation

**File**: `src/application/use_cases/retranscribe_audio_use_case.py`

**Changes**:
- Accept `enable_llm_enhancement` parameter
- Set field on new Transcription entity

#### 3.3 New Use Case: Enhance Transcription

**New File**: `src/application/use_cases/enhance_transcription_use_case.py`

```python
"""Use case for enhancing transcription with LLM"""
import time
from typing import Optional

from ...domain.entities.transcription import Transcription
from ...domain.repositories.transcription_repository import TranscriptionRepository
from ...domain.services.llm_enhancement_service import LLMEnhancementService
from ..dto.transcription_dto import TranscriptionDTO


class EnhanceTranscriptionUseCase:
    """
    Use case for enhancing transcription text using LLM.

    This use case:
    1. Validates transcription can be enhanced
    2. Marks transcription as processing
    3. Calls LLM enhancement service
    4. Updates transcription with enhanced text
    5. Handles errors and allows retry
    """

    def __init__(
        self,
        transcription_repository: TranscriptionRepository,
        llm_enhancement_service: LLMEnhancementService
    ):
        self.transcription_repo = transcription_repository
        self.llm_service = llm_enhancement_service

    async def execute(self, transcription_id: str) -> TranscriptionDTO:
        """
        Execute LLM enhancement workflow.

        Args:
            transcription_id: ID of transcription to enhance

        Returns:
            TranscriptionDTO with enhanced text

        Raises:
            ValueError: If transcription cannot be enhanced
            ServiceException: If enhancement fails
        """
        # Step 1: Get transcription
        transcription = await self.transcription_repo.get_by_id(transcription_id)
        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        # Step 2: Validate can be enhanced
        if not transcription.can_be_enhanced():
            raise ValueError(
                f"Transcription cannot be enhanced. Status: {transcription.status.value}, "
                f"LLM enabled: {transcription.enable_llm_enhancement}, "
                f"LLM status: {transcription.llm_enhancement_status}"
            )

        # Step 3: Mark as processing
        transcription.mark_llm_processing()
        await self.transcription_repo.update(transcription)

        # Step 4: Perform enhancement
        try:
            start_time = time.time()

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
            # Mark as failed but keep original text
            transcription.fail_llm_enhancement(str(e))

        # Step 6: Final update
        final_transcription = await self.transcription_repo.update(transcription)
        return TranscriptionDTO.from_entity(final_transcription)
```

---

### 4. Infrastructure Layer

#### 4.1 Configuration Settings

**File**: `src/infrastructure/config/settings.py`

**Changes**:
```python
class Settings(BaseSettings):
    # Existing fields...

    # LLM Configuration
    llm_base_url: str = Field(
        default="http://localhost:11434/v1",  # Default Ollama URL
        description="Base URL for LLM API (OpenAI-compatible)"
    )
    llm_model: str = Field(
        default="llama3",
        description="LLM model name"
    )
    llm_timeout_seconds: int = Field(
        default=60,
        description="Timeout for LLM requests in seconds"
    )
    llm_temperature: float = Field(
        default=0.3,
        description="LLM temperature (0.0-1.0, lower = more focused)"
    )
```

#### 4.2 Database Migration

**New File**: `scripts/migrations/migrate_add_llm_enhancement.py`

```python
"""Add LLM enhancement columns to transcriptions table"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import Boolean, Text, Float, String, Column
from src.infrastructure.persistence.database import engine, SessionLocal
from src.infrastructure.persistence.models.transcription_model import TranscriptionModel

def upgrade():
    """Add LLM enhancement columns"""
    with engine.begin() as conn:
        # Add columns
        conn.execute('ALTER TABLE transcriptions ADD COLUMN enable_llm_enhancement BOOLEAN DEFAULT FALSE NOT NULL')
        conn.execute('ALTER TABLE transcriptions ADD COLUMN enhanced_text TEXT')
        conn.execute('ALTER TABLE transcriptions ADD COLUMN llm_processing_time_seconds REAL')
        conn.execute('ALTER TABLE transcriptions ADD COLUMN llm_enhancement_status VARCHAR(20)')
        conn.execute('ALTER TABLE transcriptions ADD COLUMN llm_error_message TEXT')

    print("✅ Migration completed: Added LLM enhancement columns")

if __name__ == "__main__":
    upgrade()
```

---

### 5. Presentation Layer - Agent

#### 5.1 LangGraph Agent Structure

**New Folder**: `src/presentation/agent/`

**New File**: `src/presentation/agent/__init__.py`

**New File**: `src/presentation/agent/prompts.py`

```python
"""Prompts for LLM enhancement"""

ENHANCEMENT_SYSTEM_PROMPT = """You are an expert transcription editor. Your task is to enhance audio transcriptions by:

1. **Grammar & Punctuation**: Fix grammatical errors, add proper punctuation and capitalization
2. **Formatting**: Add paragraph breaks for readability, organize into sections if appropriate
3. **Filler Words**: Remove verbal fillers like "um", "uh", "like", "you know", etc.

IMPORTANT RULES:
- Preserve the original meaning and intent completely
- Do NOT add information that wasn't in the original transcription
- Do NOT change technical terms, names, or domain-specific language
- Keep the same tone and style (formal/informal) as the original
- If the transcription is already well-formatted, make minimal changes

Return ONLY the enhanced transcription text, without any preamble or explanation."""

ENHANCEMENT_USER_PROMPT_TEMPLATE = """Original Transcription:
{transcription}

Please enhance this transcription following the guidelines above."""
```

**New File**: `src/presentation/agent/llm_client.py`

```python
"""LLM client using OpenAI-compatible API"""
from typing import Dict, Any, Optional
import httpx
from openai import AsyncOpenAI


class LLMClient:
    """Client for communicating with local LLM via OpenAI-compatible API"""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 60,
        temperature: float = 0.3
    ):
        """
        Initialize LLM client.

        Args:
            base_url: Base URL for LLM API (e.g., http://localhost:11434/v1)
            model: Model name (e.g., llama3, mistral)
            timeout: Request timeout in seconds
            temperature: Sampling temperature (0.0-1.0)
        """
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key="not-needed",  # Local LLMs don't require API key
            timeout=httpx.Timeout(timeout, connect=10.0)
        )
        self.model = model
        self.temperature = temperature

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Get completion from LLM.

        Args:
            system_prompt: System message
            user_prompt: User message
            max_tokens: Maximum tokens in response

        Returns:
            LLM response text

        Raises:
            Exception: If API call fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"LLM API call failed: {str(e)}")
```

**New File**: `src/presentation/agent/enhancement_agent.py`

```python
"""LangGraph-based enhancement agent"""
from typing import Dict, Any, Optional
from langgraph.graph import Graph, StateGraph
from .llm_client import LLMClient
from .prompts import ENHANCEMENT_SYSTEM_PROMPT, ENHANCEMENT_USER_PROMPT_TEMPLATE


class EnhancementAgent:
    """
    LangGraph agent for enhancing transcriptions.

    Simple single-step agent that:
    1. Takes transcription text
    2. Formats prompt
    3. Calls LLM
    4. Returns enhanced text
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize enhancement agent.

        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow"""
        # Define state
        class EnhancementState(Dict):
            transcription: str
            language: Optional[str]
            enhanced_text: str
            error: Optional[str]

        # Create graph
        graph = StateGraph(EnhancementState)

        # Add nodes
        graph.add_node("enhance", self._enhance_node)

        # Set entry point
        graph.set_entry_point("enhance")

        # Compile
        return graph.compile()

    async def _enhance_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Enhancement node - calls LLM with prompt"""
        try:
            # Format prompt
            user_prompt = ENHANCEMENT_USER_PROMPT_TEMPLATE.format(
                transcription=state["transcription"]
            )

            # Call LLM
            enhanced_text = await self.llm_client.complete(
                system_prompt=ENHANCEMENT_SYSTEM_PROMPT,
                user_prompt=user_prompt
            )

            return {
                **state,
                "enhanced_text": enhanced_text,
                "error": None
            }

        except Exception as e:
            return {
                **state,
                "enhanced_text": "",
                "error": str(e)
            }

    async def enhance(
        self,
        transcription: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance transcription text.

        Args:
            transcription: Original transcription text
            language: Optional language code

        Returns:
            Dict with 'enhanced_text' and optional 'error'
        """
        initial_state = {
            "transcription": transcription,
            "language": language,
            "enhanced_text": "",
            "error": None
        }

        result = await self.graph.ainvoke(initial_state)

        if result.get("error"):
            raise Exception(result["error"])

        return {
            "enhanced_text": result["enhanced_text"],
            "metadata": {
                "language": language,
                "original_length": len(transcription),
                "enhanced_length": len(result["enhanced_text"])
            }
        }
```

#### 5.2 Infrastructure Service Implementation

**New File**: `src/infrastructure/services/llm_enhancement_service_impl.py`

```python
"""Implementation of LLM enhancement service"""
from typing import Dict, Any, Optional

from ...domain.services.llm_enhancement_service import LLMEnhancementService
from ...presentation.agent.llm_client import LLMClient
from ...presentation.agent.enhancement_agent import EnhancementAgent


class LLMEnhancementServiceImpl(LLMEnhancementService):
    """Implementation of LLM enhancement using LangGraph agent"""

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
            base_url: LLM API base URL
            model: LLM model name
            timeout: Request timeout
            temperature: LLM temperature
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

        Args:
            text: Original transcription text
            language: Optional language code

        Returns:
            Dict with enhanced_text and metadata

        Raises:
            Exception: If enhancement fails
        """
        if not text or not text.strip():
            raise ValueError("Transcription text cannot be empty")

        return await self.agent.enhance(text, language)
```

---

### 6. Presentation Layer - API

#### 6.1 API Schema Updates

**File**: `src/presentation/api/schemas/transcription_schema.py`

**Changes**:
```python
class TranscriptionResponse(BaseModel):
    # Existing fields...
    enable_llm_enhancement: bool = False
    enhanced_text: Optional[str] = None
    llm_processing_time_seconds: Optional[float] = None
    llm_enhancement_status: Optional[str] = None
    llm_error_message: Optional[str] = None
```

#### 6.2 Router Updates

**File**: `src/presentation/api/routers/transcription_router.py`

**Changes**:
```python
# Add enable_llm_enhancement parameter to upload endpoint
@router.post("/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None),
    model: Optional[str] = Query("base"),
    enable_llm_enhancement: bool = Query(False, description="Enable LLM enhancement"),
    use_case: TranscribeAudioUseCase = Depends(get_transcribe_audio_use_case)
):
    # ... existing code ...
    upload_dto = AudioUploadDTO(
        # ... existing fields ...
        enable_llm_enhancement=enable_llm_enhancement
    )
```

#### 6.3 New Router: LLM Enhancement

**New File**: `src/presentation/api/routers/llm_enhancement_router.py`

```python
"""API router for LLM enhancement endpoints"""
from fastapi import APIRouter, Depends, HTTPException

from src.presentation.api.dependencies import get_enhance_transcription_use_case
from src.presentation.api.schemas.transcription_schema import TranscriptionResponse
from src.application.use_cases.enhance_transcription_use_case import EnhanceTranscriptionUseCase


router = APIRouter()


@router.post(
    "/transcriptions/{transcription_id}/enhance",
    response_model=TranscriptionResponse,
    summary="Enhance transcription with LLM",
    description="Enhance completed transcription using local LLM for grammar, formatting, and filler word removal"
)
async def enhance_transcription(
    transcription_id: str,
    use_case: EnhanceTranscriptionUseCase = Depends(get_enhance_transcription_use_case)
):
    """
    Enhance a completed transcription with LLM.

    - **transcription_id**: ID of transcription to enhance

    Returns the transcription with enhanced text.
    """
    try:
        transcription_dto = await use_case.execute(transcription_id)
        return TranscriptionResponse.from_dto(transcription_dto)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )
```

#### 6.4 Dependency Injection

**File**: `src/presentation/api/dependencies.py`

**Changes**:
```python
from functools import lru_cache
from src.infrastructure.services.llm_enhancement_service_impl import LLMEnhancementServiceImpl
from src.application.use_cases.enhance_transcription_use_case import EnhanceTranscriptionUseCase

@lru_cache()
def get_llm_enhancement_service() -> LLMEnhancementServiceImpl:
    """Get singleton LLM enhancement service"""
    settings = get_settings()
    return LLMEnhancementServiceImpl(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        temperature=settings.llm_temperature
    )

def get_enhance_transcription_use_case(
    db: Session = Depends(get_db),
    llm_service: LLMEnhancementServiceImpl = Depends(get_llm_enhancement_service)
) -> EnhanceTranscriptionUseCase:
    """Get enhance transcription use case"""
    from src.infrastructure.persistence.repositories.sqlite_transcription_repository import SQLiteTranscriptionRepository
    transcription_repo = SQLiteTranscriptionRepository(db)
    return EnhanceTranscriptionUseCase(transcription_repo, llm_service)
```

#### 6.5 Main App Update

**File**: `src/presentation/api/main.py`

**Changes**:
```python
# Import new router
from src.presentation.api.routers import llm_enhancement_router

# Include router
app.include_router(
    llm_enhancement_router.router,
    prefix="/api/v1",
    tags=["LLM Enhancement"]
)
```

---

### 7. Presentation Layer - Frontend

#### 7.1 TypeScript Model Updates

**File**: `src/presentation/frontend/src/app/core/models/transcription.model.ts`

**Changes**:
```typescript
export interface Transcription {
  // Existing fields...
  enable_llm_enhancement: boolean;
  enhanced_text?: string;
  llm_processing_time_seconds?: number;
  llm_enhancement_status?: 'pending' | 'processing' | 'completed' | 'failed';
  llm_error_message?: string;
}
```

#### 7.2 API Service Updates

**File**: `src/presentation/frontend/src/app/core/services/api.service.ts`

**Changes**:
```typescript
// Add enable_llm_enhancement parameter to uploadAudio method
uploadAudio(
  file: File,
  language?: string,
  model?: string,
  enableLlmEnhancement: boolean = false
): Observable<Transcription> {
  const formData = new FormData();
  formData.append('file', file);
  if (language) formData.append('language', language);
  if (model) formData.append('model', model);
  formData.append('enable_llm_enhancement', enableLlmEnhancement.toString());

  return this.http.post<Transcription>(`${this.apiUrl}/transcriptions`, formData);
}

// New method: enhance transcription
enhanceTranscription(transcriptionId: string): Observable<Transcription> {
  return this.http.post<Transcription>(
    `${this.apiUrl}/transcriptions/${transcriptionId}/enhance`,
    {}
  );
}
```

#### 7.3 Transcription Service Updates

**File**: `src/presentation/frontend/src/app/core/services/transcription.service.ts`

**Changes**:
```typescript
// Update uploadAudio method signature
uploadAudio(
  file: File,
  language?: string,
  model?: string,
  enableLlmEnhancement: boolean = false
): Observable<Transcription> {
  return this.apiService.uploadAudio(file, language, model, enableLlmEnhancement);
}

// New method
enhanceTranscription(transcriptionId: string): Observable<Transcription> {
  return this.apiService.enhanceTranscription(transcriptionId).pipe(
    tap(transcription => this.transcriptionSubject.next(transcription))
  );
}
```

#### 7.4 Upload Component Updates

**File**: `src/presentation/frontend/src/app/features/upload/upload.component.ts`

**Changes**:
```typescript
export class UploadComponent implements OnInit, OnDestroy {
  // Add new property
  enableLlmEnhancement: boolean = false;

  // Update uploadFile method
  uploadFile(): void {
    if (!this.selectedFile) {
      return;
    }

    // ... existing code ...

    this.transcriptionService.uploadAudio(
      this.selectedFile,
      language,
      model,
      this.enableLlmEnhancement  // Pass new parameter
    ).subscribe({
      // ... existing handlers ...
    });
  }
}
```

**File**: `src/presentation/frontend/src/app/features/upload/upload.component.html`

**Changes**:
```html
<!-- Add checkbox after model selection -->
<div class="form-group">
  <label class="checkbox-label">
    <input
      type="checkbox"
      [(ngModel)]="enableLlmEnhancement"
      class="llm-checkbox">
    <span>Enhance with LLM (grammar, formatting, filler removal)</span>
  </label>
  <p class="help-text">
    If enabled, you can enhance the transcription with AI after Whisper completes.
  </p>
</div>
```

#### 7.5 Transcription Detail Component Updates

**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.ts`

**Changes**:
```typescript
export class TranscriptionComponent implements OnInit, OnDestroy {
  // Add new properties
  isEnhancing: boolean = false;
  enhancementError: string | null = null;

  // New method: enhance transcription
  enhanceWithLlm(): void {
    if (!this.activeTranscription?.id) {
      return;
    }

    this.isEnhancing = true;
    this.enhancementError = null;

    this.transcriptionService.enhanceTranscription(this.activeTranscription.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (enhanced) => {
          console.log('[TranscriptionComponent] Enhancement completed:', enhanced);
          this.isEnhancing = false;

          // Reload to get updated data
          this.loadAllTranscriptions(this.activeTranscription!.audio_file_id);

          this.popupService.success('Transcription enhanced successfully!')
            .pipe(takeUntil(this.destroy$))
            .subscribe();
        },
        error: (err) => {
          console.error('[TranscriptionComponent] Enhancement failed:', err);
          this.isEnhancing = false;

          let errorMessage = 'Failed to enhance transcription';
          if (err.error?.detail) {
            errorMessage = err.error.detail;
          } else if (err.message) {
            errorMessage = err.message;
          }

          this.enhancementError = errorMessage;
          this.popupService.error(errorMessage)
            .pipe(takeUntil(this.destroy$))
            .subscribe();
        }
      });
  }

  // Helper method
  canEnhance(): boolean {
    return (
      this.activeTranscription?.enable_llm_enhancement === true &&
      this.activeTranscription?.status === 'completed' &&
      this.activeTranscription?.llm_enhancement_status !== 'completed' &&
      this.activeTranscription?.llm_enhancement_status !== 'processing'
    );
  }

  // Helper method
  isEnhanced(): boolean {
    return this.activeTranscription?.llm_enhancement_status === 'completed';
  }
}
```

**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.html`

**Changes**:
```html
<!-- In Transcription Information section, add after processing time -->
<div class="info-item">
  <span class="info-label">Enhanced with LLM:</span>
  <span class="info-value">
    <span *ngIf="activeTranscription?.enable_llm_enhancement" class="status-badge status-enabled">
      Yes
      <span *ngIf="activeTranscription?.llm_enhancement_status === 'completed'"> ✓</span>
      <span *ngIf="activeTranscription?.llm_enhancement_status === 'processing'"> (Processing...)</span>
      <span *ngIf="activeTranscription?.llm_enhancement_status === 'failed'"> (Failed)</span>
    </span>
    <span *ngIf="!activeTranscription?.enable_llm_enhancement" class="status-badge status-disabled">
      No
    </span>
  </span>
</div>

<!-- Add LLM processing time if available -->
<div class="info-item" *ngIf="activeTranscription?.llm_processing_time_seconds">
  <span class="info-label">LLM Processing Time:</span>
  <span class="info-value">{{ formatProcessingTime(activeTranscription.llm_processing_time_seconds) }}</span>
</div>

<!-- Original Transcription Text section -->
<div class="transcription-section">
  <div class="section-header">
    <h3>
      <span *ngIf="!activeTranscription?.enable_llm_enhancement">Transcription</span>
      <span *ngIf="activeTranscription?.enable_llm_enhancement">Original Transcription (Whisper)</span>
    </h3>
  </div>
  <div class="transcription-text-container">
    <textarea
      class="transcription-text"
      [value]="activeTranscription?.text || ''"
      readonly>
    </textarea>
  </div>
</div>

<!-- Enhanced Transcription section - only show if user opted in -->
<div class="transcription-section" *ngIf="activeTranscription?.enable_llm_enhancement">
  <div class="section-header">
    <h3>Enhanced Transcription (LLM)</h3>

    <!-- Enhance button - show if not yet enhanced -->
    <button
      *ngIf="canEnhance()"
      class="btn btn-primary"
      (click)="enhanceWithLlm()"
      [disabled]="isEnhancing">
      <span *ngIf="!isEnhancing">✨ Enhance with LLM</span>
      <span *ngIf="isEnhancing">🔄 Enhancing...</span>
    </button>

    <!-- Retry button - show if failed -->
    <button
      *ngIf="activeTranscription?.llm_enhancement_status === 'failed'"
      class="btn btn-secondary"
      (click)="enhanceWithLlm()"
      [disabled]="isEnhancing">
      🔄 Retry Enhancement
    </button>
  </div>

  <!-- Enhanced text area -->
  <div class="transcription-text-container" *ngIf="isEnhanced()">
    <textarea
      class="transcription-text enhanced"
      [value]="activeTranscription?.enhanced_text || ''"
      readonly>
    </textarea>
  </div>

  <!-- Error message -->
  <div class="error-message" *ngIf="activeTranscription?.llm_error_message">
    <p>⚠️ Enhancement failed: {{ activeTranscription.llm_error_message }}</p>
  </div>

  <!-- Placeholder when not enhanced yet -->
  <div class="placeholder-text" *ngIf="!isEnhanced() && activeTranscription?.llm_enhancement_status !== 'processing'">
    <p>Click "Enhance with LLM" to improve grammar, formatting, and remove filler words.</p>
  </div>

  <!-- Processing indicator -->
  <div class="processing-indicator" *ngIf="activeTranscription?.llm_enhancement_status === 'processing'">
    <div class="spinner"></div>
    <p>Enhancing transcription with LLM...</p>
  </div>
</div>
```

#### 7.6 Transcription Detail CSS Updates

**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.css`

**Changes**:
```css
/* LLM Enhancement styles */
.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  font-weight: 500;
}

.status-enabled {
  background-color: #10b981;
  color: white;
}

.status-disabled {
  background-color: #6b7280;
  color: white;
}

.transcription-section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h3 {
  margin: 0;
}

.transcription-text.enhanced {
  border-left: 4px solid #10b981;
}

.placeholder-text {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 8px;
  border: 2px dashed #d1d5db;
}

.processing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1rem;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 1rem;
  background-color: #fee2e2;
  border-left: 4px solid #ef4444;
  border-radius: 4px;
  margin-top: 1rem;
}

.error-message p {
  margin: 0;
  color: #991b1b;
}
```

#### 7.7 Re-transcription Updates

**File**: `src/presentation/api/routers/audio_file_router.py`

**Changes**:
```python
# Add enable_llm_enhancement parameter to retranscribe endpoint
@router.post("/audio-files/{audio_file_id}/transcriptions")
async def retranscribe_audio(
    audio_file_id: str,
    model: str = Query(...),
    language: Optional[str] = Query(None),
    enable_llm_enhancement: bool = Query(False),
    use_case: RetranscribeAudioUseCase = Depends(get_retranscribe_audio_use_case)
):
    # Pass parameter to use case
    transcription_dto = await use_case.execute(audio_file_id, model, language, enable_llm_enhancement)
```

**File**: `src/presentation/frontend/src/app/features/transcription/transcription.component.html`

**Changes** (in re-transcription modal):
```html
<!-- Add checkbox in re-transcription dialog -->
<div class="form-group">
  <label class="checkbox-label">
    <input
      type="checkbox"
      [(ngModel)]="enableLlmEnhancementForRetranscribe"
      class="llm-checkbox">
    <span>Enhance with LLM</span>
  </label>
</div>
```

---

### 8. Dependencies Installation

**File**: `requirements.txt`

**Add**:
```
langgraph>=0.0.20
langchain>=0.1.0
openai>=1.10.0
httpx>=0.26.0
```

**Install**:
```bash
pip install langgraph langchain openai httpx
```

---

### 9. Environment Configuration

**File**: `.env.example` (and `.env`)

**Add**:
```
# LLM Configuration
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3
LLM_TIMEOUT_SECONDS=60
LLM_TEMPERATURE=0.3
```

---

### 10. Documentation Updates

#### 10.1 README.md

**Add sections**:
- LLM Enhancement feature description
- Configuration instructions for Ollama/LM Studio
- Model recommendations
- Usage instructions

#### 10.2 CLAUDE.md

**Add**:
- Architecture changes for LLM enhancement
- Agent folder structure
- New use cases and services
- Frontend component changes

---

## Implementation Steps

### Phase 1: Backend - Database & Domain (2-3 hours)
1. ✅ Create database migration script
2. ✅ Update domain entity (Transcription)
3. ✅ Create domain service interface
4. ✅ Update DTOs
5. ✅ Test migration and entity changes

### Phase 2: Backend - Agent & Infrastructure (3-4 hours)
6. ✅ Create `src/presentation/agent/` folder structure
7. ✅ Implement LLM client
8. ✅ Create prompts file
9. ✅ Implement LangGraph enhancement agent
10. ✅ Implement infrastructure service
11. ✅ Test agent in isolation

### Phase 3: Backend - Application & API (2-3 hours)
12. ✅ Create EnhanceTranscriptionUseCase
13. ✅ Update existing use cases (upload, retranscribe)
14. ✅ Update API schemas
15. ✅ Create LLM enhancement router
16. ✅ Update dependencies
17. ✅ Update main app
18. ✅ Test API endpoints

### Phase 4: Frontend - Models & Services (1-2 hours)
19. ✅ Update TypeScript models
20. ✅ Update API service
21. ✅ Update transcription service
22. ✅ Test service methods

### Phase 5: Frontend - Components (3-4 hours)
23. ✅ Update upload component (add checkbox)
24. ✅ Update transcription detail component (dual text areas, enhance button)
25. ✅ Update re-transcription dialog (add checkbox)
26. ✅ Add CSS styles
27. ✅ Test UI interactions

### Phase 6: Integration Testing (2-3 hours)
28. ✅ Set up local LLM (Ollama/LM Studio)
29. ✅ Run database migration
30. ✅ Install dependencies
31. ✅ Configure .env file
32. ✅ Test end-to-end workflow:
    - Upload with LLM enabled
    - Upload without LLM
    - Enhance transcription
    - Retry failed enhancement
    - Re-transcription with LLM enabled
33. ✅ Test error scenarios (timeout, connection failure)

### Phase 7: Documentation & Cleanup (1 hour)
34. ✅ Update README.md
35. ✅ Update CLAUDE.md
36. ✅ Create .env.example with LLM settings
37. ✅ Add comments to code
38. ✅ Final testing

### Phase 8: Git Commit & Documentation (30 min)
39. ✅ Review all changes
40. ✅ Create comprehensive commit message
41. ✅ Commit to feature branch

---

## Testing Checklist

### Backend Tests
- [ ] Database migration runs successfully
- [ ] Domain entity business rules work correctly
- [ ] LLM client connects to local LLM
- [ ] Enhancement agent produces good output
- [ ] Use case handles errors gracefully
- [ ] API endpoints return correct responses
- [ ] Timeout handling works (60s)

### Frontend Tests
- [ ] Upload checkbox appears and works
- [ ] Re-transcription checkbox appears and works
- [ ] Transcription detail shows correct fields
- [ ] Enhanced text area only shows when opted in
- [ ] Enhance button appears when appropriate
- [ ] Retry button appears on failure
- [ ] Processing indicators work
- [ ] Error messages display correctly

### Integration Tests
- [ ] End-to-end: Upload → Transcribe → Enhance
- [ ] LLM timeout handled gracefully
- [ ] LLM connection failure handled
- [ ] Multiple re-transcriptions with different LLM settings
- [ ] Browser refresh preserves state

---

## Estimated Total Time

**Total**: 14-19 hours

- Backend: 7-10 hours
- Frontend: 4-6 hours
- Integration Testing: 2-3 hours
- Documentation: 1 hour

---

## Potential Risks & Mitigations

### Risk 1: LangGraph Version Compatibility
**Mitigation**: Pin specific versions in requirements.txt, test immediately

### Risk 2: LLM Connection Issues
**Mitigation**: Implement robust error handling, clear error messages

### Risk 3: Database Migration Failures
**Mitigation**: Test migration on backup database first, implement rollback

### Risk 4: Frontend State Management Complexity
**Mitigation**: Use simple boolean flags, test state transitions thoroughly

### Risk 5: LLM Response Quality
**Mitigation**: Iterate on prompts, allow retry mechanism

---

## Success Criteria

1. ✅ User can opt-in for LLM enhancement during upload/re-transcription
2. ✅ Transcription detail shows "Enhanced with LLM: Yes/No"
3. ✅ When opted in, two text areas visible (original + enhanced)
4. ✅ When opted out, only one text area visible (original)
5. ✅ Enhance button triggers LLM processing
6. ✅ LLM processing time tracked and displayed
7. ✅ Errors handled gracefully with retry option
8. ✅ No breaking changes to existing functionality
9. ✅ Documentation updated
10. ✅ All tests passing

---

**End of Implementation Plan**
