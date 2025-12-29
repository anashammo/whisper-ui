# Whisper Voice-to-Text Transcription API

A professional voice-to-text transcription system using OpenAI Whisper, built with clean architecture principles. Features GPU-accelerated transcription, FastAPI backend, and Angular frontend.

## Recent Updates

**Latest Features (December 2025):**
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
- **GPU-Accelerated Transcription**: Uses CUDA for fast audio transcription with NVIDIA RTX GPUs
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **REST API**: FastAPI with automatic OpenAPI documentation
- **Multiple Audio Formats**: Supports MP3, WAV, M4A, FLAC, OGG, WEBM
- **Transcription History**: SQLite database for storing transcriptions
- **On-Premises Deployment**: All data stored locally, no cloud dependencies

### Frontend Features
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
- **CUDA**: CUDA 11.8 or higher
- **cuDNN**: Compatible with CUDA version
- **Node.js**: 18+ (for Angular frontend)

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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PyTorch with CUDA Support

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
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

### 6. Download Whisper Model

```bash
python scripts/download_whisper_model.py base
```

Available models: `tiny`, `base`, `small`, `medium`, `large`, `turbo`

### 7. Install Frontend Dependencies

```bash
cd src/presentation/frontend
npm install
cd ../../..
```

### 8. Setup Environment Variables (Optional)

```bash
cp .env.example .env
```

Edit `.env` to configure:
- `WHISPER_MODEL`: Model size (default: base)
- `WHISPER_DEVICE`: cuda or cpu (default: cuda)
- `MAX_FILE_SIZE_MB`: Maximum upload size (default: 25)
- `CORS_ORIGINS`: Allowed origins for CORS

### 9. Initialize Database

```bash
python scripts/init_db.py
```

## Running the Application

### Start Servers

**Option 1: Using convenience scripts (Recommended)**

Open two separate terminals:

```bash
# Terminal 1 - Start Backend (port 8001)
python scripts/run_backend.py

# Terminal 2 - Start Frontend (port 4200)
python scripts/run_frontend.py
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
python scripts/stop_backend.py

# Stop frontend only
python scripts/stop_frontend.py

# Stop both servers at once
python scripts/stop_all.py
```

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
  "completed_at": "2025-12-28T10:30:15Z"
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
│       │   └── dependencies.py   # Dependency injection
│       └── frontend/             # Angular Web Application
│           ├── src/              # Angular source code
│           │   ├── app/          # Application modules
│           │   └── environments/ # Environment configs
│           ├── package.json      # NPM dependencies
│           └── angular.json      # Angular configuration
├── scripts/                       # Utility scripts
│   ├── run_backend.py            # Start backend server
│   ├── run_frontend.py           # Start frontend server
│   ├── stop_backend.py           # Stop backend server
│   ├── stop_frontend.py          # Stop frontend server
│   ├── stop_all.py               # Stop all servers
│   ├── init_db.py                # Initialize database
│   └── download_whisper_model.py # Download Whisper models
├── tests/                         # Tests
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
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
- **Download Size**: Disk space needed to store the model (cached in `~/.cache/whisper/`)
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

The `scripts/` directory contains helpful utilities:

### Server Management

| Script | Description |
|--------|-------------|
| `run_backend.py` | Start the FastAPI backend server on port 8001 |
| `run_frontend.py` | Start the Angular dev server on port 4200 |
| `stop_backend.py` | Stop the backend server |
| `stop_frontend.py` | Stop the frontend server |
| `stop_all.py` | Stop both backend and frontend servers |

### Database & Models

| Script | Description |
|--------|-------------|
| `init_db.py` | Initialize the SQLite database and create tables |
| `download_whisper_model.py` | Download a specific Whisper model (tiny/base/small/medium/large/turbo) |

### Usage Examples

```bash
# Download a specific model
python scripts/download_whisper_model.py medium

# Initialize database
python scripts/init_db.py

# Start servers
python scripts/run_backend.py  # Terminal 1
python scripts/run_frontend.py # Terminal 2

# Stop servers
python scripts/stop_all.py
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
- Ensure CUDA toolkit is installed
- Check PyTorch CUDA installation: `python -c "import torch; print(torch.cuda.is_available())"`

### Import Errors

If you encounter import errors:
- Ensure virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Database Errors

If database errors occur:
- Delete the database file and run `python scripts/init_db.py` again
- Check file permissions on the database file

## License

This project is for educational and internal use.

## Support

For issues or questions, please refer to the project documentation or create an issue in the repository.
