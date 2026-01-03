# CLAUDE.md — AI Governance & Operating Rules

## Purpose
This document defines **mandatory rules** for using Claude CLI as a **senior, autonomous code assistant** in this repository.

These rules are **binding**.  
Violation of any rule means the task is **NOT DONE**.

---

## Role & Expectations
Claude operates as a **senior production-grade software engineer**.

Primary goals:
- Correctness over speed
- Zero regressions
- Full traceability
- Persistent progress across failures

---

## Core Principles
- **Understand before acting**
- **No assumptions**
- **Plan before code**
- **Iterative testing & documentation**
- **Security first**
- **Persistence over context loss**

---

## Mandatory Workflow

### 1. Codebase Understanding (Hard Requirement)
Before writing any code:
- Scan the **entire codebase**
- Understand:
  - Architecture
  - Coding style and patterns
  - Dependencies and versions
- Review **all documentation**:
  - `README.md`
  - This `CLAUDE.md`
  - All relevant `*.md` files

---

### 2. Reasoning Rules (Chain of Thought)
- Always use **internal chain-of-thought reasoning** for:
  - Analysis
  - Planning
  - Risk assessment
- **Never expose reasoning steps**
- Output only:
  - Final conclusions
  - Structured plans
  - Clear decisions and summaries

_Internal reasoning is mandatory. Disclosure is forbidden._

---

### 3. Requirements & Impact Analysis
- Analyze requested features with **zero assumptions**
- Consider impact on:
  - Database
  - Backend
  - Frontend
  - Scripts
  - Docker & infrastructure
  - Environment variables
- If anything is unclear:
  - STOP
  - Ask questions
  - Prefer multiple selectable options

---

### 4. Planning (Hard Gate)
Before implementation:
- Produce a **detailed, step-by-step plan**
- Include:
  - Files to change
  - Migrations or scripts
  - Testing strategy
  - Risks and rollback steps
- Wait for **explicit approval**
- Save plan + TODOs in:
  ```
  plans/*.md
  ```
- Continuously update TODOs during implementation

_No approved plan = no coding._

---

### 5. Git & Branching
- Always create a branch:
  ```
  features/<short-description>
  ```
- Never commit directly to protected branches
- Commits must be small and incremental

---

### 6. Implementation Rules
- Implement incrementally
- Never break existing functionality
- Maintain backward compatibility
- Test after every meaningful change

---

### 7. Testing Requirements
- Unit tests (if applicable)
- Integration tests
- Manual testing
- Re-test after fixes

---

### 8. Iterative Documentation & Configuration (STRICT)
Documentation is **continuous**, not a final step.

After:
- Each implementation phase
- Each manual testing cycle
- Final completion

You **must review and update**:
- `README.md`
- `CLAUDE.md`
- All relevant `*.md` files
- `scripts/`
- `.env`, `.env.example`, env templates

Documentation drift is a **bug**.

---

### 9. Scripts & Automation
- Use `scripts/` for:
  - Server management
  - Docker management
  - Maintenance
  - Reusable tooling
- Create or enhance scripts when reuse appears
- Document all scripts

---

### 10. Docker & GPU / ML Constraints
- Maintain:
  - Dockerfiles
  - docker-compose files
  - Environment configs
- For NVIDIA / CUDA / PyTorch / RTX:
  - Perform **fresh internet research**
  - Verify official repositories
  - Follow compatibility matrices
  - Do not rely on outdated knowledge

---

## Security & Secrets Handling (MANDATORY)

### Rules
- **Never hardcode secrets**
- Secrets include:
  - API keys
  - Tokens
  - Passwords
  - Private keys
  - Certificates

### Environment Variables
- `.env` files with real secrets:
  - Must NOT be committed
  - Must be in `.gitignore`
- Always maintain:
  - `.env.example` with placeholders
- Every new env variable requires:
  - `.env.example` update
  - Documentation update

### Logs & Docker
- Never log secrets
- Never bake secrets into Docker images
- Use runtime env injection only

**Any leaked secret = critical failure.**

---

## Commit & PR Conventions

### Commit Messages (Conventional Commits)
Format:
```
type(scope): short description
```

Allowed types:
- `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`

Examples:
```
feat(api): add audit logging
fix(db): prevent duplicate records
docs(readme): update setup steps
```

### Pull Requests Must Include
- Plan reference (`plans/*.md`)
- Confirmation:
  - Tests passed
  - Docs updated
  - Env templates updated
  - Docker verified
  - No secrets committed
- Notes on:
  - Breaking changes
  - Migrations

---

## Operating Modes

### Autonomous Mode (Default)
- Claude proceeds independently
- Asks questions only for critical ambiguity

### Assisted Mode
- Claude pauses at major decisions
- Presents options
- Waits for user selection

---

## Definition of Done (ALL Required)
- Feature implemented as planned
- No regressions
- Tests pass
- Docs, scripts, envs updated
- Docker verified
- Plan TODOs complete
- Feature branch clean

If any item fails → **NOT DONE**

---

## Failure Recovery Protocol

If context is lost or work is interrupted:
1. Open latest `plans/*.md`
2. Review plan and TODOs
3. Resume from last unchecked item
4. Re-verify tests and docs
5. Continue updating TODOs

If no plan exists → recreate it before coding.

---

## Sub-Agent Usage Rules

Use sub-agents for context-heavy tasks.

### Allowed Sub-Agents
- Codebase Scanner
- Documentation Seen
- Dependency / GPU Research
- Script & Automation
- Test & Validation

### Rules
- Sub-agents summarize only
- No verbose logs
- Main agent integrates results

---

## Enforcement
- Missing plan → STOP
- Missing documentation → NOT DONE
- Missing env updates → NOT DONE
- Security violation → FAIL HARD

---

**This file is authoritative.  
Claude must refuse to proceed if these rules are violated.**

## Project Overview

A GPU-accelerated voice-to-text transcription system using **faster-whisper** (CTranslate2 backend) with FastAPI backend and Angular frontend. Supports multiple model transcriptions per audio file (tiny/base/small/medium/large/turbo) with real-time progress tracking, grouped history view, and LLM-based transcription enhancement.

**Key Features**:
- Users can upload audio once and transcribe with multiple Whisper models to compare accuracy/speed tradeoffs
- **Up to 4x faster inference** compared to OpenAI Whisper using CTranslate2 optimization
- **Voice Activity Detection (VAD)** using Silero VAD to filter silence and improve accuracy
- Transcriptions can be enhanced with local LLM (Ollama/LM Studio) for grammar correction, formatting, and filler removal
- Transcriptions are displayed ordered by model size (smallest to largest)
- Dual text display shows original Whisper and LLM-enhanced versions side-by-side
- Audio controls consolidated at audio file level in History view
- Visual indicators for LLM enhancement status across all views
- Browser download filenames auto-convert .webm to .wav for compatibility
- Read-only transcription display prevents accidental edits

## Architecture

### Clean Architecture Layers (Strict Dependency Rules)

```
Domain Layer (Inner)
  ↓ depends on nothing
Application Layer
  ↓ depends on Domain only
Infrastructure Layer
  ↓ depends on Domain interfaces
Presentation Layer (Outer)
  ↓ depends on all layers
```

**Critical Rule**: Domain entities NEVER import from infrastructure or presentation. All external dependencies are injected via interfaces.

### Backend Structure

```
src/
├── domain/                      # Pure business logic, no external dependencies
│   ├── entities/               # Transcription, AudioFile (dataclasses with business rules)
│   ├── repositories/           # Abstract repository interfaces
│   ├── services/              # Abstract service interfaces (SpeechRecognitionService, LLMEnhancementService)
│   └── exceptions/            # Domain-specific exceptions
│
├── application/                # Use cases orchestrate domain logic
│   ├── use_cases/             # TranscribeAudioUseCase, RetranscribeAudioUseCase, EnhanceTranscriptionUseCase
│   └── dto/                   # Data transfer objects for cross-layer communication
│
├── infrastructure/             # External implementations
│   ├── persistence/
│   │   ├── models/            # SQLAlchemy ORM models (NOT domain entities)
│   │   └── repositories/      # SQLiteTranscriptionRepository implements domain interfaces
│   ├── services/              # FasterWhisperService, LLMEnhancementServiceImpl
│   └── storage/               # LocalFileStorage for audio files
│
└── presentation/
    ├── agent/                 # LangGraph agent for LLM enhancement
    │   ├── prompts.py        # System and user prompts for LLM
    │   ├── llm_client.py     # OpenAI-compatible LLM client
    │   └── enhancement_agent.py  # LangGraph workflow
    ├── api/                   # FastAPI routers, schemas, dependencies
    │   ├── routers/          # transcription_router, audio_file_router, llm_enhancement_router
    │   ├── schemas/          # Pydantic models for request/response
    │   └── dependencies.py   # Dependency injection with @lru_cache for singletons
    └── frontend/             # Angular SPA
```

### Data Flow Example (Re-transcription)

1. **Frontend** → POST `/api/v1/audio-files/{id}/transcriptions?model=small`
2. **Router** (`audio_file_router.py`) → validates input, calls use case via dependency injection
3. **Use Case** (`RetranscribeAudioUseCase`) → orchestrates:
   - Fetch AudioFile entity from repository
   - Check for duplicate transcriptions (same model)
   - Create new Transcription entity (PENDING status)
   - Mark as PROCESSING, call FasterWhisperService
   - Complete or fail based on result
4. **Repository** → persists to database (PostgreSQL in Docker, SQLite locally) via SQLAlchemy ORM
5. **Frontend** → polls GET `/api/v1/transcriptions/{id}` for status updates

### Database Schema (PostgreSQL for Docker, SQLite for Local)

**1:Many relationship**: One AudioFile → Many Transcriptions

```
audio_files
  - id (PK)
  - original_filename
  - file_path
  - duration_seconds  # Extracted once on upload
  - uploaded_at

transcriptions
  - id (PK)
  - audio_file_id (FK → audio_files.id, CASCADE DELETE)
  - model (tiny/base/small/medium/large/turbo)
  - text
  - status (pending/processing/completed/failed)
  - duration_seconds  # Copied from audio_file
  - created_at
  - completed_at

  # LLM Enhancement fields (added December 2025)
  - enable_llm_enhancement (boolean, default: false)
  - enhanced_text (text, nullable)
  - llm_processing_time_seconds (float, nullable)
  - llm_enhancement_status (varchar, nullable: processing/completed/failed)
  - llm_error_message (text, nullable)

  # Voice Activity Detection (VAD) field (added January 2026)
  - vad_filter_used (boolean, default: false)
```

**UI Features**:
- Transcriptions in History view are sorted by model size (tiny → turbo)
- Transcription Detail view tabs are ordered by model size
- Re-transcription dropdown only shows models not yet used for that audio file
- Audio file metadata (ID, original filename, upload date) displayed in detail view
- Dual text areas show original Whisper and LLM-enhanced transcriptions side-by-side (when LLM enabled)
- Read-only transcription textareas prevent accidental editing
- "Enhance with LLM" button for completed transcriptions that opted in
- LLM enhancement checkbox in upload/recording/re-transcription forms
- VAD (Voice Activity Detection) checkbox in upload/recording/re-transcription forms
- LLM enhancement status badges in both History and Details views (color-coded: green=completed, blue=processing, red=failed, orange=pending)
- Enhanced text preview in History view cards (when available)
- **Audio playback and download**:
  - History view: Play (▶️) and Download (⬇️) buttons in audio file header (consolidated, not per-transcription)
  - Details view: Play Audio and Download Audio buttons in Transcription Result section
  - Download button triggers browser download with filename conversion (.webm files download as .wav for universal compatibility)
  - Available for all transcription statuses (pending, processing, completed, failed)
- **Copy functionality** in Details view:
  - "Copy Original" - copies original Whisper text to clipboard
  - "Copy Enhanced" - copies LLM-enhanced text (only visible when enhancement successful)
- Footer includes link to WER (Word Error Rate) comparison tool

**Important**: When audio file is deleted, all associated transcriptions are automatically deleted (CASCADE).

### Data Flow Example (LLM Enhancement)

1. **Frontend** → POST `/api/v1/transcriptions/{id}/enhance`
2. **Router** (`llm_enhancement_router.py`) → validates input, calls use case via dependency injection
3. **Use Case** (`EnhanceTranscriptionUseCase`) → orchestrates:
   - Fetch Transcription entity from repository
   - Validate business rules via `transcription.can_be_enhanced()`
   - Mark as processing via `transcription.mark_llm_processing()`
   - Call LLM enhancement service (LangGraph agent)
   - Complete or fail based on result via `transcription.complete_llm_enhancement()` or `transcription.fail_llm_enhancement()`
4. **LLM Service** (Infrastructure) → calls presentation agent
5. **Agent** (`enhancement_agent.py`) → LangGraph workflow:
   - Uses LLM client to call local LLM (Ollama/LM Studio)
   - Applies enhancement prompts (grammar, formatting, filler removal)
   - Returns enhanced text
6. **Repository** → persists updated transcription to database (PostgreSQL in Docker, SQLite locally)
7. **Frontend** → displays dual text areas with original and enhanced text

## Development Commands

### Environment Setup

```bash
# Activate virtual environment (REQUIRED for all commands)
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Install UV package manager (optional but recommended - 10-100x faster)
python scripts/setup/install_uv.py

# Install dependencies (choose one method)
# Option A: With UV (recommended)
uv pip install -r src/presentation/api/requirements.txt
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Option B: With pip
pip install -r src/presentation/api/requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Frontend setup
cd src/presentation/frontend
npm install
cd ../../..
```

### Running Servers

**CRITICAL**: Backend runs on port **8001**, frontend expects this in `environment.ts`.

```bash
# Option 1: Using convenience scripts (recommended)
python scripts/server/run_backend.py   # Terminal 1 - port 8001
python scripts/server/run_frontend.py  # Terminal 2 - port 4200

# Option 2: Manual start
python -m uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8001 --reload
cd src/presentation/frontend && ng serve

# Stop servers
python scripts/server/stop_all.py
```

**Access Points**:
- Frontend: http://localhost:4200
- Backend API: http://localhost:8001
- API Docs (Swagger): http://localhost:8001/docs

### Database Management

```bash
# Initialize database (creates whisper_transcriptions.db)
python scripts/setup/init_db.py

# Clean up orphaned transcriptions (manual script)
python scripts/maintenance/cleanup_orphaned_transcriptions.py
```

### Model Management

```bash
# Download Whisper models (cached in ~/.cache/huggingface/)
# Models are automatically downloaded on first use by faster-whisper
# Docker preloads models via PRELOAD_MODELS environment variable
```

### Testing & Code Quality

```bash
# Run tests
pytest

# Code formatting
black src/

# Type checking
mypy src/
```

### Docker Deployment

**IMPORTANT**: Docker deployment uses PostgreSQL for ALL environments (development and production), not SQLite.

```bash
# Quick start
cp .env.docker .env
python scripts/docker/run.py --build

# Management scripts (scripts/docker/)
python scripts/docker/build.py              # Build images
python scripts/docker/run.py                # Start services
python scripts/docker/stop.py               # Stop services
python scripts/docker/logs.py --follow      # View logs
python scripts/docker/shell.py backend      # Open shell in backend
python scripts/docker/clean.py --all        # Clean all resources
python scripts/docker/rebuild.py            # Rebuild and restart
```

**Docker Architecture**:
- **postgres**: PostgreSQL 15 (port 5432 internal, volume: postgres-data)
- **backend**: FastAPI + CUDA 12.8 (port 8001, volumes: whisper-uploads, huggingface-cache, source code for hot-reload)
- **frontend**: Angular ng serve (port 4200, volume: source code for hot-reload)

**Hot-Reload**: Source code mounted as read-only volumes, changes auto-detected without rebuild

**Model Preloading**: Set `PRELOAD_MODELS=tiny,base,small` in .env to download on startup

**GPU Support**: Backend requires NVIDIA Container Toolkit, uses `nvidia` runtime with GPU capabilities
- **IMPORTANT**: RTX 5090 (Blackwell architecture, sm_120) requires CUDA 12.8+ and PyTorch 2.7.0+
- CUDA 11.8 will cause "CUDA kernel errors" with RTX 5090
- The Dockerfile uses CUDA 12.8 base images for compatibility with latest GPUs

**Volume Persistence**: All data (database, uploads, models) in named volumes, never in container images

## Key Implementation Patterns

### 1. Dependency Injection (Backend)

**Pattern**: FastAPI `Depends()` with factory functions in `dependencies.py`

**Singletons** (loaded once, reused across requests):
```python
@lru_cache()
def get_whisper_service() -> FasterWhisperService:
    # Model loaded once, stays in GPU memory
    settings = get_settings()
    return FasterWhisperService(settings)
```

**Per-request** (new instance per request):
```python
def get_transcribe_audio_use_case(
    db: Session = Depends(get_db),
    whisper_service: FasterWhisperService = Depends(get_whisper_service),
    file_storage: LocalFileStorage = Depends(get_file_storage),
    settings: Settings = Depends(get_settings)
) -> TranscribeAudioUseCase:
    # Fresh repositories for each request
    transcription_repo = SQLiteTranscriptionRepository(db)
    audio_file_repo = SQLiteAudioFileRepository(db)
    return TranscribeAudioUseCase(...)
```

### 2. Entity State Transitions (Domain Logic)

**Transcription status flow**: PENDING → PROCESSING → COMPLETED/FAILED

```python
# Domain entity enforces business rules
transcription = Transcription(status=TranscriptionStatus.PENDING, ...)

# Only PENDING can become PROCESSING
transcription.mark_as_processing()  # Raises ValueError if not PENDING

# Only PROCESSING can complete
transcription.complete(text="...", language="en", duration=13.07)

# Or fail
transcription.fail("GPU out of memory")
```

### 3. Frontend State Management (RxJS)

**Pattern**: BehaviorSubjects for reactive state, Services as state containers

```typescript
// transcription.service.ts
private transcriptionSubject = new BehaviorSubject<Transcription | null>(null);
currentTranscription$ = this.transcriptionSubject.asObservable();

loadTranscription(id: string) {
  this.apiService.getTranscription(id).subscribe(
    trans => this.transcriptionSubject.next(trans)
  );
}

// component.ts
this.transcriptionService.getCurrentTranscription()
  .pipe(takeUntil(this.destroy$))
  .subscribe(trans => this.transcription = trans);
```

### 4. URL State Without Reload

**Problem**: `router.navigate()` triggers component re-initialization, causing flicker.

**Solution**: Use `window.history.replaceState()` for tab switching:

```typescript
switchTranscription(transcription: Transcription): void {
  this.activeTranscription = transcription;

  // Update URL without triggering navigation/reload
  const url = this.router.createUrlTree(['/transcription', transcription.id]).toString();
  window.history.replaceState({}, '', url);
}
```

## Common Issues & Solutions

### Backend Issues

**Issue**: `duration_seconds` parameter error when calling `Transcription.complete()`
- **Cause**: Method signature uses `duration`, not `duration_seconds`
- **Fix**: Use `duration=value` when calling `.complete()`

**Issue**: Python cache prevents code updates from loading
- **Cause**: `.pyc` files in `__pycache__` directories
- **Fix**: Clear cache, restart backend:
  ```bash
  powershell -Command "Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force"
  taskkill //F //IM python.exe
  python -m uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8001
  ```

**Issue**: Orphaned transcriptions (audio file deleted but transcriptions remain)
- **Cause**: Database cascade delete not working or manual file deletion
- **Fix**: Clean up manually via SQLAlchemy queries

### Frontend Issues

**Issue**: Template binding error with `.find()` or complex expressions
- **Cause**: Angular doesn't allow assignments or complex logic in templates
- **Fix**: Create helper methods in component:
  ```typescript
  // Bad: {{ allTranscriptions.find(t => t.model === model) ? 'exists' : 'new' }}
  // Good: {{ isModelAlreadyTranscribed(model) ? 'exists' : 'new' }}

  isModelAlreadyTranscribed(model: string): boolean {
    return this.allTranscriptions.some(t => t.model === model);
  }
  ```

**Issue**: Footer not sticking to bottom
- **Fix**: Use flexbox with `flex: 1` on content wrapper:
  ```css
  .app-container { min-height: 100vh; display: flex; flex-direction: column; }
  .content-wrapper { flex: 1; }
  ```

## Critical Configuration

### Port Configuration

**Backend**: Port 8001 (configured in multiple places)
- `src/presentation/frontend/src/environments/environment.ts` → `apiUrl: 'http://localhost:8001/api/v1'`
- Server startup: `--port 8001`

**Mismatch symptoms**: Frontend can't reach API, CORS errors, 404s.

### CUDA & GPU Requirements

- **Required**: NVIDIA GPU with CUDA 12.8+
- **PyTorch**: Version 2.7.0+ (for RTX 5090 sm_120 support)
- **RTX 5090 Compatibility**: Blackwell architecture (compute capability 12.0) requires CUDA 12.8+
  - CUDA 11.8 will fail with "CUDA kernel errors" on RTX 5090
  - Docker deployment automatically uses CUDA 12.8 base images
  - Local development requires manual PyTorch installation with cu128 wheel
- **Verify GPU**: `python -c "import torch; print(torch.cuda.is_available())"`
- Backend prints on startup: "GPU detected: NVIDIA GeForce RTX 5090"

### FFmpeg Path (Windows)

Backend automatically adds FFmpeg to PATH if found in project directory:
```python
ffmpeg_path = Path("ffmpeg-8.0.1-essentials_build/bin")
if ffmpeg_path.exists():
    os.environ["PATH"] = str(ffmpeg_path.absolute()) + os.pathsep + os.environ.get("PATH", "")
```

## API Design Patterns

### Duplicate Prevention

Re-transcription endpoint checks for existing completed transcription with same model:

```python
# retranscribe_audio_use_case.py
existing_transcriptions = await self.transcription_repo.get_by_audio_file_id(audio_file_id)
for trans in existing_transcriptions:
    if trans.model == model and trans.status == TranscriptionStatus.COMPLETED:
        return TranscriptionDTO.from_entity(trans)  # Return existing instead of creating duplicate
```

### Async/Await Pattern

All use cases are async for I/O operations:

```python
class RetranscribeAudioUseCase:
    async def execute(self, audio_file_id: str, model: str, language: Optional[str] = None) -> TranscriptionDTO:
        audio_file = await self.audio_file_repo.get_by_id(audio_file_id)
        result = await self.speech_service.transcribe(...)
        final_transcription = await self.transcription_repo.update(...)
        return TranscriptionDTO.from_entity(final_transcription)
```

### Server-Sent Events (SSE) for Progress

Model download progress uses SSE for real-time updates:

```python
@router.get("/models/download-progress/{model_name}")
async def stream_model_download_progress(model_name: str):
    async def event_generator():
        while downloading:
            yield f"data: {json.dumps({'progress': percent, 'bytes_downloaded': bytes})}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

Frontend consumes with EventSource:
```typescript
const eventSource = new EventSource(`${apiUrl}/models/download-progress/${model}`);
eventSource.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  this.downloadProgress = progress.progress;
};
```

### Audio Download Endpoint

The audio endpoint supports both streaming (for playback) and downloading (for saving):

**Endpoint**: `GET /api/v1/transcriptions/{transcription_id}/audio`

**Query Parameters**:
- `download` (optional, boolean, default: `false`): If `true`, forces browser download with `Content-Disposition: attachment`

**Download Filename Conversion**:
- `.webm` files automatically renamed to `.wav` in download filename (physical file unchanged)
- Other formats (.wav, .mp3, .flac, etc.) retain original extension
- Example: `recording-1767025956723.webm` downloads as `recording-1767025956723.wav`

**Backend Implementation** (`transcription_router.py`):
```python
@router.get("/transcriptions/{transcription_id}/audio")
async def get_audio_file(
    transcription_id: str,
    download: bool = Query(False, description="If true, sets Content-Disposition to attachment for download"),
    db: Session = Depends(get_db)
):
    # ... get audio file from database ...

    # Set Content-Disposition header for download
    headers = {}
    if download:
        # Replace .webm extension with .wav for better compatibility
        download_filename = audio_file.original_filename
        if download_filename.lower().endswith('.webm'):
            download_filename = download_filename[:-5] + '.wav'

        headers["Content-Disposition"] = f'attachment; filename="{download_filename}"'

    return FileResponse(
        path=audio_file.file_path,
        media_type=audio_file.mime_type,
        filename=audio_file.original_filename,
        headers=headers
    )
```

**Frontend Usage**:
```typescript
// For playback (inline)
const audioUrl = this.apiService.getAudioUrl(transcriptionId);
// Returns: http://localhost:8001/api/v1/transcriptions/{id}/audio

// For download
const downloadUrl = this.apiService.getAudioDownloadUrl(transcriptionId);
// Returns: http://localhost:8001/api/v1/transcriptions/{id}/audio?download=true

// Trigger download
const anchor = document.createElement('a');
anchor.href = downloadUrl;
anchor.click();
```

**Behavior**:
- `download=false` (default): Browser streams audio for inline playback
- `download=true`: Browser downloads file with original filename
- Backward compatible: Existing play functionality unchanged

## Testing Notes

### Backend Testing Strategy

- **Unit tests**: Test domain entities in isolation (no database)
- **Integration tests**: Test use cases with real database (use fixtures)
- **E2E tests**: Test API endpoints with TestClient

### Frontend Testing Strategy

- **Component tests**: Test Angular components with TestBed
- **Service tests**: Mock API calls with HttpClientTestingModule
- **E2E tests**: Use Protractor or Cypress for full user flows

## Commits & Git Workflow

All commits include standardized footer:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Use semantic commit messages:
- `Fix: Description` - Bug fixes
- `Feat: Description` - New features
- `Refactor: Description` - Code improvements without behavior change
- `Docs: Description` - Documentation updates
