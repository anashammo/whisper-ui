# Whisper Voice-to-Text Transcription API

A professional voice-to-text transcription system using OpenAI Whisper, built with clean architecture principles. Features GPU-accelerated transcription, FastAPI backend, and Angular frontend.

## Recent Updates

**Latest Features (December 2025):**
- ✨ **Real-time Model Download Progress**: Visual progress bar showing actual download percentage (0-100%) when downloading new Whisper models
- 🤖 **Model Name Display**: See which Whisper model was used for each transcription in history and details views
- 📝 **Editable Transcriptions**: Edit transcription text directly in the UI
- 🎙️ **Browser Audio Recording**: Record audio directly from your microphone (up to 30 seconds)
- ▶️ **Audio Playback Controls**: Play/stop original audio with intuitive controls
- 🗑️ **Delete Functionality**: Remove transcriptions and associated audio files
- 🎛️ **Server Management Scripts**: Convenient Python scripts to start/stop backend and frontend servers

## Features

### Core Features
- **GPU-Accelerated Transcription**: Uses CUDA for fast audio transcription with NVIDIA RTX GPUs
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **REST API**: FastAPI with automatic OpenAPI documentation
- **Multiple Audio Formats**: Supports MP3, WAV, M4A, FLAC, OGG, WEBM
- **Transcription History**: SQLite database for storing transcriptions
- **On-Premises Deployment**: All data stored locally, no cloud dependencies

### Frontend Features
- **Browser Audio Recording**: Record audio directly from your microphone (up to 30 seconds)
- **File Upload**: Drag & drop audio file upload with preview
- **Editable Transcriptions**: Edit transcription text directly in the UI
- **Audio Playback**: Play original audio with play/stop controls
- **Model Selection**: Choose from 5 Whisper models (tiny, base, small, medium, large)
- **Real-time Download Progress**: Visual progress bar when downloading new models
- **Model Name Display**: See which model was used for each transcription
- **Delete Functionality**: Remove transcriptions and associated audio files
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
cd C:\Users\ahammo\Repos\Whisper
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

### 5. Download Whisper Model

```bash
python scripts/download_whisper_model.py base
```

Available models: `tiny`, `base`, `small`, `medium`, `large`

### 6. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env` to configure:
- `WHISPER_MODEL`: Model size (default: base)
- `WHISPER_DEVICE`: cuda or cpu (default: cuda)
- `MAX_FILE_SIZE_MB`: Maximum upload size (default: 25)
- `CORS_ORIGINS`: Allowed origins for CORS

### 7. Initialize Database

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
# Backend
cd C:\Users\ahammo\Repos\Whisper
./venv/Scripts/python.exe -m uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd src/presentation/frontend
npm install
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
- model: Whisper model (optional, default: 'base', options: tiny/base/small/medium/large)

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
curl -X POST "http://localhost:8000/api/v1/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "language=en"
```

### Using Python

```python
import requests

url = "http://localhost:8000/api/v1/transcriptions"
files = {"file": open("audio.mp3", "rb")}
data = {"language": "en"}

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

- **tiny**: Fastest, least accurate (~1GB RAM)
- **base**: Good balance (default, ~1GB RAM)
- **small**: Better accuracy (~2GB RAM)
- **medium**: High accuracy (~5GB RAM)
- **large**: Best accuracy (~10GB RAM)

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | base | Model size |
| `WHISPER_DEVICE` | cuda | Device (cuda/cpu) |
| `DATABASE_URL` | sqlite:///./whisper_transcriptions.db | Database connection |
| `UPLOAD_DIR` | ./uploads | Upload directory |
| `MAX_FILE_SIZE_MB` | 25 | Max upload size |
| `API_PORT` | 8000 | API port |
| `CORS_ORIGINS` | ["http://localhost:4200"] | Allowed origins |

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
