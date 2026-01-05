# Whisper Voice-to-Text Transcription API

A professional voice-to-text transcription system using **faster-whisper** (CTranslate2 backend), built with clean architecture principles. Features GPU-accelerated transcription up to 4x faster than OpenAI Whisper, Voice Activity Detection (VAD), FastAPI backend, and Angular frontend.

## Recent Updates

**Latest Features (January 2026):**
- 🚀 **faster-whisper Migration**: Up to 4x faster transcription using CTranslate2 optimization
- 🎯 **Voice Activity Detection (VAD)**: Optional Silero VAD to filter silence and improve accuracy
- ✨ **LLM Enhancement**: Enhance transcriptions with local LLM (Ollama/LM Studio) for grammar correction, formatting, and filler word removal
- 🤖 **Dual Text Display**: View original Whisper transcription and LLM-enhanced version side-by-side
- 🧠 **LangGraph Integration**: Intelligent transcription enhancement using LangGraph workflow framework
- 🎭 **Multiple Model Transcriptions**: Transcribe the same audio file with different Whisper models and compare results
- 📂 **Grouped History View**: Audio files grouped with expandable sections showing all transcriptions per file
- 🔄 **Re-transcription Support**: Re-transcribe existing audio files with different models without re-uploading
- 🏷️ **Model Tabs**: Switch between different model transcriptions with intuitive tabbed interface
- ✨ **Real-time Model Download Progress**: Visual progress bar showing actual download percentage (0-100%) when downloading new Whisper models
- 🤖 **Model Name Display**: See which Whisper model was used for each transcription in history and details views
- 📝 **Editable Transcriptions**: Edit transcription text directly in the UI
- 🎙️ **Browser Audio Recording**: Record audio directly from your microphone (up to 30 seconds)
- ▶️ **Audio Playback Controls**: Play/stop original audio with intuitive controls
- 🗑️ **Delete Functionality**: Remove transcriptions and associated audio files
- 🎛️ **Server Management Scripts**: Convenient Python scripts to start/stop backend and frontend servers
- ©️ **Copyright Footer**: Professional footer with links to this repository and OpenAI Whisper

## Features

### Core Features
- **GPU-Accelerated Transcription**: Uses CUDA for fast audio transcription with NVIDIA RTX GPUs (up to 4x faster with faster-whisper)
- **Voice Activity Detection (VAD)**: Optional Silero VAD to filter silence and improve transcription accuracy
- **LLM Enhancement**: Enhance transcriptions with local LLM (Ollama/LM Studio) for grammar, formatting, and filler removal
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **REST API**: FastAPI with automatic OpenAPI documentation
- **Multiple Audio Formats**: Supports MP3, WAV, M4A, FLAC, OGG, WEBM
- **Transcription History**: SQLite database for storing transcriptions
- **On-Premises Deployment**: All data stored locally, no cloud dependencies

### Frontend Features
- **LLM Enhancement**: Opt-in LLM enhancement during upload/recording/re-transcription with manual enhance button
- **Dual Text Areas**: Side-by-side view of original Whisper and LLM-enhanced transcriptions
- **LLM Processing Tracking**: Real-time status and processing time display for LLM enhancements
- **Multiple Model Transcriptions**: Transcribe the same audio file with different models and compare results
- **Grouped History View**: Audio files grouped with expandable sections showing all transcriptions
- **Model Tabs**: Switch between different model transcriptions with tabbed interface
- **Re-transcription Dialog**: Re-transcribe existing audio files with different models
- **Browser Audio Recording**: Record audio directly from your microphone (up to 30 seconds)
- **File Upload**: Drag & drop audio file upload with preview
- **Editable Transcriptions**: Edit transcription text directly in the UI
- **Audio Playback**: Play original audio with play/stop controls
- **Model Selection**: Choose from 6 Whisper models (tiny, base, small, medium, large, turbo)
- **Smart Model Ordering**: Transcriptions automatically sorted by model size (smallest to largest)
- **Intelligent Re-transcription**: Only shows unused models in dropdown, preventing duplicates
- **Audio File Metadata**: View audio file ID, original filename, and upload date in detail view
- **Real-time Download Progress**: Visual progress bar when downloading new models
- **Model Name Display**: See which model was used for each transcription
- **Delete Functionality**: Remove transcriptions and associated audio files
- **Custom Popups**: Professional modal dialogs for confirmations and alerts
- **WER Tool Integration**: Quick access to Word Error Rate comparison tool from footer
- **Dark Mode UI**: Modern, clean interface with dark theme

## Architecture

The project follows clean architecture principles:

```
src/
├── domain/           # Core business logic (entities, repositories interfaces)
├── application/      # Use cases and business workflows
├── infrastructure/   # External implementations (Whisper, SQLite, file storage)
└── presentation/     # Presentation layer
    ├── api/          # FastAPI REST API
    └── frontend/     # Angular web application
```

## System Requirements

### Hardware
- **GPU**: NVIDIA GPU with CUDA support (required)
- **RAM**: Minimum 8GB (16GB recommended for larger models)
- **Disk**: Sufficient space for audio files and Whisper models (~1-3GB per model)

### Software
- **Python**: 3.9 or higher
- **CUDA**: CUDA 12.6 or higher (required for RTX 5090 and newer GPUs)
- **PyTorch**: 2.5.0+ (required for RTX 5090 sm_120 support)
- **cuDNN**: Compatible with CUDA version
- **Node.js**: 18+ (for Angular frontend)

**Note**: RTX 5090 (Blackwell architecture) requires CUDA 12.6+ and PyTorch 2.5.0+ with sm_120 compiled binaries. Older CUDA versions (11.8) will cause "CUDA kernel errors".

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/anashammo/whisper-ui.git
cd whisper-ui
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install UV Package Manager (Optional but Recommended)

UV is 10-100x faster than pip for installing Python dependencies:

```bash
# Install UV
python scripts/setup/install_uv.py

# Verify installation
uv --version
```

### 4. Install Dependencies

**Option A: Using UV (Recommended - 10-100x faster):**
```bash
uv pip install -r src/presentation/api/requirements.txt
```

**Option B: Using pip:**
```bash
pip install -r src/presentation/api/requirements.txt
```

### 5. Install PyTorch with CUDA Support

**For RTX 5090 and newer GPUs (CUDA 12.8):**
```bash
# With UV (recommended)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Or with pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**For older GPUs (CUDA 11.8):**
```bash
# With UV (recommended)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or with pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Verify installation:**
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

### 5. Install FFmpeg

**Windows:**
1. Download FFmpeg from https://www.gyan.dev/ffmpeg/builds/
2. Extract to project directory (e.g., `ffmpeg-8.0.1-essentials_build/`)
3. The backend will automatically add FFmpeg to PATH on startup

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 6. Whisper Model Download

Models are automatically downloaded on first use by faster-whisper and cached in `~/.cache/huggingface/`.

Available models: `tiny`, `base`, `small`, `medium`, `large`, `turbo`

### 7. Install Frontend Dependencies

```bash
cd src/presentation/frontend
npm install
cd ../../..
```

### 8. Setup Environment Variables (Optional)

**Backend configuration:**
```bash
# Copy backend environment template
cp src/presentation/api/.env.example src/presentation/api/.env
```

Edit `src/presentation/api/.env` to configure:
- `WHISPER_MODEL`: Model size (default: base)
- `WHISPER_DEVICE`: cuda or cpu (default: cuda)
- `MAX_FILE_SIZE_MB`: Maximum upload size (default: 25)
- `CORS_ORIGINS`: Allowed origins for CORS
- `LLM_BASE_URL`: Base URL for local LLM API (default: http://localhost:11434/v1)
- `LLM_MODEL`: LLM model name (default: llama3)
- `LLM_TIMEOUT_SECONDS`: Timeout for LLM requests (default: 60)
- `LLM_TEMPERATURE`: LLM temperature 0.0-1.0 (default: 0.3)

**Frontend configuration:**

Frontend uses TypeScript environment files (`src/presentation/frontend/src/environments/environment.ts`).
No .env file needed - API URL is configured in the environment.ts file.

### 9. Setup LLM Enhancement (Optional)

To enable transcription enhancement with local LLM:

**Option 1: Using Ollama (Recommended)**

1. Install Ollama from https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull llama3
   ```
3. The server runs on http://localhost:11434 by default

**Option 2: Using LM Studio**

1. Install LM Studio from https://lmstudio.ai
2. Download a model from the UI
3. Start the local server (default: http://localhost:1234/v1)
4. Update `.env`: `LLM_BASE_URL=http://localhost:1234/v1`

The LLM enhancement feature provides:
- Grammar and punctuation correction
- Formatting and structure improvements
- Filler word removal (um, uh, like, etc.)
- Preserves original meaning and technical terms

### 10. Initialize Database

```bash
python scripts/setup/init_db.py
```

## Running the Application

### Start Servers

**Option 1: Using convenience scripts (Recommended)**

Open two separate terminals:

```bash
# Terminal 1 - Start Backend (port 8001)
python scripts/server/run_backend.py

# Terminal 2 - Start Frontend (port 4200)
python scripts/server/run_frontend.py
```

**Option 2: Manual start**

```bash
# Backend (from project root)
python -m uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend (from project root)
cd src/presentation/frontend
ng serve
```

The servers will be available at:
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/v1/health
- **Frontend**: http://localhost:4200

### Stop Servers

```bash
# Stop backend only
python scripts/server/stop_backend.py

# Stop frontend only
python scripts/server/stop_frontend.py

# Stop both servers at once
python scripts/server/stop_all.py
```

## Docker Deployment

For production deployment or containerized development, use Docker:

### Prerequisites

- Docker Engine 20.10+ with Docker Compose
- NVIDIA Container Toolkit (for GPU support)
- 20GB+ free disk space

### Quick Start

```bash
# 1. Configure backend environment variables
cp src/presentation/api/.env.docker src/presentation/api/.env
# Edit src/presentation/api/.env and set secure POSTGRES_PASSWORD

# 2. Build and run all services
python scripts/docker/run.py --build

# 3. Access the application
# Frontend: http://localhost:4200
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Docker Management Scripts

All Docker operations are managed via Python scripts in `scripts/docker/`:

```bash
# Build images
python scripts/docker/build.py              # Build all services
python scripts/docker/build.py --backend    # Build backend only
python scripts/docker/build.py --frontend   # Build frontend only
python scripts/docker/build.py --no-cache   # Clean build

# Run services
python scripts/docker/run.py                # Start core services
python scripts/docker/run.py --build        # Build and start
python scripts/docker/run.py --detach       # Run in background
python scripts/docker/run.py --ngrok        # Include ngrok tunnels (requires NGROK_AUTHTOKEN)

# View logs
python scripts/docker/logs.py               # Core service logs
python scripts/docker/logs.py backend       # Backend only
python scripts/docker/logs.py --follow      # Follow logs
python scripts/docker/logs.py --tail 100    # Last 100 lines
python scripts/docker/logs.py --ngrok -f    # Include ngrok logs

# Stop services
python scripts/docker/stop.py               # Stop all containers
python scripts/docker/stop.py -v            # Stop and remove volumes (WARNING: deletes data)
python scripts/docker/stop.py --ngrok-only  # Stop only ngrok tunnels

# Open shell in container
python scripts/docker/shell.py backend      # Backend shell
python scripts/docker/shell.py frontend     # Frontend shell
python scripts/docker/shell.py postgres     # PostgreSQL shell

# Clean up resources
python scripts/docker/clean.py              # Remove containers
python scripts/docker/clean.py --images     # Remove images
python scripts/docker/clean.py --volumes    # Remove volumes (WARNING: deletes data)
python scripts/docker/clean.py --all        # Remove everything (WARNING)

# Rebuild and restart
python scripts/docker/rebuild.py            # Stop, rebuild, and restart core services
python scripts/docker/rebuild.py --ngrok    # Rebuild with ngrok tunnels
```

### Ngrok Tunnels (Optional)

For external access via public URLs, use ngrok tunnels:

```bash
# Set your ngrok auth token in .env
NGROK_AUTHTOKEN=your_token_here

# Start with ngrok
python scripts/docker/run.py --ngrok --build --detach
```

**Public URLs** (requires reserved domains in ngrok account):
- Backend: https://anas-hammo-whisper-backend.ngrok.dev
- Frontend: https://anas-hammo-whisper-frontend.ngrok.dev
- LLM: https://anas-hammo-whisper-llm.ngrok.dev

**Web Inspection UI** (for debugging):
- Backend: http://localhost:4050
- Frontend: http://localhost:4051
- LLM: http://localhost:4052

See [DOCKER.md](DOCKER.md#ngrok-tunnels) for detailed ngrok configuration.

### Docker Architecture

The Docker deployment consists of three services:

1. **PostgreSQL Database** (`postgres`)
   - Image: `postgres:15-alpine`
   - Port: 5432 (internal only)
   - Volume: `postgres-data` → PostgreSQL data and logs

2. **FastAPI Backend** (`backend`)
   - GPU-accelerated with NVIDIA CUDA 12.6 (supports RTX 5090 and all older GPUs)
   - Port: 8001 (exposed to host)
   - Volumes:
     - `whisper-uploads` → Audio files
     - `huggingface-cache` → Whisper model cache (HuggingFace Hub)
     - Source code mounted for hot-reload (development)

3. **Angular Frontend** (`frontend`)
   - Node.js 18 with ng serve
   - Port: 4200 (exposed to host)
   - Volume: Source code mounted for hot-reload (development)

### Environment Configuration

Edit `src/presentation/api/.env` to configure Docker services:

```bash
# PostgreSQL Database
POSTGRES_USER=whisper
POSTGRES_PASSWORD=change_this_secure_password_in_production
POSTGRES_DB=whisper_db

# Whisper Model Preloading
PRELOAD_MODELS=base              # Models to download on startup (comma-separated: tiny,base,small)
FORCE_DOWNLOAD=                  # Set to "true" to force re-download

# Port Mapping
BACKEND_PORT=8001
FRONTEND_PORT=4200
```

### Hot-Reload Development

Both backend and frontend support hot-reload without rebuilding containers:

- **Backend**: Source code changes trigger Uvicorn auto-reload
- **Frontend**: Angular watches for file changes and recompiles automatically

No rebuild needed for code changes - containers automatically detect and apply updates.

### Volume Persistence

All persistent data is stored in Docker volumes (not in container images):

- **postgres-data**: PostgreSQL database and logs
- **whisper-uploads**: User-uploaded audio files
- **huggingface-cache**: Downloaded Whisper models (~1-3GB per model)

Data persists across container restarts and rebuilds.

### GPU Support

The backend container requires NVIDIA GPU with Docker GPU support:

```bash
# Verify GPU availability in container
python scripts/docker/shell.py backend
python -c "import torch; print(torch.cuda.is_available())"  # Should print: True
```

If GPU is not detected:
- Ensure NVIDIA Container Toolkit is installed
- Verify `nvidia-smi` works on host
- Check `docker-compose.yml` has correct GPU configuration

### Model Management

Whisper models are automatically downloaded on first container startup:

```bash
# Download specific models (set in .env)
PRELOAD_MODELS=tiny,base,small

# Force re-download models
FORCE_DOWNLOAD=true python scripts/docker/run.py --build
```

Models are cached in `huggingface-cache` volume and reused across rebuilds.

For detailed Docker deployment guide, see [DOCKER.md](DOCKER.md).

## API Endpoints

### Transcription Endpoints

#### Upload and Transcribe Audio
```http
POST /api/v1/transcriptions
Content-Type: multipart/form-data

Parameters:
- file: Audio file (required)
- language: Language code (optional, e.g., 'en', 'es')
- model: Whisper model (optional, default: 'base', options: tiny/base/small/medium/large/turbo)
- enable_llm_enhancement: Boolean (optional, default: false) - Enable LLM enhancement
- vad_filter: Boolean (optional, default: false) - Enable Voice Activity Detection

Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_file_id": "660e8400-e29b-41d4-a716-446655440001",
  "text": "Transcribed text here...",
  "status": "completed",
  "language": "en",
  "model": "base",
  "duration_seconds": 45.3,
  "created_at": "2025-12-28T10:30:00Z",
  "completed_at": "2025-12-28T10:30:15Z",
  "enable_llm_enhancement": false,
  "enhanced_text": null,
  "llm_processing_time_seconds": null,
  "llm_enhancement_status": null,
  "llm_error_message": null
}
```

#### Enhance Transcription with LLM
```http
POST /api/v1/transcriptions/{transcription_id}/enhance

Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_file_id": "660e8400-e29b-41d4-a716-446655440001",
  "text": "Transcribed text here...",
  "enhanced_text": "Enhanced transcribed text with proper grammar and formatting.",
  "status": "completed",
  "language": "en",
  "model": "base",
  "duration_seconds": 45.3,
  "created_at": "2025-12-28T10:30:00Z",
  "completed_at": "2025-12-28T10:30:15Z",
  "enable_llm_enhancement": true,
  "llm_processing_time_seconds": 2.35,
  "llm_enhancement_status": "completed",
  "llm_error_message": null
}
```

#### Get Transcription History
```http
GET /api/v1/transcriptions?limit=100&offset=0

Response:
{
  "items": [...],
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

#### Get Specific Transcription
```http
GET /api/v1/transcriptions/{transcription_id}
```

#### Delete Transcription
```http
DELETE /api/v1/transcriptions/{transcription_id}

Response: 204 No Content
```

#### Download Original Audio
```http
GET /api/v1/transcriptions/{transcription_id}/audio

Response: Audio file (binary stream)
```

### Audio File Endpoints

#### Re-transcribe Existing Audio File
```http
POST /api/v1/audio-files/{audio_file_id}/transcriptions?model={model}&language={language}

Parameters:
- audio_file_id: ID of the existing audio file (required, path parameter)
- model: Whisper model (required, query parameter, options: tiny/base/small/medium/large/turbo)
- language: Language code (optional, query parameter, e.g., 'en', 'es')

Response:
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "audio_file_id": "660e8400-e29b-41d4-a716-446655440001",
  "text": null,
  "status": "pending",
  "language": "en",
  "model": "medium",
  "duration_seconds": 45.3,
  "created_at": "2025-12-28T10:35:00Z",
  "completed_at": null
}

Notes:
- If a completed transcription with the same model already exists, returns the existing one
- Transcription status will be "pending" or "processing" initially
- Poll GET /api/v1/transcriptions/{id} to check completion status
```

#### Get All Transcriptions for Audio File
```http
GET /api/v1/audio-files/{audio_file_id}/transcriptions

Response:
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "audio_file_id": "660e8400-e29b-41d4-a716-446655440001",
    "text": "Transcribed text here...",
    "status": "completed",
    "language": "en",
    "model": "base",
    "duration_seconds": 45.3,
    "created_at": "2025-12-28T10:30:00Z",
    "completed_at": "2025-12-28T10:30:15Z"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "audio_file_id": "660e8400-e29b-41d4-a716-446655440001",
    "text": "Transcribed text here...",
    "status": "completed",
    "language": "en",
    "model": "medium",
    "duration_seconds": 45.3,
    "created_at": "2025-12-28T10:35:00Z",
    "completed_at": "2025-12-28T10:35:25Z"
  }
]

Notes:
- Returns all transcriptions for the specified audio file
- Sorted by created_at DESC (newest first)
- Raises 404 if audio file not found
```

### Model Management Endpoints

#### Check Model Status
```http
GET /api/v1/models/status/{model_name}

Response:
{
  "model_name": "medium",
  "is_cached": true,
  "is_loaded": false
}
```

#### Stream Model Download Progress (SSE)
```http
GET /api/v1/models/download-progress/{model_name}

Response: Server-Sent Events stream
data: {"status": "downloading", "progress": 45.2, "bytes_downloaded": 678000000, "total_bytes": 1500000000}
```

#### Get Available Models
```http
GET /api/v1/models/available

Response:
{
  "models": [
    {"code": "tiny", "name": "Tiny", "size": "~75MB", ...},
    {"code": "base", "name": "Base", "size": "~150MB", ...},
    ...
  ]
}
```

### Health Endpoints

#### Health Check
```http
GET /api/v1/health

Response:
{
  "status": "healthy",
  "message": "Whisper Transcription API is running"
}
```

#### System Information
```http
GET /api/v1/info

Response:
{
  "app_name": "Whisper Transcription API",
  "app_version": "1.0.0",
  "whisper_model": {...},
  "max_file_size_mb": 25
}
```

## Usage Example

### Using cURL

```bash
curl -X POST "http://localhost:8001/api/v1/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "model=base"
```

### Using Python

```python
import requests

url = "http://localhost:8001/api/v1/transcriptions"
files = {"file": open("audio.mp3", "rb")}
data = {"language": "en", "model": "base"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## Project Structure

```
Whisper/
├── src/
│   ├── domain/                    # Business logic (Domain Layer)
│   │   ├── entities/             # Transcription, AudioFile
│   │   ├── repositories/         # Repository interfaces
│   │   ├── services/             # Service interfaces
│   │   └── exceptions/           # Domain exceptions
│   ├── application/               # Use cases (Application Layer)
│   │   ├── use_cases/            # Business workflows
│   │   ├── dto/                  # Data transfer objects
│   │   └── interfaces/           # Application interfaces
│   ├── infrastructure/            # External implementations (Infrastructure Layer)
│   │   ├── config/               # Settings
│   │   ├── persistence/          # SQLAlchemy models & repos
│   │   ├── services/             # Whisper service
│   │   └── storage/              # File storage
│   └── presentation/              # Presentation Layer
│       ├── api/                  # FastAPI REST API
│       │   ├── routers/          # API endpoints
│       │   ├── schemas/          # Pydantic models
│       │   ├── dependencies.py   # Dependency injection
│       │   ├── Dockerfile        # Backend Docker image
│       │   ├── requirements.txt  # Python dependencies
│       │   ├── .env.example      # Backend env template (local)
│       │   └── .env.docker       # Backend env template (Docker)
│       └── frontend/             # Angular Web Application
│           ├── src/              # Angular source code
│           │   ├── app/          # Application modules
│           │   └── environments/ # TypeScript environment configs
│           ├── package.json      # NPM dependencies
│           ├── angular.json      # Angular configuration
│           └── Dockerfile        # Frontend Docker image
├── scripts/                       # Utility scripts
│   ├── setup/                    # Setup & initialization
│   │   ├── init_db.py            # Initialize database
│   │   └── download_whisper_model.py # Download Whisper models
│   ├── server/                   # Server management
│   │   ├── run_backend.py        # Start backend server
│   │   ├── run_dev.py            # Start with .env config
│   │   ├── run_frontend.py       # Start frontend server
│   │   ├── stop_backend.py       # Stop backend server
│   │   ├── stop_frontend.py      # Stop frontend server
│   │   └── stop_all.py           # Stop all servers
│   ├── maintenance/              # Database utilities
│   │   ├── check_db_status.py    # Check database status
│   │   ├── show_db_contents.py   # Inspect database
│   │   ├── debug_transcriptions.py # Debug transcriptions
│   │   ├── auto_cleanup_orphans.py # Auto cleanup
│   │   └── cleanup_orphaned_transcriptions.py # Manual cleanup
│   └── migrations/               # Database migrations
│       ├── migrate_add_model_column.py # Add model column
│       └── migrate_add_processing_time.py # Add processing time
├── tests/                         # Tests
├── docker-compose.yml             # Docker orchestration
├── .env.example                   # Root env template (backward compat)
└── README.md                      # This file

**Note**: Backend configuration files (Dockerfile, requirements.txt, .env) are now located in `src/presentation/api/` for better organization.
```

## Configuration

### Whisper Models

Each Whisper model has different trade-offs between speed, accuracy, and resource usage:

| Model | Parameters | Download Size | VRAM Required | Speed | Best For |
|-------|-----------|---------------|---------------|-------|----------|
| **tiny** | 39M | ~75MB | ~1GB | ~10x faster | Quick drafts, testing |
| **base** | 74M | ~150MB | ~1GB | ~7x faster | General use (recommended) |
| **small** | 244M | ~500MB | ~2GB | ~4x faster | Better accuracy |
| **medium** | 769M | ~1.5GB | ~5GB | ~2x faster | Important transcriptions |
| **large** | 1550M | ~3GB | ~10GB | 1x (baseline) | Best accuracy |
| **turbo** | 809M | ~3GB | ~6GB | ~8x faster | Speed + accuracy optimized |

**Notes**:
- **Download Size**: Disk space needed to store the model (cached in `~/.cache/huggingface/`)
- **VRAM Required**: GPU memory needed for inference (important for GPU users)
- **Speed**: Relative to large model on A100 GPU (actual speed depends on hardware)
- **Turbo Model**: Optimized variant with 8x faster speed, not suitable for translation tasks
- **English-only variants**: Models with `.en` suffix (e.g., `tiny.en`, `base.en`) perform better for English audio, especially for smaller models

**Model Selection Guide**:
- **For development/testing**: Use `tiny` for quick iteration
- **For production (general)**: Use `base` for good balance of speed and accuracy
- **For high-quality transcriptions**: Use `medium` or `turbo`
- **For maximum accuracy**: Use `large` (requires powerful GPU)
- **For English-only audio**: Consider using `.en` variants for better accuracy

**Additional Resources**:
- [OpenAI Whisper GitHub Repository](https://github.com/openai/whisper) - Official model documentation and benchmarks
- [Whisper Model Card](https://github.com/openai/whisper/blob/main/model-card.md) - Detailed performance metrics and limitations
- Model specifications are based on OpenAI's official repository (last updated: December 2025)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | base | Model size |
| `WHISPER_DEVICE` | cuda | Device (cuda/cpu) |
| `DATABASE_URL` | sqlite:///./whisper_transcriptions.db | Database connection |
| `UPLOAD_DIR` | ./uploads | Upload directory |
| `MAX_FILE_SIZE_MB` | 25 | Max upload size |
| `MAX_DURATION_SECONDS` | 30 | Max audio duration |
| `API_PORT` | 8001 | API port |
| `CORS_ORIGINS` | ["http://localhost:4200"] | Allowed origins |

## Utility Scripts

The `scripts/` directory contains organized utilities in subfolders:

### Setup & Initialization (`scripts/setup/`)

| Script | Description |
|--------|-------------|
| `init_db.py` | Initialize the SQLite database and create tables |
| `download_whisper_model.py` | Download a specific Whisper model (tiny/base/small/medium/large/turbo) |

### Server Management (`scripts/server/`)

| Script | Description |
|--------|-------------|
| `run_backend.py` | Start the FastAPI backend server on port 8001 |
| `run_dev.py` | Start backend with .env configuration loading |
| `run_frontend.py` | Start the Angular dev server on port 4200 |
| `stop_backend.py` | Stop the backend server |
| `stop_frontend.py` | Stop the frontend server |
| `stop_all.py` | Stop both backend and frontend servers |

### Database Maintenance (`scripts/maintenance/`)

| Script | Description |
|--------|-------------|
| `check_db_status.py` | Verify database health and check for issues |
| `show_db_contents.py` | Inspect database contents and records |
| `debug_transcriptions.py` | Debug transcription-related issues |
| `auto_cleanup_orphans.py` | Automatically clean up orphaned transcriptions |
| `cleanup_orphaned_transcriptions.py` | Manually clean up orphaned records |

### Database Migrations (`scripts/migrations/`)

| Script | Description |
|--------|-------------|
| `migrate_add_model_column.py` | Migration: Add model column to transcriptions |
| `migrate_add_processing_time.py` | Migration: Add processing_time_seconds column |
| `migrate_add_vad_filter.py` | Migration: Add vad_filter_used column for VAD support |

### Usage Examples

```bash
# Download a specific model
python scripts/setup/download_whisper_model.py medium

# Initialize database
python scripts/setup/init_db.py

# Start servers
python scripts/server/run_backend.py  # Terminal 1
python scripts/server/run_frontend.py # Terminal 2

# Stop servers
python scripts/server/stop_all.py

# Database maintenance
python scripts/maintenance/check_db_status.py
python scripts/maintenance/show_db_contents.py
```

## Development

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
```

### Type Checking

```bash
mypy src/
```

## Clean Architecture Benefits

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations
4. **Dependency Inversion**: Domain doesn't depend on frameworks

## Troubleshooting

### CUDA Not Available

If you see "CUDA requested but not available":
- Verify NVIDIA GPU drivers are installed
- Ensure CUDA toolkit is installed (CUDA 12.6+ for RTX 5090)
- Check PyTorch CUDA installation: `python -c "import torch; print(torch.cuda.is_available())"`

### RTX 5090 CUDA Kernel Errors

If you see "CUDA kernel errors" or "no kernel image available for device" with RTX 5090:

**Root Cause**: RTX 5090 (Blackwell architecture, sm_120) requires CUDA 12.6+ and PyTorch 2.5.0+. CUDA 11.8 does not support this GPU.

**Solutions**:
1. **Update CUDA toolkit to 12.6+**:
   - Download from https://developer.nvidia.com/cuda-downloads
   - Install and restart system

2. **Reinstall PyTorch with CUDA 12.6 support**:
   ```bash
   # Uninstall old version
   pip uninstall torch torchvision torchaudio

   # Reinstall with CUDA 12.6 (using UV is faster)
   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   # Or with pip:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

3. **Verify PyTorch detects CUDA 12.6**:
   ```bash
   python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"
   # Should show: PyTorch: 2.5.0+cu126, CUDA: 12.6
   ```

4. **Docker Users**: Rebuild with CUDA 12.6 base images
   ```bash
   python scripts/docker/rebuild.py --no-cache
   ```

**Note**: This issue only affects RTX 5090 and newer Blackwell GPUs. Older GPUs work fine with CUDA 11.8.

### Import Errors

If you encounter import errors:
- Ensure virtual environment is activated
- Verify all dependencies are installed:
  - With UV: `uv pip install -r src/presentation/api/requirements.txt`
  - With pip: `pip install -r src/presentation/api/requirements.txt`

### Database Errors

If database errors occur:
- Delete the database file and run `python scripts/setup/init_db.py` again
- Check file permissions on the database file

## License

This project is for educational and internal use.

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/anashammo/whisper-ui?utm_source=oss&utm_medium=github&utm_campaign=anashammo%2Fwhisper-ui&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)
