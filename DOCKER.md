# Docker Deployment Guide

Complete guide for deploying the Whisper transcription system using Docker and Docker Compose.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Environment Configuration](#environment-configuration)
- [Management Scripts](#management-scripts)
- [Ngrok Tunnels](#ngrok-tunnels)
- [Volume Management](#volume-management)
- [GPU Configuration](#gpu-configuration)
- [Hot-Reload Development](#hot-reload-development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Overview

The Docker deployment provides a complete containerized solution with:

- **PostgreSQL Database**: Persistent storage for transcriptions and audio metadata
- **FastAPI Backend**: GPU-accelerated faster-whisper transcription with CUDA 12.8
- **Angular Frontend**: Modern web interface with ng serve
- **Hot-Reload Development**: Source code changes without container rebuild
- **Volume Persistence**: All data stored in Docker volumes
- **Smart Model Caching**: Automatic Whisper model download and caching

## Prerequisites

### Required Software

1. **Docker Engine 20.10+**
   - Linux: `sudo apt install docker.io docker-compose`
   - Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **NVIDIA Container Toolkit** (for GPU support)

   **Note**: The legacy `nvidia-docker` wrapper has been deprecated. Use NVIDIA Container Toolkit instead.

   ```bash
   # Ubuntu/Debian - Install NVIDIA Container Toolkit
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
     && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
       sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
       sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit

   # Configure Docker to use NVIDIA runtime
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

   **Alternative installation (using apt repository)**:
   ```bash
   # Add NVIDIA package repositories
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
      && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
      && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

   Windows/macOS with Docker Desktop: GPU support included, no additional installation needed

3. **Verify GPU Access**
   ```bash
   # Verify NVIDIA Container Toolkit installation
   nvidia-ctk --version

   # Test GPU access in Docker
   docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi

   # Should display your GPU information
   ```

   **Expected output**:
   ```
   +-----------------------------------------------------------------------------+
   | NVIDIA-SMI 535.54.03    Driver Version: 535.54.03    CUDA Version: 12.2     |
   |-------------------------------+----------------------+----------------------+
   | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
   | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
   |                               |                      |               MIG M. |
   |===============================+======================+======================|
   |   0  NVIDIA GeForce ... Off  | 00000000:01:00.0  On |                  N/A |
   ```

### System Requirements

- **Disk Space**: 20GB+ free
  - Docker images: ~8GB (backend), ~1GB (frontend), ~200MB (postgres)
  - Whisper models: ~1-3GB per model
  - Audio uploads: Varies by usage

- **RAM**: 8GB minimum, 16GB recommended

- **GPU**: NVIDIA GPU with CUDA 12.8+ support
  - Minimum: GTX 1060 (6GB VRAM)
  - Recommended: RTX 3060+ (12GB VRAM)
  - For production: RTX 4090 or A100
  - **RTX 5090 (Blackwell)**: Requires CUDA 12.8+ and PyTorch 2.9.0+ (sm_120 architecture)

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/anashammo/whisper-ui.git
cd whisper-ui
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.docker .env

# Edit .env with your preferred editor
nano .env
```

**CRITICAL**: Change `POSTGRES_PASSWORD` from default:

```bash
POSTGRES_PASSWORD=your_secure_random_password_here
```

### 3. Build and Run

```bash
# Build images and start all services
python scripts/docker/run.py --build

# Wait for services to be healthy (30-60 seconds)
# Backend will download Whisper models on first run
```

### 4. Access Application

- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/v1/health

### 5. Verify GPU Access

```bash
# Open shell in backend container
python scripts/docker/shell.py backend

# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

# Should print:
# CUDA available: True
# GPU: NVIDIA GeForce RTX 5090 (or your GPU model)
```

## Architecture

### Service Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Docker Host                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Frontend   │  │   Backend    │  │  PostgreSQL  │     │
│  │              │  │              │  │              │     │
│  │  Angular 17  │  │  FastAPI     │  │  Postgres 15 │     │
│  │  ng serve    │  │  Whisper AI  │  │              │     │
│  │  Port 4200   │  │  CUDA 12.8   │  │  Port 5432   │     │
│  │              │  │  Port 8001   │  │  (internal)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         │                 │                 │              │
│  ┌──────▼─────────────────▼─────────────────▼───────┐     │
│  │              Docker Volumes                      │     │
│  ├──────────────────────────────────────────────────┤     │
│  │  • postgres-data (PostgreSQL database + logs)   │     │
│  │  • whisper-uploads (Audio files)                │     │
│  │  • huggingface-cache (Whisper models ~1-3GB each)   │     │
│  │  • Source code (read-only, hot-reload)          │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │           NVIDIA GPU (passed through)            │     │
│  │           Used by: backend container             │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Service Details

#### PostgreSQL Service (`postgres`)

- **Image**: `postgres:15-alpine` (lightweight PostgreSQL)
- **Port**: 5432 (internal only, not exposed to host)
- **Volume**: `postgres-data` → `/var/lib/postgresql/data`
- **Health Check**: `pg_isready -U whisper`
- **Purpose**: Persistent storage for transcriptions and audio metadata

#### Backend Service (`backend`)

- **Base Image**: `nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04`
- **Port**: 8001 (exposed to host)
- **GPU**: NVIDIA GPU passed through via `nvidia` runtime
- **Volumes**:
  - `whisper-uploads` → `/app/uploads` (user audio files)
  - `huggingface-cache` → `/root/.cache/huggingface` (model cache)
  - `./src` → `/app/src:ro` (source code, read-only, hot-reload)
  - `./scripts` → `/app/scripts:ro` (utility scripts)
- **Environment**: PostgreSQL connection, model preload settings
- **Health Check**: HTTP GET `http://localhost:8001/api/v1/health`
- **Startup**:
  1. Preload Whisper models (via `preload_models.py`)
  2. Start Uvicorn with `--reload` flag
- **Dependencies**: Waits for PostgreSQL to be healthy

#### Frontend Service (`frontend`)

- **Base Image**: `node:18-alpine`
- **Port**: 4200 (exposed to host)
- **Volumes**:
  - `./src/presentation/frontend/src` → `/app/src:ro` (source code, hot-reload)
  - `./src/presentation/frontend/angular.json` → `/app/angular.json:ro`
- **Command**: `ng serve --host 0.0.0.0 --poll 1000`
- **Health Check**: HTTP GET `http://localhost:4200`
- **Dependencies**: Waits for backend to be healthy

### Network

All services connected via Docker bridge network:

- **Frontend** → **Backend**: `http://backend:8001/api/v1`
- **Backend** → **PostgreSQL**: `postgresql://whisper:password@postgres:5432/whisper_db`
- **Host** → **Frontend**: `http://localhost:4200`
- **Host** → **Backend**: `http://localhost:8001`

## Environment Configuration

### .env File Structure

```bash
# ============================================================================
# PostgreSQL Database Configuration
# ============================================================================
POSTGRES_USER=whisper                                    # Database username
POSTGRES_PASSWORD=change_this_secure_password_in_production  # Database password (CHANGE THIS!)
POSTGRES_DB=whisper_db                                  # Database name

# ============================================================================
# Whisper Model Configuration
# ============================================================================
# Models to download on container startup (comma-separated)
# Options: tiny, base, small, medium, large, turbo
PRELOAD_MODELS=base

# Force re-download models even if cached (set to "true" to enable)
FORCE_DOWNLOAD=

# ============================================================================
# Port Configuration
# ============================================================================
BACKEND_PORT=8001                                        # Backend API port
FRONTEND_PORT=4200                                       # Frontend dev server port

# ============================================================================
# LLM Enhancement Configuration (Optional)
# ============================================================================
LLM_BASE_URL=http://host.docker.internal:11434/v1       # Ollama/LM Studio URL
LLM_MODEL=llama3                                         # LLM model name
LLM_TIMEOUT_SECONDS=60                                   # LLM request timeout
LLM_TEMPERATURE=0.3                                      # LLM temperature (0.0-1.0)
```

### Model Preloading

**PRELOAD_MODELS** determines which Whisper models are downloaded on container startup:

```bash
# Download single model
PRELOAD_MODELS=base

# Download multiple models (comma-separated, no spaces)
PRELOAD_MODELS=tiny,base,small

# Download all models (WARNING: ~10GB total)
PRELOAD_MODELS=tiny,base,small,medium,large,turbo

# Skip download (not recommended - first transcription will be slow)
PRELOAD_MODELS=
```

**FORCE_DOWNLOAD** forces re-download even if models exist in cache:

```bash
# Normal operation (skip if cached)
FORCE_DOWNLOAD=

# Force re-download (useful if cache corrupted)
FORCE_DOWNLOAD=true
```

**Model download happens**:
- On container first run (if models not in volume)
- On every rebuild if `FORCE_DOWNLOAD=true`
- Models cached in `huggingface-cache` volume persist across rebuilds

### Port Customization

Change ports if defaults conflict with existing services:

```bash
# Use custom ports
BACKEND_PORT=8080
FRONTEND_PORT=3000
```

Then access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8080

## Management Scripts

All Docker operations via Python scripts in `scripts/docker/`:

### Build Scripts

#### build.py - Build Docker Images

```bash
# Build all services
python scripts/docker/build.py

# Build specific service
python scripts/docker/build.py --backend
python scripts/docker/build.py --frontend

# Clean build (no cache)
python scripts/docker/build.py --no-cache

# Build specific service with no cache
python scripts/docker/build.py --backend --no-cache
```

**Options**:
- `--backend`: Build backend only
- `--frontend`: Build frontend only
- `--no-cache`: Build from scratch (ignores Docker cache)

**Use Cases**:
- Initial setup: `python scripts/docker/build.py`
- After dependency changes: `python scripts/docker/build.py --backend --no-cache`
- After Angular config changes: `python scripts/docker/build.py --frontend`

### Runtime Scripts

#### run.py - Start Services

```bash
# Start core services (postgres, backend, frontend)
python scripts/docker/run.py

# Build and start
python scripts/docker/run.py --build

# Run in background (detached mode)
python scripts/docker/run.py --detach

# Build and run in background
python scripts/docker/run.py --build --detach

# Start with ngrok tunnels (requires NGROK_AUTHTOKEN in .env)
python scripts/docker/run.py --ngrok

# Build and start with ngrok tunnels
python scripts/docker/run.py --build --ngrok --detach
```

**Options**:
- `--build`: Build images before starting
- `--detach`: Run in background
- `--ngrok`: Include ngrok tunnel services (requires NGROK_AUTHTOKEN)

**Behavior**:
- Starts core services defined in `docker-compose.yml`
- With `--ngrok`, also starts ngrok tunnel services via Docker profiles
- Creates volumes if they don't exist
- Waits for health checks to pass
- Streams logs to console (unless `--detach`)

#### stop.py - Stop Services

```bash
# Stop all containers (keep volumes)
python scripts/docker/stop.py

# Stop containers and remove volumes (WARNING: deletes all data)
python scripts/docker/stop.py --remove-volumes
python scripts/docker/stop.py -v

# Stop only ngrok tunnel services (keep core services running)
python scripts/docker/stop.py --ngrok-only
```

**Options**:
- `-v, --remove-volumes`: Remove volumes (deletes database, uploads, models)
- `--ngrok-only`: Stop only ngrok tunnel services

**Confirmation Required**:
- Asks for confirmation before removing volumes
- Enter `yes` to confirm, anything else cancels

#### rebuild.py - Rebuild and Restart

```bash
# Stop, rebuild, and restart core services
python scripts/docker/rebuild.py

# Stop, rebuild, and restart with ngrok tunnels
python scripts/docker/rebuild.py --ngrok
```

**Options**:
- `--ngrok`: Include ngrok tunnel services after rebuild

**Workflow**:
1. Stops all containers
2. Rebuilds images
3. Starts containers (with ngrok if `--ngrok` flag used)
4. Exits with success/failure status

**Equivalent to**:
```bash
python scripts/docker/stop.py
python scripts/docker/build.py
python scripts/docker/run.py           # or run.py --ngrok
```

### Debugging Scripts

#### logs.py - View Logs

```bash
# View core service logs
python scripts/docker/logs.py

# View all logs including ngrok
python scripts/docker/logs.py --ngrok

# View specific service logs
python scripts/docker/logs.py backend
python scripts/docker/logs.py frontend
python scripts/docker/logs.py postgres
python scripts/docker/logs.py ngrok-whisper-backend
python scripts/docker/logs.py ngrok-whisper-frontend
python scripts/docker/logs.py ngrok-whisper-llm

# Follow logs (live stream)
python scripts/docker/logs.py --follow
python scripts/docker/logs.py -f

# Last N lines
python scripts/docker/logs.py --tail 100
python scripts/docker/logs.py backend --tail 50

# Combine options
python scripts/docker/logs.py backend --follow --tail 100
python scripts/docker/logs.py --ngrok -f --tail 100
```

**Options**:
- `service`: Service name (backend, frontend, postgres, ngrok-whisper-backend, ngrok-whisper-frontend, ngrok-whisper-llm)
- `-f, --follow`: Follow log output (live stream)
- `--tail N`: Show last N lines
- `--ngrok`: Include ngrok services in logs

**Use Cases**:
- Check startup: `python scripts/docker/logs.py backend --tail 50`
- Debug issues: `python scripts/docker/logs.py backend --follow`
- Monitor all: `python scripts/docker/logs.py --follow`
- Monitor with ngrok: `python scripts/docker/logs.py --ngrok -f`

#### shell.py - Open Container Shell

```bash
# Open bash in backend container
python scripts/docker/shell.py backend

# Open sh in frontend container
python scripts/docker/shell.py frontend

# Open sh in PostgreSQL container
python scripts/docker/shell.py postgres
```

**Available Shells**:
- `backend`: bash (Ubuntu-based)
- `frontend`: sh (Alpine-based)
- `postgres`: sh (Alpine-based)

**Common Uses**:

Backend shell:
```bash
python scripts/docker/shell.py backend

# Inside container:
python -c "import torch; print(torch.cuda.is_available())"  # Check GPU
python scripts/setup/download_whisper_model.py medium       # Download model
ls -lh /root/.cache/huggingface/                             # Check cached models
ls -lh /app/uploads/                                         # Check uploads
```

Frontend shell:
```bash
python scripts/docker/shell.py frontend

# Inside container:
ng version                                                   # Check Angular version
ls -lh /app/src/                                             # Check source code
```

PostgreSQL shell:
```bash
python scripts/docker/shell.py postgres

# Inside container:
psql -U whisper -d whisper_db                                # Connect to database
\dt                                                           # List tables
SELECT COUNT(*) FROM transcriptions;                          # Query data
```

### Cleanup Scripts

#### clean.py - Remove Docker Resources

```bash
# Remove containers only (keeps images and volumes)
python scripts/docker/clean.py

# Remove images only
python scripts/docker/clean.py --images

# Remove volumes only (WARNING: deletes all data)
python scripts/docker/clean.py --volumes

# Remove everything (WARNING: deletes all data and images)
python scripts/docker/clean.py --all
```

**Options**:
- `--images`: Remove Docker images
- `--volumes`: Remove Docker volumes (requires confirmation)
- `--all`: Remove containers, images, and volumes (requires confirmation)

**Confirmation Required**:
- `--volumes`: Asks for confirmation
- `--all`: Asks for confirmation

**Use Cases**:
- Free disk space: `python scripts/docker/clean.py --images`
- Complete reset: `python scripts/docker/clean.py --all` (then rebuild from scratch)
- Remove old data: `python scripts/docker/clean.py --volumes`

## Ngrok Tunnels

Ngrok tunnels provide external access to your local Docker services via public URLs. These are optional and controlled via Docker Compose profiles.

### Overview

Three ngrok tunnel services are available:

| Service | Target | Public URL | Web UI |
|---------|--------|------------|--------|
| `ngrok-whisper-backend` | Backend API (port 8001) | https://anas-hammo-whisper-backend.ngrok.dev | http://localhost:4050 |
| `ngrok-whisper-frontend` | Frontend (port 4200) | https://anas-hammo-whisper-frontend.ngrok.dev | http://localhost:4051 |
| `ngrok-whisper-llm` | LLM service (port 1234) | https://anas-hammo-whisper-llm.ngrok.dev | http://localhost:4052 |

### Configuration

1. **Get your ngrok auth token** from https://dashboard.ngrok.com/get-started/your-authtoken

2. **Add to your `.env` file**:
   ```bash
   NGROK_AUTHTOKEN=your_token_here
   ```

3. **Reserved domains**: The tunnel URLs require ngrok reserved domains configured in your ngrok account.

### Usage

```bash
# Start core services + ngrok tunnels
python scripts/docker/run.py --ngrok

# Build and start with ngrok
python scripts/docker/run.py --build --ngrok --detach

# Rebuild with ngrok tunnels
python scripts/docker/rebuild.py --ngrok

# Stop only ngrok (keep core services running)
python scripts/docker/stop.py --ngrok-only

# View ngrok logs
python scripts/docker/logs.py ngrok-whisper-backend -f
python scripts/docker/logs.py --ngrok -f
```

### Docker Profiles

Ngrok services use Docker Compose profiles (`profiles: - ngrok`). This means:

- **Default**: Ngrok services are NOT started with regular `docker-compose up`
- **With profile**: Use `docker-compose --profile ngrok up` to include them
- **Scripts**: The `--ngrok` flag in Python scripts handles this automatically

### Web Inspection UI

Each ngrok tunnel exposes a web inspection UI for debugging HTTP requests:

- **Backend inspector**: http://localhost:4050
- **Frontend inspector**: http://localhost:4051
- **LLM inspector**: http://localhost:4052

These UIs show:
- All HTTP requests/responses
- Request headers and body
- Response timing
- Replay functionality for debugging

### Dependencies

- `ngrok-whisper-backend`: Waits for backend to be healthy before starting
- `ngrok-whisper-frontend`: Waits for frontend to be healthy before starting
- `ngrok-whisper-llm`: Starts immediately (LLM runs on host, not in Docker)

## Volume Management

### Volume Overview

All persistent data stored in Docker named volumes:

| Volume Name | Mount Point | Purpose | Size |
|------------|-------------|---------|------|
| `postgres-data` | `/var/lib/postgresql/data` | PostgreSQL database + logs | ~100MB-10GB |
| `whisper-uploads` | `/app/uploads` | User audio files | Varies |
| `huggingface-cache` | `/root/.cache/huggingface` | Whisper models | ~1-3GB per model |

### Volume Inspection

```bash
# List all volumes
docker volume ls

# Inspect specific volume
docker volume inspect postgres-data
docker volume inspect whisper-uploads
docker volume inspect huggingface-cache

# Check volume disk usage
docker system df -v
```

### Volume Backup

#### Backup PostgreSQL Database

```bash
# Create backup
docker exec whisper-postgres pg_dump -U whisper whisper_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
cat backup_20250101_120000.sql | docker exec -i whisper-postgres psql -U whisper -d whisper_db
```

#### Backup Uploads

```bash
# Create tar archive of uploads
docker run --rm -v whisper-uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup.tar.gz -C /data .

# Restore uploads
docker run --rm -v whisper-uploads:/data -v $(pwd):/backup alpine tar xzf /backup/uploads_backup.tar.gz -C /data
```

#### Backup Models

```bash
# Create tar archive of models
docker run --rm -v huggingface-cache:/data -v $(pwd):/backup alpine tar czf /backup/models_backup.tar.gz -C /data .

# Restore models
docker run --rm -v huggingface-cache:/data -v $(pwd):/backup alpine tar xzf /backup/models_backup.tar.gz -C /data
```

### Volume Migration

Move volumes to new Docker host:

```bash
# On source host: Export volumes
docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres.tar.gz -C /data .
docker run --rm -v whisper-uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads.tar.gz -C /data .
docker run --rm -v huggingface-cache:/data -v $(pwd):/backup alpine tar czf /backup/cache.tar.gz -C /data .

# Transfer files to new host
scp *.tar.gz user@newhost:/path/to/whisper/

# On destination host: Import volumes
docker volume create postgres-data
docker volume create whisper-uploads
docker volume create huggingface-cache

docker run --rm -v postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres.tar.gz -C /data
docker run --rm -v whisper-uploads:/data -v $(pwd):/backup alpine tar xzf /backup/uploads.tar.gz -C /data
docker run --rm -v huggingface-cache:/data -v $(pwd):/backup alpine tar xzf /backup/cache.tar.gz -C /data
```

### Volume Pruning

Remove unused volumes:

```bash
# WARNING: This removes ALL unused Docker volumes on your system
docker volume prune

# Remove project volumes manually
docker volume rm postgres-data whisper-uploads huggingface-cache
```

## GPU Configuration

### Requirements

1. **NVIDIA GPU** with CUDA Compute Capability 3.5+
   - Check compatibility: https://developer.nvidia.com/cuda-gpus

2. **NVIDIA Driver**
   - Linux: 450.80.02+ (recommended: latest stable)
   - Windows: 452.39+ (recommended: latest Game Ready or Studio driver)
   ```bash
   nvidia-smi  # Should display GPU info and driver version
   ```

3. **NVIDIA Container Toolkit**
   - Installed and configured (see [Prerequisites](#prerequisites))
   - Repository: https://github.com/NVIDIA/nvidia-container-toolkit
   - **Note**: Legacy `nvidia-docker` wrapper is deprecated and no longer supported

### Verification

#### Host GPU Access

```bash
# Check NVIDIA driver
nvidia-smi

# Verify NVIDIA Container Toolkit
nvidia-ctk --version

# Check Docker runtime configuration
docker info | grep -i runtime
# Should show: Runtimes: io.containerd.runc.v2 nvidia runc

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

#### Container GPU Access

```bash
# Open backend shell
python scripts/docker/shell.py backend

# Check PyTorch CUDA
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
python -c "import torch; print(f'cuDNN version: {torch.backends.cudnn.version()}')"
python -c "import torch; print(f'GPU count: {torch.cuda.device_count()}')"
python -c "import torch; print(f'GPU name: {torch.cuda.get_device_name(0)}')"

# Check faster-whisper
python -c "import faster_whisper; print('faster-whisper installed')"

# Expected output:
# PyTorch version: 2.9.1+cu128
# CUDA available: True
# CUDA version: 12.8
# cuDNN version: 90100
# GPU count: 1
# GPU name: NVIDIA GeForce RTX 5090
```

### GPU Configuration in docker-compose.yml

```yaml
backend:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1              # Number of GPUs (1 = first GPU, all = all GPUs)
            capabilities: [gpu]
```

**GPU Selection**:
- `count: 1` - Use first GPU only
- `count: all` - Use all available GPUs
- `device_ids: ['0']` - Use specific GPU by ID

**For multi-GPU systems**:
```yaml
devices:
  - driver: nvidia
    device_ids: ['0', '1']  # Use GPU 0 and GPU 1
    capabilities: [gpu]
```

### Troubleshooting GPU

#### GPU Not Detected in Container

1. **Verify NVIDIA Container Toolkit installation**:
   ```bash
   # Check if toolkit is installed
   nvidia-ctk --version

   # If not installed, install it
   sudo apt-get install -y nvidia-container-toolkit
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

2. **Check Docker runtime configuration**:
   ```bash
   docker info | grep -i runtime
   # Should show: Runtimes: io.containerd.runc.v2 nvidia runc

   # If nvidia runtime missing, reconfigure
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

3. **Verify docker-compose.yml GPU configuration**:
   ```yaml
   backend:
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: 1
               capabilities: [gpu]
   ```

4. **Test GPU access directly**:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
   # Should display GPU information
   ```

5. **Check Docker daemon configuration** (if still not working):
   ```bash
   # Verify /etc/docker/daemon.json includes nvidia runtime
   cat /etc/docker/daemon.json
   # Should contain:
   # {
   #   "runtimes": {
   #     "nvidia": {
   #       "path": "nvidia-container-runtime",
   #       "runtimeArgs": []
   #     }
   #   }
   # }

   # If missing, reconfigure with nvidia-ctk
   sudo nvidia-ctk runtime configure --runtime=docker
   sudo systemctl restart docker
   ```

#### CUDA Out of Memory

If transcription fails with "CUDA out of memory":

1. **Use smaller Whisper model**:
   ```bash
   # In .env
   PRELOAD_MODELS=tiny  # Instead of large
   ```

2. **Free GPU memory**:
   ```bash
   # Stop other GPU processes
   nvidia-smi
   kill -9 <PID>
   ```

3. **Restart backend container**:
   ```bash
   docker restart whisper-backend
   ```

## Hot-Reload Development

### How It Works

Source code mounted as read-only volumes:

```yaml
backend:
  volumes:
    - ./src:/app/src:ro                # Python source code
    - ./scripts:/app/scripts:ro         # Utility scripts

frontend:
  volumes:
    - ./src/presentation/frontend/src:/app/src:ro           # Angular source
    - ./src/presentation/frontend/angular.json:/app/angular.json:ro
```

**Backend**: Uvicorn `--reload` flag watches for file changes

**Frontend**: Angular `ng serve` watches for file changes with `--poll 1000`

### Development Workflow

1. **Start containers**:
   ```bash
   python scripts/docker/run.py --build
   ```

2. **Edit code**:
   - Backend: Edit files in `src/` or `scripts/`
   - Frontend: Edit files in `src/presentation/frontend/src/`

3. **Changes auto-detected**:
   - Backend: Uvicorn reloads Python modules (~1-2 seconds)
   - Frontend: Angular recompiles and hot-reloads (~5-10 seconds)

4. **Refresh browser**: Changes reflected immediately

### When Rebuild Required

Hot-reload does NOT work for:

**Backend**:
- Dependency changes in `requirements.txt`
- Dockerfile changes
- Environment variable changes in `.env`

**Frontend**:
- Dependency changes in `package.json`
- Dockerfile changes
- `angular.json` or `tsconfig.json` changes

**For these changes, rebuild**:
```bash
python scripts/docker/rebuild.py
```

### Performance Notes

- **Backend reload**: Fast (~1-2 seconds)
- **Frontend rebuild**: Moderate (~5-10 seconds for incremental)
- **Full rebuild**: Slow (~5-10 minutes depending on hardware)

Use hot-reload for rapid iteration, rebuild only when necessary.

## Production Deployment

### Security Hardening

#### 1. Change Default Passwords

```bash
# .env
POSTGRES_PASSWORD=<generate-random-64-char-password>
```

Generate secure password:
```bash
openssl rand -base64 48
```

#### 2. Remove Development Mounts

Edit `docker-compose.yml` to remove source code volumes:

```yaml
backend:
  volumes:
    # Remove these lines:
    # - ./src:/app/src:ro
    # - ./scripts:/app/scripts:ro

    # Keep only data volumes:
    - whisper-uploads:/app/uploads
    - huggingface-cache:/root/.cache/huggingface

frontend:
  volumes:
    # Remove these lines:
    # - ./src/presentation/frontend/src:/app/src:ro
    # - ./src/presentation/frontend/angular.json:/app/angular.json:ro
```

#### 3. Disable --reload Flag

Edit `docker-compose.yml`:

```yaml
backend:
  command: >
    sh -c "
    python3 /usr/local/bin/preload_models.py --models ${PRELOAD_MODELS:-base} &&
    python3 -m uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8001
    "
  # Removed: --reload flag
```

#### 4. Set Resource Limits

Add to `docker-compose.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '8'
        memory: 16G
      reservations:
        cpus: '4'
        memory: 8G
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]

frontend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G

postgres:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

#### 5. Network Isolation

Only expose necessary ports:

```yaml
services:
  postgres:
    # Remove:
    # ports:
    #   - "5432:5432"
    # PostgreSQL only accessible from backend, not from host

  backend:
    ports:
      - "127.0.0.1:8001:8001"  # Only localhost

  frontend:
    ports:
      - "127.0.0.1:4200:4200"  # Only localhost
```

Then use reverse proxy (Nginx, Caddy) for external access.

### Reverse Proxy Configuration

#### Nginx Example

```nginx
server {
    listen 80;
    server_name whisper.example.com;

    # Frontend
    location / {
        proxy_pass http://localhost:4200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for long transcriptions
        proxy_read_timeout 300s;
        client_max_body_size 100M;
    }

    # WebSocket support for SSE
    location /api/v1/models/download-progress {
        proxy_pass http://localhost:8001/api/v1/models/download-progress;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable HTTPS with Let's Encrypt:
```bash
sudo certbot --nginx -d whisper.example.com
```

### Monitoring

#### Health Checks

```bash
# Backend health
curl http://localhost:8001/api/v1/health

# PostgreSQL health
docker exec whisper-postgres pg_isready -U whisper

# Frontend health
curl http://localhost:4200
```

#### Resource Monitoring

```bash
# Container stats
docker stats

# GPU monitoring
nvidia-smi -l 1

# Disk usage
docker system df -v
```

#### Log Rotation

Configure Docker log rotation in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

### Backup Strategy

**Daily backups**:
```bash
#!/bin/bash
# /usr/local/bin/backup-whisper.sh

BACKUP_DIR=/backups/whisper
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec whisper-postgres pg_dump -U whisper whisper_db > "$BACKUP_DIR/db_$DATE.sql"

# Backup uploads
docker run --rm -v whisper-uploads:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/uploads_$DATE.tar.gz" -C /data .

# Keep last 7 days
find "$BACKUP_DIR" -name "db_*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-whisper.sh
```

## Troubleshooting

### Common Issues

#### Issue: Containers Fail to Start

**Symptom**: `docker-compose up` fails

**Solutions**:

1. **Check logs**:
   ```bash
   python scripts/docker/logs.py backend
   python scripts/docker/logs.py postgres
   ```

2. **Verify .env file**:
   ```bash
   cat .env
   # Ensure POSTGRES_PASSWORD is set
   ```

3. **Check port conflicts**:
   ```bash
   # Linux/macOS
   sudo netstat -tulpn | grep -E '4200|8001|5432'

   # Windows
   netstat -ano | findstr -E "4200 8001 5432"
   ```

4. **Remove and recreate**:
   ```bash
   python scripts/docker/clean.py --all
   python scripts/docker/run.py --build
   ```

#### Issue: Backend GPU Not Working

**Symptom**: Transcription slow, logs show "CUDA not available"

**Solutions**:

1. **Verify host GPU**:
   ```bash
   nvidia-smi
   ```

2. **Check Docker GPU runtime**:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
   ```

3. **Restart NVIDIA Container Toolkit**:
   ```bash
   sudo systemctl restart docker
   ```

4. **Check docker-compose.yml**:
   ```yaml
   backend:
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: 1
               capabilities: [gpu]
   ```

#### Issue: RTX 5090 CUDA Kernel Errors

**Symptom**: Transcription fails with "CUDA kernel errors" or "no kernel image available for device"

**Root Cause**: RTX 5090 (Blackwell architecture, compute capability 12.0 / sm_120) requires CUDA 12.8+ and PyTorch 2.9.0+ with sm_120 compiled binaries. CUDA 11.8 or 12.6 do not fully support this architecture.

**Solutions**:

1. **Verify Dockerfile uses CUDA 12.8**:
   ```bash
   grep "nvidia/cuda" Dockerfile
   # Should show:
   # FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 AS builder
   # FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04
   ```

2. **Verify PyTorch version in container**:
   ```bash
   docker exec whisper-backend python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"
   # Should show: PyTorch: 2.9.1+cu128, CUDA: 12.8
   ```

3. **If using older CUDA version, rebuild with CUDA 12.8**:
   ```bash
   # Update Dockerfile base images to 12.8.0
   # Update pip install command to cu128 wheel
   python scripts/docker/rebuild.py --no-cache
   ```

4. **Check GPU compute capability**:
   ```bash
   nvidia-smi --query-gpu=compute_cap --format=csv
   # RTX 5090 will show: 12.0
   ```

5. **Verify backend logs show successful GPU loading**:
   ```bash
   python scripts/docker/logs.py backend | grep -i "gpu\|cuda"
   # Should show:
   # GPU detected: NVIDIA GeForce RTX 5090
   # faster-whisper model 'base' loaded successfully on cuda
   ```

**Note**: This issue only affects RTX 5090 and newer Blackwell GPUs. Older GPUs (RTX 40xx, 30xx, etc.) work fine with CUDA 11.8.

#### Issue: Frontend Can't Connect to Backend

**Symptom**: Frontend shows network errors, API calls fail

**Solutions**:

1. **Check backend health**:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```

2. **Verify backend logs**:
   ```bash
   python scripts/docker/logs.py backend --tail 50
   ```

3. **Check CORS configuration**:
   - Ensure backend allows `http://localhost:4200` in CORS

4. **Verify network**:
   ```bash
   docker network inspect whisper_default
   ```

#### Issue: Database Connection Failed

**Symptom**: Backend logs show "could not connect to server"

**Solutions**:

1. **Check PostgreSQL health**:
   ```bash
   docker exec whisper-postgres pg_isready -U whisper
   ```

2. **Verify credentials**:
   ```bash
   # Check .env matches docker-compose.yml
   grep POSTGRES .env
   ```

3. **Check PostgreSQL logs**:
   ```bash
   python scripts/docker/logs.py postgres --tail 100
   ```

4. **Restart PostgreSQL**:
   ```bash
   docker restart whisper-postgres
   ```

#### Issue: Models Download Slow or Fail

**Symptom**: Backend stuck on "Downloading model..."

**Solutions**:

1. **Check internet connection**:
   ```bash
   python scripts/docker/shell.py backend
   curl -I https://openaipublic.azureedge.net/main/whisper/models/
   ```

2. **Pre-download models manually**:
   ```bash
   python scripts/docker/shell.py backend
   python scripts/setup/download_whisper_model.py base
   ```

3. **Use smaller model**:
   ```bash
   # .env
   PRELOAD_MODELS=tiny  # Faster download
   ```

4. **Check disk space**:
   ```bash
   docker system df -v
   df -h
   ```

#### Issue: Hot-Reload Not Working

**Symptom**: Code changes not reflected

**Solutions**:

1. **Verify volume mounts**:
   ```bash
   docker inspect whisper-backend | grep -A 10 Mounts
   ```

2. **Check file permissions**:
   ```bash
   ls -la src/
   ```

3. **Restart containers**:
   ```bash
   docker restart whisper-backend whisper-frontend
   ```

4. **Rebuild if needed**:
   ```bash
   python scripts/docker/rebuild.py
   ```

### Debugging Tools

#### Container Inspection

```bash
# View container details
docker inspect whisper-backend
docker inspect whisper-frontend
docker inspect whisper-postgres

# View container processes
docker top whisper-backend

# View container resource usage
docker stats whisper-backend
```

#### Network Debugging

```bash
# Test backend from frontend container
docker exec whisper-frontend wget -O- http://backend:8001/api/v1/health

# Test PostgreSQL from backend container
docker exec whisper-backend psql -h postgres -U whisper -d whisper_db -c "SELECT 1"
```

#### Volume Debugging

```bash
# List volume contents
docker run --rm -v huggingface-cache:/data alpine ls -lh /data
docker run --rm -v whisper-uploads:/data alpine ls -lh /data

# Check volume disk usage
docker system df -v | grep -E "whisper|huggingface"
```

## Security Considerations

### Environment Variables

- **Never commit `.env` to version control**
- Add `.env` to `.gitignore`
- Use `.env.docker` as template only

### Secrets Management

For production, use Docker secrets:

1. **Create secrets**:
   ```bash
   echo "your_secure_password" | docker secret create postgres_password -
   ```

2. **Update docker-compose.yml**:
   ```yaml
   services:
     postgres:
       environment:
         POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
       secrets:
         - postgres_password

   secrets:
     postgres_password:
       external: true
   ```

### Network Security

- **Use internal networks**: Don't expose PostgreSQL port to host
- **Firewall**: Limit access to ports 4200 and 8001
- **Reverse proxy**: Use Nginx/Caddy with HTTPS
- **Rate limiting**: Implement API rate limiting

### Container Security

- **Run as non-root**: Add USER directive to Dockerfiles
- **Read-only filesystem**: Mount volumes as read-only where possible
- **Security scanning**: Use `docker scan` to check images
- **Update regularly**: Rebuild images to get security patches

### Data Protection

- **Encrypt volumes**: Use encrypted Docker volumes
- **Backup regularly**: Daily automated backups
- **Access control**: Limit who can access Docker host
- **Audit logs**: Enable Docker audit logging

### Compliance

For HIPAA/GDPR compliance:
- Encrypt data at rest and in transit
- Implement access logging
- Regular security audits
- Data retention policies
- User consent management

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) (current, supported)
- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/index.html)
- [nvidia-docker (archived, deprecated)](https://github.com/NVIDIA/nvidia-docker) - Use NVIDIA Container Toolkit instead
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Angular Documentation](https://angular.io/docs)

## Support

For issues or questions:
- GitHub Issues: https://github.com/anashammo/whisper-ui/issues
- Project Documentation: README.md, CLAUDE.md

---

**Last Updated**: January 2026
**Docker Version**: 20.10+
**Docker Compose Version**: 2.0+
