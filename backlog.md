# Product Backlog - Whisper Voice-to-Text Transcription System

> **Last Updated:** January 2026
> **Product Status:** Production-Ready
> **Version:** 1.0

---

## Executive Summary

A GPU-accelerated voice-to-text transcription system using **faster-whisper** (CTranslate2 backend) with FastAPI backend and Angular frontend. The system enables users to upload or record audio, transcribe with multiple AI models, and optionally enhance transcriptions using local LLM.

---

## Epic 1: Audio Input Management

### User Story 1.1: Audio File Upload
**As a** user
**I want to** upload audio files for transcription
**So that** I can convert my recordings to text

**Acceptance Criteria:**
- [x] Drag and drop file upload support
- [x] Click-to-browse file selection
- [x] Supported formats: MP3, WAV, M4A, FLAC, OGG, WEBM
- [x] Maximum file size: 25 MB
- [x] Maximum audio duration: 30 seconds
- [x] File type validation with clear error messages
- [x] Preview/playback of selected file before upload
- [x] Visual feedback during file upload

**API Endpoint:** `POST /api/v1/transcriptions`

---

### User Story 1.2: Browser Audio Recording
**As a** user
**I want to** record audio directly in the browser
**So that** I can transcribe spoken content without a separate recording device

**Acceptance Criteria:**
- [x] Microphone access request with permission handling
- [x] Recording duration counter (up to 30 seconds max)
- [x] Auto-stop at 30 seconds limit
- [x] Pause/resume not currently supported (stop only)
- [x] Playback preview of recorded audio
- [x] Re-record option (cancel and start over)
- [x] Clear error messages for permission denied/no microphone
- [x] Recording saved as WEBM format

**Browser Support:** Chrome, Firefox, Edge (Safari not tested)

---

### User Story 1.3: Audio File Deletion
**As a** user
**I want to** delete audio files I no longer need
**So that** I can manage my storage and remove outdated content

**Acceptance Criteria:**
- [x] Delete individual transcriptions
- [x] Delete audio file with all associated transcriptions (cascade delete)
- [x] Physical file removed from storage
- [x] Database records cleaned up
- [x] Confirmation before destructive actions

**API Endpoints:**
- `DELETE /api/v1/transcriptions/{transcription_id}` - Delete single transcription
- `DELETE /api/v1/audio-files/{audio_file_id}` - Delete audio file and all transcriptions

---

## Epic 2: Speech-to-Text Transcription

### User Story 2.1: Whisper Model Selection
**As a** user
**I want to** choose which Whisper model to use
**So that** I can balance between transcription speed and accuracy

**Acceptance Criteria:**
- [x] Model options: tiny, base, small, medium, large, turbo
- [x] Model descriptions with estimated sizes
- [x] Model status indicator (cached/needs download)
- [x] Real-time download progress with SSE streaming
- [x] Default model: base (recommended for general use)

**Available Models:**
| Model | Size | Description |
|-------|------|-------------|
| tiny | ~75MB | Fastest model with acceptable accuracy |
| base | ~150MB | Recommended for general use (best balance) |
| small | ~500MB | Balanced performance with better accuracy |
| medium | ~1.5GB | High accuracy for important transcriptions |
| large | ~3GB | Best accuracy for critical transcriptions |
| turbo | ~3GB | Optimized for speed and accuracy |

**API Endpoint:** `GET /api/v1/models/status/{model_name}`

---

### User Story 2.2: Language Selection
**As a** user
**I want to** specify the language of my audio
**So that** I can improve transcription accuracy for non-English content

**Acceptance Criteria:**
- [x] Auto-detect language option (default)
- [x] Manual language selection from dropdown
- [x] Supported languages: English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Chinese, Arabic, Hindi (and 90+ more via API)
- [x] Language persisted with transcription record

---

### User Story 2.3: Voice Activity Detection (VAD)
**As a** user
**I want to** enable Voice Activity Detection
**So that** I can filter out silence and improve transcription accuracy

**Acceptance Criteria:**
- [x] VAD toggle checkbox in upload form
- [x] VAD toggle in re-transcription dialog
- [x] Uses Silero VAD for silence filtering
- [x] VAD status persisted and displayed in transcription metadata
- [x] Configurable parameters (min_silence_duration_ms: 500, speech_pad_ms: 200)

---

### User Story 2.4: Re-transcription with Different Model
**As a** user
**I want to** transcribe the same audio with a different model
**So that** I can compare accuracy without re-uploading

**Acceptance Criteria:**
- [x] "Transcribe with Different Model" button in transcription details
- [x] Dropdown shows only models not yet used for this audio
- [x] Language selection in re-transcription dialog
- [x] LLM enhancement option in re-transcription
- [x] VAD option in re-transcription
- [x] Prevents duplicate transcriptions (same model returns existing)
- [x] Automatic model download if not cached

**API Endpoint:** `POST /api/v1/audio-files/{audio_file_id}/transcriptions`

---

### User Story 2.5: Model Download Progress Tracking
**As a** user
**I want to** see download progress when a model needs to be downloaded
**So that** I know how long to wait before transcription begins

**Acceptance Criteria:**
- [x] Check model cache status before transcription
- [x] Real-time progress bar with percentage
- [x] Server-Sent Events (SSE) for live updates
- [x] Estimated download size displayed
- [x] Automatic progress tracking during upload

**API Endpoint:** `GET /api/v1/models/download-progress/{model_name}` (SSE)

---

## Epic 3: LLM Enhancement

### User Story 3.1: LLM-Enhanced Transcription
**As a** user
**I want to** optionally enhance transcriptions with AI
**So that** I get cleaner text with proper grammar, formatting, and filler removal

**Acceptance Criteria:**
- [x] "Enhance with LLM" checkbox during upload/recording
- [x] LLM enhancement option in re-transcription dialog
- [x] Uses local LLM (Ollama/LM Studio with OpenAI-compatible API)
- [x] Preserves original Whisper transcription
- [x] Separate enhanced_text field for LLM output
- [x] Processing time tracking for LLM
- [x] Graceful failure handling (original text preserved if LLM fails)

**Enhancement Capabilities:**
- Grammar and punctuation correction
- Spelling error fixes
- Filler word removal (um, uh, etc.)
- Sentence structure improvement
- Formatting for readability

---

### User Story 3.2: Manual LLM Enhancement
**As a** user
**I want to** manually trigger LLM enhancement on completed transcriptions
**So that** I can enhance transcriptions that weren't initially processed

**Acceptance Criteria:**
- [x] "Enhance with LLM" button for eligible transcriptions
- [x] Button visible only when: completed status, LLM enabled, no existing enhancement
- [x] Processing state indicator during enhancement
- [x] Success/failure feedback
- [x] Retry capability for failed enhancements

**API Endpoint:** `POST /api/v1/transcriptions/{transcription_id}/enhance`

---

### User Story 3.3: Dual Text Display
**As a** user
**I want to** see both original and enhanced transcriptions side-by-side
**So that** I can compare and choose which version to use

**Acceptance Criteria:**
- [x] Side-by-side text areas when LLM enhancement is enabled
- [x] "Original Whisper Transcription" section
- [x] "Enhanced with LLM" section
- [x] Word count and character count for both
- [x] Read-only text areas (prevents accidental edits)
- [x] Copy functionality for both versions

---

## Epic 4: Transcription History & Management

### User Story 4.1: Transcription History View
**As a** user
**I want to** view all my transcriptions
**So that** I can access and manage my previous work

**Acceptance Criteria:**
- [x] Grouped by audio file (one audio = multiple transcription cards)
- [x] Audio file header with filename, duration, upload date
- [x] Transcription cards sorted by model size (tiny -> turbo)
- [x] Status badges with color coding (pending/processing/completed/failed)
- [x] LLM enhancement status badges (processing/completed/failed/pending)
- [x] Text preview (original + enhanced if available)
- [x] Expandable/collapsible audio file groups
- [x] Pagination support (limit/offset)

**API Endpoint:** `GET /api/v1/transcriptions`

---

### User Story 4.2: Transcription Details View
**As a** user
**I want to** view detailed information about a transcription
**So that** I can see full text, metadata, and processing information

**Acceptance Criteria:**
- [x] Full transcription text display
- [x] Enhanced text display (when available)
- [x] Transcription metadata: ID, model, language, processing time, timestamps
- [x] Audio file metadata: ID, filename, duration, upload date
- [x] Status information with timestamps
- [x] LLM enhancement status and processing time
- [x] Model tabs when multiple transcriptions exist for same audio
- [x] Tab switching without page reload (URL state management)

**API Endpoint:** `GET /api/v1/transcriptions/{transcription_id}`

---

### User Story 4.3: Audio Playback
**As a** user
**I want to** play back the original audio
**So that** I can verify transcription accuracy

**Acceptance Criteria:**
- [x] Play/Stop button in transcription details
- [x] Play/Stop button in history view (audio file header)
- [x] Audio streaming via FileResponse
- [x] Play one audio at a time (stops previous)
- [x] Available for all transcription statuses

**API Endpoint:** `GET /api/v1/transcriptions/{transcription_id}/audio`

---

### User Story 4.4: Audio Download
**As a** user
**I want to** download the original audio file
**So that** I can save it locally or use it elsewhere

**Acceptance Criteria:**
- [x] Download button in transcription details
- [x] Download button in history view (audio file header)
- [x] Force download with Content-Disposition header
- [x] WEBM files download with .wav extension for compatibility
- [x] Original filename preserved (with extension conversion)

**API Endpoint:** `GET /api/v1/transcriptions/{transcription_id}/audio?download=true`

---

### User Story 4.5: Copy to Clipboard
**As a** user
**I want to** copy transcription text to clipboard
**So that** I can paste it into other applications

**Acceptance Criteria:**
- [x] "Copy Original" button for original Whisper text
- [x] "Copy Enhanced" button for LLM-enhanced text (when available)
- [x] Visual feedback on successful copy

---

## Epic 5: System Status & Health

### User Story 5.1: Health Monitoring
**As an** administrator
**I want to** monitor system health
**So that** I can ensure the service is running properly

**Acceptance Criteria:**
- [x] Health check endpoint
- [x] Backend service status
- [x] GPU availability detection
- [x] faster-whisper service status

**API Endpoint:** `GET /api/v1/health`

---

### User Story 5.2: System Information
**As a** user
**I want to** see system capabilities
**So that** I know what features are available

**Acceptance Criteria:**
- [x] GPU detection and name display
- [x] CUDA availability status
- [x] Available Whisper models list
- [x] Backend version information
- [x] faster-whisper backend indicator

**API Endpoint:** `GET /api/v1/info`

---

## Epic 6: Docker Deployment

### User Story 6.1: Containerized Deployment
**As a** system administrator
**I want to** deploy the application using Docker
**So that** I can run it consistently across environments

**Acceptance Criteria:**
- [x] Multi-service docker-compose setup
- [x] Backend container with GPU support (NVIDIA Container Toolkit)
- [x] Frontend container with ng serve
- [x] PostgreSQL database container
- [x] Volume persistence for data, uploads, model cache
- [x] Health checks for all services
- [x] Hot-reload for development

**Docker Services:**
- `postgres` - PostgreSQL 15 database (port 5432 internal)
- `backend` - FastAPI + CUDA 12.8 (port 8001)
- `frontend` - Angular ng serve (port 4200)

---

### User Story 6.2: Model Preloading
**As a** system administrator
**I want to** preload Whisper models at startup
**So that** users don't wait for downloads on first use

**Acceptance Criteria:**
- [x] PRELOAD_MODELS environment variable
- [x] Smart caching (skip already downloaded models)
- [x] Force download option
- [x] Support for all model sizes
- [x] Volume-based persistence (survives container restarts)

**Environment Variable:** `PRELOAD_MODELS=tiny,base,small`

---

## Non-Functional Requirements (Implemented)

### Performance
- [x] GPU acceleration with CUDA 12.8+ (RTX 5090 compatible)
- [x] faster-whisper with CTranslate2 (up to 4x faster than OpenAI Whisper)
- [x] INT8/FP16 quantization for efficient inference
- [x] Model caching in memory (singleton pattern)
- [x] Asynchronous transcription processing

### Scalability
- [x] PostgreSQL database for Docker deployments
- [x] SQLite for local development
- [x] Connection pooling for database
- [x] Stateless API design

### Security
- [x] File type validation
- [x] File size limits
- [x] Audio duration limits
- [x] Input sanitization
- [x] No secret hardcoding (environment variables)

### Reliability
- [x] Graceful error handling
- [x] Partial success (LLM failure doesn't fail transcription)
- [x] Retry capability for failed enhancements
- [x] Cascade delete for data consistency
- [x] Transaction management with SQLAlchemy

### Usability
- [x] Responsive UI design
- [x] Dark mode interface
- [x] Clear error messages
- [x] Progress indicators
- [x] Loading states

---

## API Reference Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/transcriptions` | POST | Upload and transcribe audio |
| `/api/v1/transcriptions` | GET | Get transcription history |
| `/api/v1/transcriptions/{id}` | GET | Get specific transcription |
| `/api/v1/transcriptions/{id}` | DELETE | Delete transcription |
| `/api/v1/transcriptions/{id}/audio` | GET | Stream/download audio |
| `/api/v1/transcriptions/{id}/enhance` | POST | Enhance with LLM |
| `/api/v1/audio-files/{id}/transcriptions` | POST | Re-transcribe with different model |
| `/api/v1/audio-files/{id}/transcriptions` | GET | Get all transcriptions for audio file |
| `/api/v1/audio-files/{id}` | DELETE | Delete audio file and all transcriptions |
| `/api/v1/models/status/{model}` | GET | Check model cache status |
| `/api/v1/models/download-progress/{model}` | GET (SSE) | Stream download progress |
| `/api/v1/models/available` | GET | List available models |
| `/api/v1/health` | GET | Health check |
| `/api/v1/info` | GET | System information |

---

## Technology Stack

### Backend
- Python 3.9+
- FastAPI (REST API)
- faster-whisper (CTranslate2 backend)
- SQLAlchemy (ORM)
- PostgreSQL/SQLite (Database)
- PyTorch with CUDA 12.8
- LangGraph (LLM orchestration)
- Local LLM (Ollama/LM Studio)

### Frontend
- Angular 17
- TypeScript
- RxJS
- CSS (custom dark theme)

### Infrastructure
- Docker & Docker Compose
- NVIDIA Container Toolkit
- HuggingFace Hub (model distribution)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 2026 | Initial backlog documentation of implemented features |
