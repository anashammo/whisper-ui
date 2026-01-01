# Docker Implementation Plan

**Feature**: Dockerize the Whisper Voice-to-Text Transcription System
**Date**: 2025-12-31
**Status**: Ready for Implementation
**User Decisions**: Confirmed

---

## Executive Summary

This plan outlines the complete dockerization of the Whisper transcription system with:
- **Backend API**: FastAPI with CUDA GPU support
- **Frontend**: Angular SPA with `ng serve` (all environments - simplified, no Nginx)
- **Database**: PostgreSQL for ALL environments (data and logs in volumes)
- **Model Caching**: Smart pre-download with volume persistence
- **Complete Orchestration**: Production and development Docker Compose configurations

**Key Innovations**:
- Smart model pre-download script with existence checking and override flag
- PostgreSQL for all environments (consistent database, no dev/prod differences)
- Simplified frontend with ng serve (no Nginx complexity)
- Complete volume-based persistence (database data, logs, uploads, models)
- Development-friendly setup with hot-reload everywhere

---

## User Decisions (Confirmed 2025-12-31)

1. ✅ **LLM Service**: External (Option B) - Document connection, keep flexible
2. ✅ **Whisper Models**: Smart pre-download at startup with volume caching
   - Check existence first, download only missing models
   - Override flag to force re-download
   - Volume mount for persistence (NOT in image)
3. ✅ **Database**: PostgreSQL for ALL environments (development AND production)
   - Consistent database across all environments
   - No SQLite usage in Docker deployment
   - **Data and logs stored in volumes** (NOT in image)
4. ✅ **Frontend**: Use `ng serve` for ALL environments (simplified, no Nginx)
   - Same setup for development and production
   - Hot-reload support built-in
5. ✅ **Port Exposure**: Both ports (4200 for frontend, 8001 for backend)
6. ✅ **Deployment**: Local development/testing + Production server

---

## 1. Architecture Overview

### 1.1 Production Architecture (docker-compose.yml)

```
┌────────────────────────────────────────────────────────────┐
│                  Docker Compose Network                    │
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │   Frontend   │───▶│   Backend    │───▶│ PostgreSQL │  │
│  │  (ng serve)  │    │   (FastAPI)  │    │   (DB)     │  │
│  │  Port: 4200  │    │   Port: 8001 │    │  Port: -   │  │
│  └──────────────┘    └──────┬───────┘    └─────┬──────┘  │
│                             │                   │         │
│                    ┌────────▼────────┐          │         │
│                    │  GPU (NVIDIA)   │          │         │
│                    │  Runtime Access │          │         │
│                    └─────────────────┘          │         │
│                                                  │         │
│  Volumes (Persistent Storage):                  │         │
│  - postgres-data ←───────────────────────────────┘         │
│    (PostgreSQL database data + logs)                      │
│  - whisper-uploads (uploaded audio files)                 │
│  - whisper-cache (Whisper models - smart cached)          │
└────────────────────────────────────────────────────────────┘
```

### 1.2 Development Architecture (docker-compose.dev.yml)

```
┌────────────────────────────────────────────────────────────┐
│             Docker Compose Development Network             │
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │   Frontend   │───▶│   Backend    │───▶│ PostgreSQL │  │
│  │  (ng serve)  │    │   (FastAPI)  │    │  (Dev DB)  │  │
│  │  Port: 4200  │    │   Port: 8001 │    │            │  │
│  │ + Hot Reload │    │ + Hot Reload │    │            │  │
│  └──────────────┘    └──────────────┘    └────────────┘  │
│       ↑                      ↑                            │
│       │                      │                            │
│   [Source Code Volume Mount for Hot Reload]               │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Current System Analysis

### 2.1 Backend Architecture
- **Framework**: FastAPI (Python 3.9+)
- **AI Engine**: OpenAI Whisper (GPU-accelerated with CUDA)
- **Database**: SQLite (whisper_transcriptions.db)
- **File Storage**: Local filesystem (./uploads directory)
- **Audio Processing**: FFmpeg
- **LLM Enhancement**: LangGraph + Local LLM (Ollama/LM Studio)
- **Port**: 8001

### 2.2 Frontend Architecture
- **Framework**: Angular 17
- **Build Tool**: Angular CLI
- **Server**: ng serve (port 4200) - used for ALL environments
- **API Endpoint**: http://localhost:8001/api/v1 (or http://backend:8001/api/v1 in Docker)

### 2.3 Critical Dependencies
**Python Dependencies** (from requirements.txt):
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- openai-whisper (requires torch, torchaudio)
- torch (CUDA-enabled version required)
- sqlalchemy==2.0.25
- langchain, langgraph (LLM enhancement)
- numpy, tiktoken, more-itertools
- aiofiles, python-multipart, pydantic, httpx

**System Dependencies**:
- CUDA 11.8+ (GPU acceleration)
- cuDNN (compatible with CUDA)
- FFmpeg (audio processing)
- Python 3.9+
- Node.js 18+ (frontend build)

**Frontend Dependencies** (from package.json):
- @angular/core: ^17.0.0
- rxjs: ~7.8.0
- TypeScript: ~5.2.2

### 2.4 Data Persistence Requirements (All in Volumes)
- **Database**: PostgreSQL data directory → `postgres-data` volume
  - Path in container: `/var/lib/postgresql/data`
  - Includes: Database files, WAL logs, configuration
- **Database Logs**: PostgreSQL logs → stored in data volume or stdout
- **Uploads**: Audio files → `whisper-uploads` volume
  - Path in container: `/app/uploads`
- **Model Cache**: Whisper models → `whisper-cache` volume
  - Path in container: `/root/.cache/whisper`

**Important**: NO data stored in container images - everything persists in volumes

---

## 3. Implementation Tasks - Detailed Breakdown

### PHASE 1: Preparation & Prerequisites

#### Task 1.1: Review and Update requirements.txt
**Impact**: Backend Dockerfile, PostgreSQL support
**Priority**: High

**Changes Required**:
1. Add explicit versions for all packages
2. Add PostgreSQL driver: `psycopg2-binary==2.9.9`
3. Remove duplicate `httpx` entry (appears twice at lines 30 and 40)
4. Group dependencies with comments
5. Pin torch, torchaudio, openai-whisper versions

**Files Modified**: `requirements.txt`

---

#### Task 1.2: Fix Frontend Production Environment
**Impact**: Frontend production build
**Priority**: High

**Issue**: `environment.prod.ts` points to port 8000 instead of 8001

**Change**:
```typescript
// Before
apiUrl: 'http://localhost:8000/api/v1'

// After
apiUrl: 'http://localhost:8001/api/v1'
```

**Files Modified**: `src/presentation/frontend/src/environments/environment.prod.ts`

---

#### Task 1.3: Update Database Configuration for PostgreSQL
**Impact**: Backend database layer
**Priority**: High

**File**: `src/infrastructure/persistence/database.py`

**Changes Required**:

```python
"""Database configuration and session management using SQLAlchemy"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from ..config.settings import get_settings

# Get settings
settings = get_settings()

# Create engine with PostgreSQL-optimized configuration
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    # PostgreSQL connection pool settings
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,         # Number of connections to maintain
    max_overflow=10      # Maximum additional connections
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Rest remains the same...
```

**Note**: Removes SQLite-specific `connect_args={"check_same_thread": False}` since we're PostgreSQL-only now.

**Files Modified**: `src/infrastructure/persistence/database.py`

**Testing**:
- Test with PostgreSQL: `DATABASE_URL=postgresql://whisper:password@postgres:5432/whisper_db`

---

### PHASE 2: Backend Docker Implementation

#### Task 2.1: Create Model Pre-Download Startup Script
**Impact**: Container startup, model caching
**Priority**: Critical

**File**: `scripts/docker/preload_models.py`

**Requirements**:
1. Check if models exist in cache volume (`/root/.cache/whisper/`)
2. Download only missing models
3. Support `--force` flag to override and re-download
4. Support `--models` flag to specify which models to download
5. Log progress clearly
6. Exit with appropriate status codes

**Implementation**: See full script in appendix

**Usage**:
```bash
# Download default model (base)
python preload_models.py

# Download specific models
python preload_models.py --models tiny base small

# Download all models
python preload_models.py --all

# Force re-download
python preload_models.py --models base --force
```

**Files Created**: `scripts/docker/preload_models.py`

---

#### Task 2.2: Create Backend Dockerfile
**Impact**: Backend container image
**Priority**: Critical

**File**: `Dockerfile`

**Multi-Stage Build Strategy**:
- Stage 1 (builder): Install dependencies and build packages
- Stage 2 (runtime): Minimal runtime with GPU support

**Key Features**:
- Base image: nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
- FFmpeg installation
- PyTorch with CUDA 11.8
- Smart entrypoint: Run model preload before starting app
- Environment variables: PRELOAD_MODELS, FORCE_DOWNLOAD

**Files Created**: `Dockerfile`

**Expected Image Size**: ~8-10 GB (CUDA + PyTorch + Whisper)

---

#### Task 2.3: Create Backend .dockerignore
**Impact**: Build performance, image size
**Priority**: Medium

**File**: `.dockerignore`

**Excludes**:
- Python: venv/, __pycache__/, *.pyc
- Environment: .env files
- Database: *.db files (should be in volume)
- Uploads: uploads/ (should be in volume)
- Frontend: node_modules/, dist/
- Git, IDE, logs, tests, documentation

**Files Created**: `.dockerignore`

---

### PHASE 3: Frontend Docker Implementation

#### Task 3.1: Create Frontend Dockerfile (ng serve)
**Impact**: Frontend container image
**Priority**: High

**File**: `src/presentation/frontend/Dockerfile`

**Simple Single-Stage Build**:
- Base image: node:18-alpine
- Install Angular CLI and dependencies
- Run `ng serve --host 0.0.0.0`
- Supports hot-reload when source is volume-mounted

**Dockerfile**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Install Angular CLI globally
RUN npm install -g @angular/cli

# Copy application code
COPY . .

# Expose Angular dev server port
EXPOSE 4200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:4200/ || exit 1

# Start Angular dev server
CMD ["ng", "serve", "--host", "0.0.0.0", "--poll", "1000"]
```

**Files Created**: `src/presentation/frontend/Dockerfile`

**Expected Image Size**: ~500 MB (includes Node.js + Angular CLI + dependencies)

**Note**: No Nginx needed - ng serve handles everything

---

#### Task 3.2: Create Frontend .dockerignore
**Impact**: Build performance
**Priority**: Low

**File**: `src/presentation/frontend/.dockerignore`

**Content**:
```
node_modules/
dist/
.angular/
coverage/
.git/
*.md
.editorconfig
.gitignore
e2e/
.vscode/
.idea/
*.log
```

**Files Created**: `src/presentation/frontend/.dockerignore`

---

### PHASE 4: Docker Compose Orchestration

#### Task 4.1: Create Production docker-compose.yml
**Impact**: Production deployment orchestration
**Priority**: Critical

**File**: `docker-compose.yml`

**Services**:
1. **postgres**: PostgreSQL 15 database
   - Data volume: `postgres-data` → `/var/lib/postgresql/data`
   - Logs: Stored in data volume or output to stdout
   - No data in image
2. **backend**: FastAPI with GPU support
   - Volumes: uploads, model cache
3. **frontend**: Angular with ng serve
   - Port: 4200 (exposed)
   - No Nginx, just ng serve

**Features**:
- GPU passthrough for backend
- Health checks for all services
- **Named volumes for ALL data persistence** (database, uploads, models)
- Environment variable configuration
- Service dependencies
- Restart policies

**PostgreSQL Volume Configuration**:
```yaml
postgres:
  image: postgres:15-alpine
  volumes:
    - postgres-data:/var/lib/postgresql/data  # Data + logs
  environment:
    - POSTGRES_USER=whisper
    - POSTGRES_PASSWORD=secure_password
    - POSTGRES_DB=whisper_db
```

**Files Created**: `docker-compose.yml`

---

#### Task 4.2: Create Development docker-compose.dev.yml
**Impact**: Development workflow
**Priority**: High

**File**: `docker-compose.dev.yml`

**Features**:
- PostgreSQL database (same as production, consistent environment)
- Source code volume mounts for hot-reload (both frontend and backend)
- Smaller model set (tiny, base) for faster testing
- Debug mode enabled
- Separate PostgreSQL instance/database for development

**Key Differences from Production**:
- Frontend: Source code mounted for hot-reload
- Backend: Source code mounted for hot-reload
- Database: Separate database name (whisper_dev_db vs whisper_db)
- Models: Only download tiny + base (faster startup)

**Files Created**: `docker-compose.dev.yml`

**Note**: No separate frontend Dockerfile needed - same Dockerfile works for both, just with volume mounts in dev

---

#### Task 4.4: Create .env.docker Example
**Impact**: Configuration documentation
**Priority**: Medium

**File**: `.env.docker`

**Content**:
- PostgreSQL configuration
- Model preload settings
- Application settings
- API configuration
- Whisper settings
- Upload settings
- CORS settings
- LLM settings
- Docker-specific notes

**Files Created**: `.env.docker`

---

### PHASE 5: Docker Management Scripts

Create Python scripts under `scripts/docker/`:

1. **build.py**: Build Docker images
2. **run.py**: Run containers using docker-compose
3. **stop.py**: Stop running containers
4. **logs.py**: View container logs
5. **shell.py**: Open shell in running container
6. **clean.py**: Clean up Docker resources
7. **rebuild.py**: Rebuild and restart

**Files Created**: 7 Docker management scripts + `__init__.py`

---

### PHASE 6: Testing & Validation

#### Task 6.1: Backend Build Testing
- Build completes without errors
- Image size < 12GB
- CUDA libraries present
- FFmpeg installed
- Python packages installed

#### Task 6.2: Frontend Build Testing
- Build completes without errors
- Image size < 1GB (includes Node.js + Angular CLI)
- ng serve starts successfully
- Port 4200 accessible

#### Task 6.3: Production Compose Testing
- All services start successfully
- GPU accessible in backend
- PostgreSQL healthy
- Model pre-download completes
- Upload and transcription works
- Data persists across restarts

#### Task 6.4: Development Compose Testing
- Services start with PostgreSQL
- Frontend on port 4200 with hot-reload
- Backend hot-reload works
- Development database isolated from production

#### Task 6.5: Database Persistence Testing
- PostgreSQL data persists across container restarts
- PostgreSQL data persists across image rebuilds
- Database backups and restores work correctly

---

### PHASE 7: Documentation

#### Task 7.1: Update README.md
Add section: "Docker Deployment"

**Content**:
- Prerequisites (Docker, Docker Compose, nvidia-docker)
- Quick start with Docker
- Production deployment
- Development deployment
- Environment configuration
- Volume management
- Troubleshooting

**Files Modified**: `README.md`

---

#### Task 7.2: Update CLAUDE.md
Add section: "Docker Configuration"

**Content**:
- Docker architecture overview
- Dockerfile design decisions
- docker-compose.yml structure
- Model caching strategy
- PostgreSQL integration
- Development workflow
- Common issues

**Files Modified**: `CLAUDE.md`

---

#### Task 7.3: Create DOCKER.md
**File**: `DOCKER.md`

**Content**:
- Comprehensive deployment guide
- Architecture diagrams
- Prerequisites installation
- Step-by-step setup
- Configuration reference
- Model management
- Database management
- Troubleshooting
- Security best practices
- Performance tuning

**Files Created**: `DOCKER.md`

---

## 4. PostgreSQL Integration Details

### 4.1 Code Changes Required

**File**: `src/infrastructure/persistence/database.py`

**Changes**:
1. Remove SQLite-specific `connect_args={"check_same_thread": False}`
2. Add PostgreSQL connection pooling (pool_size, max_overflow)
3. Add `pool_pre_ping` for connection health checks
4. Simplify engine creation (no conditional logic needed)

**Analysis**:
- Current models (TranscriptionModel, AudioFileModel) are already database-agnostic
- Using standard SQLAlchemy types that work across databases
- No changes needed to models or repositories
- Only database.py needs updating

**Testing**: PostgreSQL only

---

### 4.2 Migration Strategy from Existing SQLite Data (Optional)

**For users migrating from existing SQLite deployments**:

1. Export existing SQLite data:
   ```bash
   sqlite3 whisper_transcriptions.db .dump > backup.sql
   ```

2. Convert to PostgreSQL-compatible SQL (manual editing):
   - Remove SQLite-specific syntax
   - Adjust data types if needed

3. Import to PostgreSQL:
   ```bash
   psql -U whisper -d whisper_db -f backup.sql
   ```

**Note**: For fresh Docker deployments, no migration needed.

---

### 4.3 Connection String Examples

**Development** (Docker Compose):
```
DATABASE_URL=postgresql://whisper_dev:dev_password@postgres:5432/whisper_dev_db
```

**Production** (Docker Compose):
```
DATABASE_URL=postgresql://whisper:secure_password@postgres:5432/whisper_db
```

---

## 5. Model Caching Architecture

### 5.1 Flow Diagram

```
Container Startup
       ↓
Run preload_models.py
       ↓
Check /root/.cache/whisper/ (VOLUME)
       ↓
   ┌───────────────────┐
   │ Models exist?     │
   └────┬──────────┬───┘
        │ Yes      │ No
        ↓          ↓
    Skip      Download
        ↓          ↓
        └──────────┘
             ↓
    Start FastAPI
```

### 5.2 Volume Persistence

**Volume Name**: `whisper-cache`
**Mount Point**: `/root/.cache/whisper`
**Contents**: `{model}.pt` files (e.g., `base.pt`, `small.pt`)

**Behavior**:
- First run: Downloads models (5-30 minutes depending on model size)
- Subsequent runs: Uses cached models (instant startup)
- Rebuild image: Models persist (in volume, not lost)
- Force re-download: `FORCE_DOWNLOAD=1` in environment

---

## 6. Success Criteria

### 6.1 Build Success
- ✅ Backend Docker image builds without errors
- ✅ Backend image size < 12GB (CUDA + PyTorch + Whisper)
- ✅ Frontend Docker image builds without errors
- ✅ Frontend image size < 1GB (Node.js + Angular CLI)
- ✅ docker-compose up starts all services successfully
- ✅ No critical vulnerabilities in images

### 6.2 Functional Success
- ✅ GPU is accessible and functional in backend container
- ✅ Upload audio file works through Docker deployment
- ✅ Transcription completes successfully
- ✅ PostgreSQL integration works (all environments)
- ✅ **PostgreSQL data persists in volume** (not in image)
- ✅ **PostgreSQL logs accessible** (in volume or stdout)
- ✅ Database persists across container restarts
- ✅ Database persists across image rebuilds
- ✅ Uploaded files persist in volume across restarts
- ✅ Whisper models cached in volume and reused
- ✅ Model pre-download script works correctly
- ✅ Frontend hot-reload works (ng serve)
- ✅ Backend hot-reload works (uvicorn --reload)
- ✅ Development and production databases are isolated
- ✅ **No data stored in container images**

### 6.3 Performance Success
- ✅ Transcription performance comparable to non-Docker deployment
- ✅ Container startup time < 90 seconds (with cached models)
- ✅ Container startup time < 10 minutes (first time, downloading models)
- ✅ Memory usage within acceptable limits
- ✅ GPU utilization matches non-Docker usage

### 6.4 Documentation Success
- ✅ README.md includes clear Docker instructions
- ✅ CLAUDE.md documents Docker architecture and patterns
- ✅ DOCKER.md provides comprehensive deployment guide
- ✅ All scripts are documented with usage examples

---

## 7. Potential Issues and Mitigations

### Issue 7.1: CUDA Version Mismatch
**Problem**: Host GPU driver incompatible with container CUDA version
**Mitigation**:
- Document CUDA compatibility matrix
- Test on target hardware early
- Provide alternative Dockerfiles for different CUDA versions

### Issue 7.2: FFmpeg Missing Codecs
**Problem**: FFmpeg in container missing required audio codecs
**Mitigation**:
- Install full FFmpeg package
- Test with various audio formats during validation

### Issue 7.3: Whisper Model Download Timeouts
**Problem**: Large models timeout during download
**Mitigation**:
- Increase timeout in preload script
- Support resume/retry logic
- Document expected download times

### Issue 7.4: Frontend Cannot Reach Backend
**Problem**: API URL configuration issues
**Mitigation**:
- Use Docker network for backend-frontend communication
- Configure environment.ts with correct backend URL
- Document URL configuration options

### Issue 7.5: PostgreSQL Connection Issues
**Problem**: Backend cannot connect to PostgreSQL
**Mitigation**:
- Add health checks and wait-for-db logic
- Configure connection pooling
- Document troubleshooting steps

### Issue 7.6: Volume Permission Issues
**Problem**: Container cannot write to volumes
**Mitigation**:
- Use named volumes (Docker manages permissions)
- Document proper volume setup
- Avoid bind mounts for data storage

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CUDA compatibility issues | Medium | High | Test on target hardware early, document requirements |
| Image size too large | High | Medium | Multi-stage builds, clean up build artifacts |
| Performance degradation | Low | High | Benchmark early, optimize if needed |
| Volume permission issues | Medium | Medium | Document proper setup, use named volumes |
| Network configuration issues | Low | Medium | Test thoroughly, provide troubleshooting guide |
| PostgreSQL migration complexity | Medium | Medium | Provide clear migration guide, test both databases |
| Model download failures | Medium | High | Implement retry logic, increase timeouts |

---

## 9. Implementation Timeline

**Total Estimated Time**: ~14 hours

| Phase | Tasks | Time |
|-------|-------|------|
| Phase 1: Preparation | 3 tasks | 2 hours |
| Phase 2: Backend Docker | 3 tasks | 3 hours |
| Phase 3: Frontend Docker | 3 tasks | 2 hours |
| Phase 4: Docker Compose | 4 tasks | 2 hours |
| Phase 5: Scripts | 7 scripts | 2 hours |
| Phase 6: Testing | 5 test scenarios | 2 hours |
| Phase 7: Documentation | 3 documents | 1 hour |

---

## 10. File Structure After Implementation

```
Whisper/
├── Dockerfile                          # Backend Dockerfile (NEW)
├── .dockerignore                       # Backend Docker ignore (NEW)
├── docker-compose.yml                  # Production compose (NEW)
├── docker-compose.dev.yml             # Development compose (NEW)
├── .env.docker                        # Docker env example (NEW)
├── DOCKER.md                          # Docker documentation (NEW)
│
├── src/
│   ├── infrastructure/
│   │   └── persistence/
│   │       └── database.py            # MODIFIED: PostgreSQL-only config
│   │
│   └── presentation/
│       └── frontend/
│           ├── Dockerfile             # Frontend ng serve (NEW)
│           ├── .dockerignore          # Frontend ignore (NEW)
│           └── src/environments/
│               └── environment.prod.ts # MODIFIED: port 8001
│
├── scripts/
│   └── docker/                        # Docker management scripts (NEW)
│       ├── __init__.py
│       ├── preload_models.py         # CRITICAL: model caching
│       ├── build.py
│       ├── run.py
│       ├── stop.py
│       ├── logs.py
│       ├── shell.py
│       ├── clean.py
│       └── rebuild.py
│
├── plans/
│   └── DOCKER_IMPLEMENTATION_PLAN.md  # This file
│
├── requirements.txt                   # MODIFIED: Add PostgreSQL driver
├── README.md                          # MODIFIED: Docker section
└── CLAUDE.md                          # MODIFIED: Docker architecture
```

**Summary**:
- **NEW**: 16 files (removed: nginx.conf, Dockerfile.dev)
- **MODIFIED**: 4 files
- **Total Changes**: 20 files

**Volume Persistence**:
- `postgres-data`: PostgreSQL database files + logs
- `whisper-uploads`: Uploaded audio files
- `whisper-cache`: Whisper model files
- **All data in volumes, nothing in images**

---

## 11. Next Steps

1. ✅ **User Approval**: Confirm this plan
2. **Create Git Branch**: `feature/docker-implementation`
3. **Start Implementation**: Phase 1 → Phase 7 sequentially
4. **Test Thoroughly**: Each phase before proceeding
5. **Document Issues**: Track any problems encountered
6. **Final Review**: Complete testing on clean environment
7. **Merge to Main**: After successful testing

---

## Appendix A: Model Pre-Download Script (Complete)

```python
#!/usr/bin/env python3
"""
Whisper Model Pre-Download Script for Docker

Downloads Whisper models to cache volume on container startup.
Smart caching: Only downloads missing models unless --force is used.
"""
import argparse
import os
import sys
from pathlib import Path
import whisper

# Available Whisper models
AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]
DEFAULT_MODELS = ["base"]  # Default model to pre-download

# Cache directory (will be volume-mounted in Docker)
CACHE_DIR = Path.home() / ".cache" / "whisper"


def model_exists(model_name: str) -> bool:
    """Check if a Whisper model exists in cache."""
    model_file = CACHE_DIR / f"{model_name}.pt"
    exists = model_file.exists()

    if exists:
        file_size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"✓ Model '{model_name}' found in cache ({file_size_mb:.1f} MB)")
    else:
        print(f"✗ Model '{model_name}' not found in cache")

    return exists


def download_model(model_name: str, force: bool = False) -> bool:
    """Download a Whisper model if missing or force is True."""
    if not force and model_exists(model_name):
        print(f"⊳ Skipping '{model_name}' (already cached, use --force to re-download)")
        return True

    try:
        print(f"⬇ Downloading model '{model_name}'...")
        whisper.load_model(model_name, download_root=str(CACHE_DIR))
        print(f"✓ Successfully downloaded '{model_name}'")
        return True
    except Exception as e:
        print(f"✗ Failed to download '{model_name}': {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Pre-download Whisper models to cache volume"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=AVAILABLE_MODELS,
        default=DEFAULT_MODELS,
        help=f"Models to download (default: {DEFAULT_MODELS})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if models exist in cache"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available models"
    )

    args = parser.parse_args()

    # Determine which models to download
    models_to_download = AVAILABLE_MODELS if args.all else args.models

    print("=" * 60)
    print("Whisper Model Pre-Download Script")
    print("=" * 60)
    print(f"Cache directory: {CACHE_DIR}")
    print(f"Models to process: {', '.join(models_to_download)}")
    print(f"Force re-download: {args.force}")
    print("=" * 60)
    print()

    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Download models
    success_count = 0
    failure_count = 0

    for model in models_to_download:
        if download_model(model, force=args.force):
            success_count += 1
        else:
            failure_count += 1
        print()  # Blank line between models

    # Summary
    print("=" * 60)
    print(f"Summary: {success_count} successful, {failure_count} failed")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(1 if failure_count > 0 else 0)


if __name__ == "__main__":
    main()
```

---

## Appendix B: Example Docker Commands

### Build
```bash
# Production build
docker-compose build

# Development build
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# Build specific service
docker-compose build backend

# Build with no cache
docker-compose build --no-cache
```

### Run
```bash
# Production (detached)
docker-compose up -d

# Production (with logs)
docker-compose up

# Development (with logs)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Rebuild and run
docker-compose up --build
```

### Manage
```bash
# Stop services
docker-compose down

# Stop and remove volumes (DELETE DATA!)
docker-compose down -v

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend

# Shell into backend
docker exec -it whisper-backend bash

# Shell into frontend
docker exec -it whisper-frontend sh

# Check GPU in backend
docker exec whisper-backend nvidia-smi

# Check GPU availability
docker exec whisper-backend python3 -c "import torch; print(torch.cuda.is_available())"
```

### Model Management
```bash
# Pre-download specific models
docker exec whisper-backend python3 /usr/local/bin/preload_models.py --models tiny base

# Force re-download
docker exec whisper-backend python3 /usr/local/bin/preload_models.py --models base --force

# Download all models
docker exec whisper-backend python3 /usr/local/bin/preload_models.py --all
```

### Volume Management
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect whisper_whisper-cache

# Backup database volume
docker run --rm -v whisper_postgres-data:/data -v $(pwd):/backup ubuntu tar czf /backup/db-backup.tar.gz /data

# Restore database volume
docker run --rm -v whisper_postgres-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/db-backup.tar.gz -C /
```

---

**Plan Status**: ✅ Ready for Implementation
**User Approval**: REQUIRED
**Version**: 2.0
**Last Updated**: 2025-12-31
