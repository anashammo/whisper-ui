# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A GPU-accelerated voice-to-text transcription system using OpenAI Whisper with FastAPI backend and Angular frontend. Supports multiple model transcriptions per audio file (tiny/base/small/medium/large) with real-time progress tracking and grouped history view.

**Key Feature**: Users can upload audio once and transcribe with multiple Whisper models to compare accuracy/speed tradeoffs.

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
│   ├── services/              # Abstract service interfaces (SpeechRecognitionService)
│   └── exceptions/            # Domain-specific exceptions
│
├── application/                # Use cases orchestrate domain logic
│   ├── use_cases/             # TranscribeAudioUseCase, RetranscribeAudioUseCase, etc.
│   └── dto/                   # Data transfer objects for cross-layer communication
│
├── infrastructure/             # External implementations
│   ├── persistence/
│   │   ├── models/            # SQLAlchemy ORM models (NOT domain entities)
│   │   └── repositories/      # SQLiteTranscriptionRepository implements domain interfaces
│   ├── services/              # WhisperService (implements SpeechRecognitionService)
│   └── storage/               # LocalFileStorage for audio files
│
└── presentation/
    ├── api/                   # FastAPI routers, schemas, dependencies
    │   ├── routers/          # transcription_router, audio_file_router, etc.
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
   - Mark as PROCESSING, call WhisperService
   - Complete or fail based on result
4. **Repository** → persists to SQLite via SQLAlchemy ORM
5. **Frontend** → polls GET `/api/v1/transcriptions/{id}` for status updates

### Database Schema (SQLite)

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
  - model (tiny/base/small/medium/large)
  - text
  - status (pending/processing/completed/failed)
  - duration_seconds  # Copied from audio_file
  - created_at
  - completed_at
```

**Important**: When audio file is deleted, all associated transcriptions are automatically deleted (CASCADE).

## Development Commands

### Environment Setup

```bash
# Activate virtual environment (REQUIRED for all commands)
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Frontend setup
cd src/presentation/frontend
npm install
cd ../../..
```

### Running Servers

**CRITICAL**: Backend runs on port **8001**, frontend expects this in `environment.ts`.

```bash
# Option 1: Using convenience scripts (recommended)
python scripts/run_backend.py   # Terminal 1 - port 8001
python scripts/run_frontend.py  # Terminal 2 - port 4200

# Option 2: Manual start
python -m uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8001 --reload
cd src/presentation/frontend && ng serve

# Stop servers
python scripts/stop_all.py
```

**Access Points**:
- Frontend: http://localhost:4200
- Backend API: http://localhost:8001
- API Docs (Swagger): http://localhost:8001/docs

### Database Management

```bash
# Initialize database (creates whisper_transcriptions.db)
python scripts/init_db.py

# Clean up orphaned transcriptions (manual script)
python -c "from src.infrastructure.persistence.database import SessionLocal; ..."
```

### Model Management

```bash
# Download Whisper models (cached in ~/.cache/whisper/)
python scripts/download_whisper_model.py tiny
python scripts/download_whisper_model.py base
python scripts/download_whisper_model.py small
python scripts/download_whisper_model.py medium
python scripts/download_whisper_model.py large
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

## Key Implementation Patterns

### 1. Dependency Injection (Backend)

**Pattern**: FastAPI `Depends()` with factory functions in `dependencies.py`

**Singletons** (loaded once, reused across requests):
```python
@lru_cache()
def get_whisper_service() -> WhisperService:
    # Model loaded once, stays in GPU memory
    settings = get_settings()
    return WhisperService(settings)
```

**Per-request** (new instance per request):
```python
def get_transcribe_audio_use_case(
    db: Session = Depends(get_db),
    whisper_service: WhisperService = Depends(get_whisper_service),
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

- **Required**: NVIDIA GPU with CUDA 11.8+
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
