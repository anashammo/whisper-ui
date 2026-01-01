# Docker Optimization and Project Structure Enhancement Plan

**Branch**: `feature/docker-implementation` (continuing on existing branch)
**Created**: 2026-01-01
**Status**: PLANNING

---

## Table of Contents
1. [Overview](#overview)
2. [Features Summary](#features-summary)
3. [Research & References](#research--references)
4. [Impact Analysis](#impact-analysis)
5. [Detailed Implementation Plan](#detailed-implementation-plan)
6. [Testing Strategy](#testing-strategy)
7. [Documentation Updates](#documentation-updates)
8. [Progress Tracking](#progress-tracking)

---

## Overview

This plan covers **9 interrelated features** focused on optimizing Docker build performance, improving project structure, and enhancing developer experience:

1. **Docker Build Performance**: Implement BuildKit cache mounts for faster builds
2. **Backend Dockerfile Relocation**: Move Dockerfile to `src/presentation/api/`
3. **Separate Environment Files**: Create nested `.env` files for better isolation
4. **Requirements.txt Relocation**: Move to `src/presentation/api/` with refactoring
5. **UV Package Manager**: Replace pip with uv for 10-100x faster installs
6. **Enhanced Model Cache Detection**: Comprehensive version detection for all Whisper models
7. **Unicode Character Handling**: Fix Windows console issues in all Python scripts
8. **Hot-Reload Verification**: Verify and document hot-reload configuration (already implemented)
9. **Agent Code Refactoring**: Move agent from presentation to proper clean architecture layers

---

## Features Summary

### Feature 11: Docker Build Performance Enhancement
**Goal**: Reduce Docker build time by implementing BuildKit cache mounts for pip, apt, and npm dependencies while maintaining current Whisper model volume strategy.

**Note**: Hot-reload is already implemented via volume mounts and `--reload` flag. Will verify and document.

**Current State**:
- Multi-stage Dockerfile with CUDA 12.8
- Downloads all dependencies on every rebuild
- Model cache persists in named volume (✅ keep this)
- ~20.5GB backend image, ~940MB frontend image

**Target State**:
- BuildKit cache mounts for `/root/.cache/uv` (pip cache)
- BuildKit cache mounts for `/var/cache/apt` and `/var/lib/apt` (apt cache)
- BuildKit cache mounts for `/root/.npm` (npm cache)
- Same model caching strategy (whisper-cache volume)
- Expected: 40% faster CI/CD builds, 80% faster incremental builds

---

### Feature 12: Backend Dockerfile Relocation
**Goal**: Move backend Dockerfile from root to `src/presentation/api/` for better organization.

**Current State**:
- `Dockerfile` at project root (backend)
- `src/presentation/frontend/Dockerfile` (frontend)
- `docker-compose.yml` references `dockerfile: Dockerfile`

**Target State**:
- `src/presentation/api/Dockerfile` (backend)
- `src/presentation/frontend/Dockerfile` (frontend)
- Updated `docker-compose.yml` build context

---

### Feature 13: Separate Environment Files
**Goal**: Create separate `.env` files for frontend and backend, nested in their respective component folders.

**Current State**:
- `.env.docker` at root with all configs
- `.env.example` at root
- Single `.env` file used by both services

**Target State**:
- `src/presentation/api/.env` (backend-specific configs)
- `src/presentation/api/.env.example` (backend template)
- `src/presentation/frontend/.env` (frontend-specific configs)
- `src/presentation/frontend/.env.example` (frontend template)
- `.env.docker` deprecated and removed
- Updated `docker-compose.yml` to reference both files

**Configuration Split**:
- **Backend**: Database, Whisper, LLM, API, uploads, CORS
- **Frontend**: API_URL, build configs

---

### Feature 14: Requirements.txt Relocation
**Goal**: Move `requirements.txt` to `src/presentation/api/` folder since it's backend-only.

**Current State**:
- `requirements.txt` at project root
- Referenced in `Dockerfile`, scripts, docs

**Target State**:
- `src/presentation/api/requirements.txt`
- All references updated (Dockerfile, scripts, README.md, CLAUDE.md)

**Files to Update**:
- `src/presentation/api/Dockerfile` (COPY path)
- `scripts/setup/init_db.py` (if referenced)
- `README.md` (installation instructions)
- `CLAUDE.md` (architecture docs)
- `.gitignore` (if has requirements patterns)

---

### Feature 15: UV Package Manager Migration
**Goal**: Replace pip with uv for 10-100x faster package installations in Docker and local dev.

**Research Sources**:
- [uv Documentation - Docker Integration](https://docs.astral.sh/uv/guides/integration/docker/)
- [Production-ready Python Docker with uv](https://hynek.me/articles/docker-uv/)
- [Best practices for Python & uv in Docker](https://ashishb.net/programming/using-python-uv-inside-docker/)
- [Optimal Dockerfile for Python with uv](https://depot.dev/docs/container-builds/how-to-guides/optimal-dockerfiles/python-uv-dockerfile)

**Performance Benchmarks**:
- 8-10x faster than pip without caching
- 115x faster with warm cache
- 40% faster CI/CD pipelines reported
- Cold install of JupyterLab: 2.6s (uv) vs 21.4s (pip)

**Migration Strategy**:
1. **Dockerfile Changes**:
   - Copy uv from official image: `COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /uvx /bin/`
   - Use cache mounts: `--mount=type=cache,target=/root/.cache/uv`
   - Enable bytecode compilation: `ENV UV_COMPILE_BYTECODE=1`
   - Set link mode: `ENV UV_LINK_MODE=copy`
   - Replace `pip install` with `uv pip install`

2. **Local Development**:
   - Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Linux/Mac) or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
   - Update scripts to use `uv pip` instead of `pip`
   - Maintain backward compatibility: scripts should detect uv availability

3. **Key Benefits**:
   - Parallel downloads
   - Global module cache
   - Rust-native performance
   - Drop-in pip replacement (same command syntax with `uv pip`)

---

### Feature 16: Enhanced Model Cache Detection
**Goal**: Improve model cache detection to handle all Whisper model versions and variants.

**Current State** (partially implemented):
- Checks `large-v3.pt`, `large-v3-turbo.pt`
- Misses `large-v1.pt`, `large-v2.pt`
- Incomplete coverage for `.en` variants

**Whisper Model Naming Conventions**:
```python
tiny    → tiny.pt, tiny.en.pt
base    → base.pt, base.en.pt
small   → small.pt, small.en.pt
medium  → medium.pt, medium.en.pt
large   → large.pt, large-v1.pt, large-v2.pt, large-v3.pt
turbo   → turbo.pt, large-v3-turbo.pt
```

**Target State**:
- Check ALL version variants for each model
- Prefer latest version but accept any cached version
- Consistent implementation across all scripts that check model cache

**Files to Update**:
- `scripts/docker/preload_models.py` - `model_exists()` function
- `src/infrastructure/services/whisper_service.py` (if has cache checks)
- Any other scripts that check model cache

---

### Feature 17: Unicode Character Handling in Scripts
**Goal**: Fix Windows console encoding issues for all Python scripts that use Unicode characters.

**Unicode Characters Used**:
- ✓ (U+2713) - Check mark
- ✗ (U+2717) - Cross mark
- ⬇ (U+2B07) - Down arrow
- ❌ (U+274C) - Cross mark emoji
- ✅ (U+2705) - Check mark emoji
- ⊳ (U+22B3) - Right triangle
- ⚠️ (U+26A0 + U+FE0F) - Warning sign

**Scripts Already Fixed**:
- ✅ `scripts/docker/build.py`
- ✅ `scripts/docker/preload_models.py`

**Scripts Needing Fix** (found via grep):
- `scripts/docker/clean.py`
- `scripts/docker/rebuild.py`
- `scripts/maintenance/cleanup_orphaned_transcriptions.py`
- `scripts/setup/init_db.py`
- `scripts/setup/download_whisper_model.py`
- `scripts/migrations/migrate_add_processing_time.py`
- `scripts/migrations/migrate_add_model_column.py`

**Standard Fix** (add to top of each script):
```python
#!/usr/bin/env python3
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

---

### Feature 18: Verify and Document Hot-Reload Configuration
**Goal**: Ensure hot-reload is properly configured for both backend and frontend, avoiding rebuilds for code changes (especially important with large dependencies like PyTorch).

**Current State** (Already Implemented):
- ✅ Backend: Source mounted as volume (`./src:/app/src:ro`)
- ✅ Backend: Uvicorn `--reload` flag enabled
- ✅ Frontend: Source files mounted (`./src/presentation/frontend/src:/app/src:ro`)
- ✅ Frontend: Angular dev server with `--poll 1000`

**Tasks**:
1. Verify hot-reload works for backend Python code changes
2. Verify hot-reload works for frontend TypeScript/HTML changes
3. Consider if `:ro` (read-only) should be removed for better compatibility
4. Document in README.md and CLAUDE.md
5. Add troubleshooting section for hot-reload issues

**Expected Behavior**:
- Backend code change → Uvicorn auto-reloads (no rebuild needed)
- Frontend code change → Angular recompiles (no rebuild needed)
- PyTorch and large deps stay in image (not affected by code changes)

---

### Feature 19: Refactor Agent Code Following Clean Architecture
**Goal**: Move agent code from `src/presentation/agent/` to proper clean architecture layers.

**Current State**:
```
src/presentation/agent/
├── __init__.py
├── enhancement_agent.py    # LangGraph workflow (APPLICATION LOGIC)
├── llm_client.py           # HTTP client (INFRASTRUCTURE)
└── prompts.py              # Prompts (APPLICATION LOGIC)
```

**Used By**: `src/infrastructure/services/llm_enhancement_service_impl.py`

**Clean Architecture Issue**:
- Agent code is in **presentation layer** but it's actually **application logic**
- LLMClient is **infrastructure** (external HTTP client)
- Violates clean architecture dependency rules

**Target State** (Proper Layer Separation):
```
src/application/enhancement/
├── __init__.py
├── enhancement_agent.py    # LangGraph workflow
└── prompts.py              # Enhancement prompts

src/infrastructure/llm/
├── __init__.py
└── llm_client.py           # OpenAI-compatible HTTP client
```

**Refactoring Impact**:
- Update imports in `src/infrastructure/services/llm_enhancement_service_impl.py`
- Update any tests that import from presentation.agent
- Update CLAUDE.md architecture documentation
- Verify clean architecture dependency rules are followed

**Dependency Flow** (After Refactor):
```
Infrastructure (llm_enhancement_service_impl.py)
    ↓ imports
Application (enhancement_agent.py)
    ↓ imports
Infrastructure (llm_client.py)
```

This is acceptable because:
- Infrastructure can depend on Application (outer depends on inner)
- Application uses Infrastructure via dependency injection (agent receives LLMClient instance)

---

## Research & References

### UV Package Manager
1. [Installation | uv](https://docs.astral.sh/uv/getting-started/installation/) - Official installation guide
2. [Using uv in Docker | uv](https://docs.astral.sh/uv/guides/integration/docker/) - Docker integration guide
3. [Production-ready Python Docker Containers with uv](https://hynek.me/articles/docker-uv/) - Production best practices
4. [Best practices for using Python & uv inside Docker](https://ashishb.net/programming/using-python-uv-inside-docker/) - Docker optimization
5. [uv vs pip: Managing Python Packages and Dependencies](https://realpython.com/uv-vs-pip/) - Comparison and benchmarks
6. [UV: A Faster, More Efficient Python Package Manager](https://dev.to/mechcloud_academy/uv-a-faster-more-efficient-python-package-manager-fle) - Performance analysis

### Docker BuildKit
- BuildKit cache mounts documentation
- Multi-stage build best practices
- Layer caching strategies

---

## Impact Analysis

### Database Layer
**Impact**: ❌ None
**Reason**: These are infrastructure and configuration changes only

---

### Backend (API) Layer
**Impact**: ⚠️ Medium

**Files Modified**:
- `src/presentation/api/Dockerfile` (created/moved from root)
- `src/presentation/api/requirements.txt` (moved from root)
- `src/presentation/api/.env` (created)
- `src/presentation/api/.env.example` (created)
- `src/infrastructure/services/whisper_service.py` (model cache detection enhancement)

**Behavior Changes**:
- Faster builds (transparent to runtime)
- UV instead of pip (transparent to runtime)
- Environment variable loading path changes (needs testing)

---

### Frontend Layer
**Impact**: ⚠️ Low

**Files Modified**:
- `src/presentation/frontend/.env` (created)
- `src/presentation/frontend/.env.example` (created)
- `src/presentation/frontend/Dockerfile` (minor updates for BuildKit cache)

**Behavior Changes**:
- Faster npm install in Docker (transparent to runtime)
- Environment variable loading (needs verification)

---

### Docker Infrastructure
**Impact**: ⚠️ High

**Files Modified**:
- `docker-compose.yml` (build context, env_file directives)
- `src/presentation/api/Dockerfile` (moved + BuildKit + uv)
- `src/presentation/frontend/Dockerfile` (BuildKit cache)

**Behavior Changes**:
- Requires Docker BuildKit enabled (DOCKER_BUILDKIT=1)
- Different cache strategy (faster rebuilds)
- Multiple .env files loaded per service

---

### Scripts
**Impact**: ⚠️ Medium

**Files Modified**:
- All scripts in `scripts/docker/` (Unicode fix + uv compatibility)
- All scripts in `scripts/setup/` (Unicode fix + requirements.txt path)
- All scripts in `scripts/maintenance/` (Unicode fix)
- All scripts in `scripts/migrations/` (Unicode fix)
- All scripts in `scripts/server/` (requirements.txt path if referenced)

**Behavior Changes**:
- Windows console output works correctly with Unicode
- Scripts use `uv pip` when available, fall back to `pip`

---

## Detailed Implementation Plan

### Phase 1: Preparation & Validation (Tasks 1-5)

#### Task 1.1: Enable Docker BuildKit
**File**: N/A (environment configuration)
**Action**:
- Verify Docker version supports BuildKit (18.09+)
- Set `DOCKER_BUILDKIT=1` environment variable
- Test BuildKit syntax: `docker buildx version`

**Validation**:
```bash
docker buildx version
# Should show: github.com/docker/buildx vX.X.X
```

**Status**: [ ] Not Started

---

#### Task 1.2: Create Plans Directory Backup
**File**: `plans/DOCKER_OPTIMIZATION_AND_STRUCTURE_PLAN.md`
**Action**:
- Save this plan
- Create progress tracking checklist

**Status**: [ ] Not Started

---

#### Task 1.3: Research UV Installation
**File**: N/A (research task)
**Action**:
- Verify latest uv version: https://github.com/astral-sh/uv/releases
- Document Windows/Linux installation commands
- Test uv locally: `uv --version`

**Validation**:
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
uv --version

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

**Status**: [ ] Not Started

---

#### Task 1.4: Backup Current Configuration
**Files**: `.env`, `docker-compose.yml`, `Dockerfile`, `requirements.txt`
**Action**:
- Create backup branch: `git stash` (if uncommitted changes)
- Tag current state: `git tag -a pre-optimization -m "Before optimization changes"`

**Status**: [ ] Not Started

---

#### Task 1.5: Test Current Docker Setup
**Action**:
- Stop all containers: `python scripts/docker/stop.py`
- Rebuild fresh: `python scripts/docker/rebuild.py`
- Test transcription: Verify frontend works at localhost:4200
- Document current build time (baseline)

**Baseline Metrics**:
- Backend build time: `_____ seconds`
- Frontend build time: `_____ seconds`
- Total docker-compose up time: `_____ seconds`

**Status**: [ ] Not Started

---

### Phase 2: Feature 15 - UV Package Manager Migration (Tasks 6-10)

#### Task 2.1: Install UV Locally
**Action**:
- Install uv on development machine
- Verify installation: `uv --version`
- Test with current requirements: `uv pip install -r requirements.txt` (dry run)

**Commands**:
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version
```

**Status**: [ ] Not Started

---

#### Task 2.2: Update Backend Dockerfile for UV (Part 1 - Builder Stage)
**File**: `Dockerfile` (root, will move later)
**Action**:
- Add UV installation in builder stage
- Replace pip commands with uv pip
- Add BuildKit cache mounts

**Changes**:
```dockerfile
# ============================================================================
# Stage 1: Builder - Install dependencies with UV
# ============================================================================
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 AS builder

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /uvx /bin/

# Set UV environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Set working directory
WORKDIR /build

# Copy requirements file
COPY requirements.txt .

# Install PyTorch with CUDA 12.8 support FIRST
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install remaining Python dependencies with UV
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt
```

**Status**: [ ] Not Started

---

#### Task 2.3: Update Backend Dockerfile for UV (Part 2 - Runtime Stage)
**File**: `Dockerfile` (root, will move later)
**Action**:
- No changes needed in runtime stage (just copies from builder)

**Status**: [ ] Not Started

---

#### Task 2.4: Update Frontend Dockerfile for NPM Cache
**File**: `src/presentation/frontend/Dockerfile`
**Action**:
- Add BuildKit cache mount for npm

**Changes**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm install

# Install Angular CLI globally with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm install -g @angular/cli

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

**Status**: [ ] Not Started

---

#### Task 2.5: Update Docker Compose for BuildKit
**File**: `docker-compose.yml`
**Action**:
- No changes needed (BuildKit is environment setting)
- Document DOCKER_BUILDKIT=1 requirement in README

**Status**: [ ] Not Started

---

#### Task 2.6: Test UV Docker Build
**Action**:
- Set DOCKER_BUILDKIT=1: `$env:DOCKER_BUILDKIT=1` (PowerShell) or `export DOCKER_BUILDKIT=1` (Bash)
- Clean rebuild: `python scripts/docker/rebuild.py`
- Verify containers start successfully
- Test transcription functionality

**Validation**:
- Backend container healthy
- Frontend accessible at localhost:4200
- Transcription works
- Measure new build time (compare to baseline)

**Metrics**:
- Backend build time: `_____ seconds` (expected: 40% faster on incremental)
- Frontend build time: `_____ seconds`
- Total time: `_____ seconds`

**Status**: [ ] Not Started

---

#### Task 2.7: Update Local Development Scripts for UV
**Files**:
- `scripts/setup/init_db.py`
- `scripts/setup/download_whisper_model.py`
- Any script that runs pip commands

**Action**:
- Add UV detection and fallback logic
- Update documentation strings

**Pattern**:
```python
import subprocess
import shutil

def get_pip_command():
    """Get pip command, preferring uv if available."""
    if shutil.which('uv'):
        return ['uv', 'pip']
    return ['pip']

# Usage
pip_cmd = get_pip_command()
subprocess.run([*pip_cmd, 'install', 'package_name'])
```

**Status**: [ ] Not Started

---

#### Task 2.8: Create UV Installation Script
**File**: `scripts/setup/install_uv.py` (new)
**Action**:
- Create script to install UV on development machine
- Platform detection (Windows/Linux/Mac)
- Verification step

**Content**:
```python
#!/usr/bin/env python3
"""Install UV package manager"""
import sys
import subprocess
import shutil

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("Installing UV package manager...")

    if shutil.which('uv'):
        print("✓ UV already installed")
        subprocess.run(['uv', '--version'])
        return

    try:
        if sys.platform == 'win32':
            # Windows
            subprocess.run([
                'powershell', '-c',
                'irm https://astral.sh/uv/install.ps1 | iex'
            ], check=True)
        else:
            # Linux/Mac
            subprocess.run([
                'sh', '-c',
                'curl -LsSf https://astral.sh/uv/install.sh | sh'
            ], check=True)

        print("✅ UV installed successfully!")
        subprocess.run(['uv', '--version'])

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install UV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Status**: [ ] Not Started

---

#### Task 2.9: Test UV with Current Requirements
**Action**:
- Create test virtual environment
- Install with UV: `uv pip install -r requirements.txt`
- Verify all packages installed correctly
- Run backend tests: `pytest`

**Commands**:
```bash
python -m venv venv_test
# Windows
venv_test\Scripts\activate
# Linux
source venv_test/bin/activate

uv pip install -r requirements.txt
pytest
```

**Status**: [ ] Not Started

---

#### Task 2.10: Update Requirements.txt Comments
**File**: `requirements.txt` (root, will move later)
**Action**:
- Add comment about UV compatibility
- Document installation command

**Addition** (at top):
```text
# Python Dependencies for Whisper Transcription API
#
# Installation:
#   With UV (recommended, 10-100x faster): uv pip install -r requirements.txt
#   With pip: pip install -r requirements.txt
#
# Note: PyTorch with CUDA 12.8 should be installed separately first:
#   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**Status**: [ ] Not Started

---

### Phase 3: Feature 14 - Requirements.txt Relocation (Tasks 11-15)

#### Task 3.1: Move Requirements.txt to Backend Folder
**Action**:
- Move: `requirements.txt` → `src/presentation/api/requirements.txt`
- Git track the move: `git mv requirements.txt src/presentation/api/requirements.txt`

**Commands**:
```bash
git mv requirements.txt src/presentation/api/requirements.txt
```

**Status**: [ ] Not Started

---

#### Task 3.2: Update Dockerfile Path Reference
**File**: `Dockerfile` (root, will move later)
**Action**:
- Update COPY path for requirements.txt

**Change**:
```dockerfile
# OLD
COPY requirements.txt .

# NEW
COPY src/presentation/api/requirements.txt .
```

**Status**: [ ] Not Started

---

#### Task 3.3: Update README.md References
**File**: `README.md`
**Action**:
- Find all references to `requirements.txt`
- Update paths to `src/presentation/api/requirements.txt`

**Search Pattern**: `requirements.txt`

**Expected Changes**:
- Installation instructions
- Virtual environment setup
- PyTorch installation commands

**Status**: [ ] Not Started

---

#### Task 3.4: Update CLAUDE.md References
**File**: `CLAUDE.md`
**Action**:
- Update all `requirements.txt` references
- Update backend structure diagram

**Expected Changes**:
```markdown
# OLD
pip install -r requirements.txt

# NEW
pip install -r src/presentation/api/requirements.txt

# Backend Structure
src/presentation/api/
├── requirements.txt          # Python dependencies
├── .env                      # Backend environment config
├── .env.example              # Backend env template
└── ...
```

**Status**: [ ] Not Started

---

#### Task 3.5: Update Scripts References
**Files**:
- `scripts/setup/init_db.py`
- `scripts/setup/download_whisper_model.py`
- Any other scripts that reference requirements.txt

**Action**:
- Search for `requirements.txt` in all scripts
- Update paths if any scripts reference it

**Search Command**:
```bash
grep -r "requirements.txt" scripts/
```

**Status**: [ ] Not Started

---

#### Task 3.6: Update .gitignore (if needed)
**File**: `.gitignore`
**Action**:
- Check if .gitignore has patterns for requirements.txt
- Update if necessary

**Search**:
```bash
grep requirements .gitignore
```

**Status**: [ ] Not Started

---

#### Task 3.7: Test Requirements Path Update
**Action**:
- Rebuild Docker: `python scripts/docker/rebuild.py`
- Verify build succeeds
- Verify containers start

**Status**: [ ] Not Started

---

### Phase 4: Feature 12 - Backend Dockerfile Relocation (Tasks 16-20)

#### Task 4.1: Move Dockerfile to Backend Folder
**Action**:
- Move: `Dockerfile` → `src/presentation/api/Dockerfile`
- Git track: `git mv Dockerfile src/presentation/api/Dockerfile`

**Commands**:
```bash
git mv Dockerfile src/presentation/api/Dockerfile
```

**Status**: [ ] Not Started

---

#### Task 4.2: Update Dockerfile Build Context Paths
**File**: `src/presentation/api/Dockerfile`
**Action**:
- Update all COPY paths to account for new context
- Build context will be project root, Dockerfile is nested

**Changes**:
```dockerfile
# Context is still project root, so paths stay the same
# OR we can change context in docker-compose.yml

# Current paths are correct relative to root:
COPY src/presentation/api/requirements.txt /build/requirements.txt
COPY src/ ./src/
COPY scripts/ ./scripts/
```

**Decision**: Keep context as root (.) in docker-compose, just change dockerfile path

**Status**: [ ] Not Started

---

#### Task 4.3: Update docker-compose.yml Backend Build
**File**: `docker-compose.yml`
**Action**:
- Update backend service `dockerfile` path

**Change**:
```yaml
backend:
  build:
    context: .
    dockerfile: src/presentation/api/Dockerfile  # Changed from: Dockerfile
```

**Status**: [ ] Not Started

---

#### Task 4.4: Update Docker Scripts
**Files**:
- `scripts/docker/build.py`
- Any other scripts that reference Dockerfile directly

**Action**:
- Check if scripts hardcode Dockerfile path
- Update if necessary

**Search**:
```bash
grep -r "Dockerfile" scripts/docker/
```

**Expected**: Most scripts use docker-compose, which has the path configured

**Status**: [ ] Not Started

---

#### Task 4.5: Update Documentation for Dockerfile Location
**Files**:
- `README.md`
- `CLAUDE.md`
- `plans/DOCKER_IMPLEMENTATION_PLAN.md`

**Action**:
- Update references to backend Dockerfile location
- Update architecture diagrams

**Status**: [ ] Not Started

---

#### Task 4.6: Test Dockerfile Relocation
**Action**:
- Rebuild: `python scripts/docker/rebuild.py`
- Verify build succeeds
- Verify containers start and work

**Status**: [ ] Not Started

---

### Phase 5: Feature 13 - Separate Environment Files (Tasks 21-30)

#### Task 5.1: Create Backend .env Template
**File**: `src/presentation/api/.env.example` (new)
**Action**:
- Extract backend-specific configs from `.env.docker`
- Create template with comments

**Content**:
```bash
# ============================================================================
# Backend API - Environment Configuration
# ============================================================================
# Copy this file to .env and configure as needed
# ============================================================================

# ============================================================================
# PostgreSQL Database Configuration
# ============================================================================
POSTGRES_USER=whisper
POSTGRES_PASSWORD=change_this_secure_password_in_production
POSTGRES_DB=whisper_db

# Database connection URL (auto-constructed in docker-compose.yml)
# For local dev with SQLite: sqlite:///./whisper_transcriptions.db
# For Docker with PostgreSQL: postgresql://whisper:password@postgres:5432/whisper_db
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# ============================================================================
# Application Settings
# ============================================================================
APP_NAME=Whisper Transcription API
APP_VERSION=1.0.0
DEBUG=false

# ============================================================================
# API Server Configuration
# ============================================================================
API_HOST=0.0.0.0
API_PORT=8001

# ============================================================================
# Whisper Configuration
# ============================================================================
WHISPER_MODEL=base
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# ============================================================================
# File Upload Settings
# ============================================================================
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE_MB=25
MAX_DURATION_SECONDS=30

# ============================================================================
# CORS Configuration
# ============================================================================
CORS_ORIGINS=["http://localhost","http://localhost:4200","http://frontend","*"]

# ============================================================================
# LLM Enhancement Configuration (Optional)
# ============================================================================
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_MODEL=llama3
LLM_TIMEOUT_SECONDS=60
LLM_TEMPERATURE=0.3

# ============================================================================
# GPU Configuration
# ============================================================================
CUDA_VISIBLE_DEVICES=0

# ============================================================================
# Model Pre-loading (Docker only)
# ============================================================================
PRELOAD_MODELS=base
FORCE_DOWNLOAD=

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO
```

**Status**: [ ] Not Started

---

#### Task 5.2: Create Backend .env for Development
**File**: `src/presentation/api/.env` (new, gitignored)
**Action**:
- Copy from .env.example
- Set development-friendly defaults

**Status**: [ ] Not Started

---

#### Task 5.3: Create Frontend .env Template
**File**: `src/presentation/frontend/.env.example` (new)
**Action**:
- Extract frontend configs

**Content**:
```bash
# ============================================================================
# Frontend - Environment Configuration
# ============================================================================
# Copy this file to .env and configure as needed
# ============================================================================

# ============================================================================
# Backend API Configuration
# ============================================================================
# URL of the backend API
# Development (local): http://localhost:8001/api/v1
# Docker: http://backend:8001/api/v1 (internal) or http://localhost:8001/api/v1 (external)
API_URL=http://localhost:8001/api/v1

# ============================================================================
# Build Configuration
# ============================================================================
# Angular build configuration
# Options: development, production
NODE_ENV=development
```

**Status**: [ ] Not Started

---

#### Task 5.4: Create Frontend .env for Development
**File**: `src/presentation/frontend/.env` (new, gitignored)
**Action**:
- Copy from .env.example

**Status**: [ ] Not Started

---

#### Task 5.5: Update .gitignore for New .env Files
**File**: `.gitignore`
**Action**:
- Add patterns for nested .env files

**Addition**:
```gitignore
# Environment files
.env
.env.local
.env.*.local
src/presentation/api/.env
src/presentation/frontend/.env

# Keep templates
!.env.example
!src/presentation/api/.env.example
!src/presentation/frontend/.env.example
```

**Status**: [ ] Not Started

---

#### Task 5.6: Update docker-compose.yml for Multiple env_file
**File**: `docker-compose.yml`
**Action**:
- Update backend service to use `src/presentation/api/.env`
- Update frontend service to use `src/presentation/frontend/.env`
- Remove old `.env` reference

**Changes**:
```yaml
backend:
  # ... existing config ...
  env_file:
    - src/presentation/api/.env
  # ... rest ...

frontend:
  # ... existing config ...
  env_file:
    - src/presentation/frontend/.env
  # ... rest ...
```

**Status**: [ ] Not Started

---

#### Task 5.7: Update Backend to Load .env from Correct Path
**File**: `src/presentation/api/main.py`
**Action**:
- Verify dotenv loading logic
- Update path if hardcoded

**Check**:
```python
from dotenv import load_dotenv

# Should auto-detect .env in same directory or parent
load_dotenv()  # Default behavior

# OR explicit path if needed:
# load_dotenv(Path(__file__).parent / ".env")
```

**Status**: [ ] Not Started

---

#### Task 5.8: Update Frontend Environment Loading
**File**: `src/presentation/frontend/src/environments/environment.ts`
**Action**:
- Verify if Angular reads .env files
- May need angular-dotenv or similar package

**Research**: Angular doesn't natively read .env files at runtime (build time only)

**Decision**: Frontend .env is for Docker container build-time only. Runtime API URL is in environment.ts

**Status**: [ ] Not Started

---

#### Task 5.9: Update README.md for New .env Structure
**File**: `README.md`
**Action**:
- Update installation instructions
- Document new .env locations

**Section to Update**:
```markdown
## Configuration

### Backend Configuration
Copy the backend environment template:
```bash
cp src/presentation/api/.env.example src/presentation/api/.env
```

Edit `src/presentation/api/.env` and configure:
- Database settings
- API port (default: 8001)
- Whisper model and device
- etc.

### Frontend Configuration
Copy the frontend environment template:
```bash
cp src/presentation/frontend/.env.example src/presentation/frontend/.env
```

Edit `src/presentation/frontend/.env` and set the backend API URL.
```

**Status**: [ ] Not Started

---

#### Task 5.10: Update CLAUDE.md for New .env Structure
**File**: `CLAUDE.md`
**Action**:
- Update configuration documentation
- Update file structure diagram

**Status**: [ ] Not Started

---

#### Task 5.11: Deprecate Old .env.docker
**File**: `.env.docker`
**Action**:
- Rename to `.env.docker.deprecated`
- Add deprecation notice
- Update .gitignore

**Status**: [ ] Not Started

---

#### Task 5.12: Create Migration Script for .env Files
**File**: `scripts/maintenance/migrate_env_files.py` (new)
**Action**:
- Create helper script to migrate old .env to new structure
- Parse old .env and split into backend/frontend

**Status**: [ ] Not Started

---

#### Task 5.13: Test New .env Configuration
**Action**:
- Create both .env files from templates
- Start Docker: `python scripts/docker/run.py`
- Verify environment variables loaded correctly
- Test backend API: Check logs for config values
- Test frontend: Verify API_URL is correct

**Validation**:
```bash
# Check backend env loaded
docker exec whisper-backend env | grep DATABASE_URL

# Check frontend env loaded
docker exec whisper-frontend env | grep API_URL
```

**Status**: [ ] Not Started

---

### Phase 6: Feature 16 - Enhanced Model Cache Detection (Tasks 31-35)

#### Task 6.1: Research All Whisper Model Versions
**Action**:
- Verify Whisper naming conventions
- Check OpenAI Whisper repository for version history
- Document all possible filenames

**Reference**: https://github.com/openai/whisper

**Findings**:
```
tiny    → tiny.pt, tiny.en.pt
base    → base.pt, base.en.pt
small   → small.pt, small.en.pt
medium  → medium.pt, medium.en.pt
large   → large.pt, large-v1.pt, large-v2.pt, large-v3.pt
turbo   → turbo.pt, large-v3-turbo.pt
```

**Status**: [ ] Not Started

---

#### Task 6.2: Update preload_models.py model_exists()
**File**: `scripts/docker/preload_models.py`
**Action**:
- Enhance `model_exists()` function
- Check ALL variants for each model

**Current Code** (lines 26-56):
```python
def model_exists(model_name: str) -> bool:
    """Check if a Whisper model exists in cache."""
    # Whisper uses versioned names: large -> large-v3, turbo -> large-v3-turbo
    # Check for both versioned and non-versioned filenames
    possible_names = [f"{model_name}.pt"]

    # Add versioned variants
    if model_name == "large":
        possible_names.extend(["large-v1.pt", "large-v2.pt", "large-v3.pt"])
    elif model_name == "turbo":
        possible_names.extend(["turbo.pt", "large-v3-turbo.pt"])
    elif model_name == "medium":
        possible_names.extend(["medium.en.pt"])
    elif model_name == "small":
        possible_names.extend(["small.en.pt"])
    elif model_name == "base":
        possible_names.extend(["base.en.pt"])
    elif model_name == "tiny":
        possible_names.extend(["tiny.en.pt"])

    # Check if any variant exists
    for variant in possible_names:
        model_file = CACHE_DIR / variant
        if model_file.exists():
            file_size_mb = model_file.stat().st_size / (1024 * 1024)
            print(f"✓ Model '{model_name}' found in cache as '{variant}' ({file_size_mb:.1f} MB)")
            return True

    print(f"✗ Model '{model_name}' not found in cache")
    return False
```

**Status**: ✅ Already implemented correctly (all variants checked)

---

#### Task 6.3: Check WhisperService for Model Cache Logic
**File**: `src/infrastructure/services/whisper_service.py`
**Action**:
- Search for model caching logic
- Update if similar check exists

**Search Pattern**: `cache`, `model_exists`, `.pt`

**Status**: [ ] Not Started

---

#### Task 6.4: Verify Model Download Logic
**File**: `scripts/setup/download_whisper_model.py`
**Action**:
- Check if script has cache detection
- Ensure consistency with preload_models.py

**Status**: [ ] Not Started

---

#### Task 6.5: Test Model Cache Detection
**Action**:
- Clear model cache: Delete files in `~/.cache/whisper/` or Docker volume
- Download specific version: e.g., large-v2
- Run preload script: Verify it detects large-v2 as "large"
- Test with all models

**Test Cases**:
- [ ] tiny.pt detected
- [ ] tiny.en.pt detected
- [ ] base.pt detected
- [ ] base.en.pt detected
- [ ] small.pt detected
- [ ] small.en.pt detected
- [ ] medium.pt detected
- [ ] medium.en.pt detected
- [ ] large.pt detected
- [ ] large-v1.pt detected
- [ ] large-v2.pt detected
- [ ] large-v3.pt detected
- [ ] turbo.pt detected
- [ ] large-v3-turbo.pt detected

**Status**: [ ] Not Started

---

### Phase 7: Feature 17 - Unicode Character Handling (Tasks 36-45)

#### Task 7.1: Create Standard Unicode Fix Template
**Action**:
- Document standard fix pattern
- Create helper module (optional)

**Standard Fix**:
```python
#!/usr/bin/env python3
import sys

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

**Status**: [ ] Not Started

---

#### Task 7.2: Fix scripts/docker/clean.py
**File**: `scripts/docker/clean.py`
**Action**:
- Add Unicode fix at top
- Verify Unicode characters: ⚠️, ✅

**Status**: [ ] Not Started

---

#### Task 7.3: Fix scripts/docker/rebuild.py
**File**: `scripts/docker/rebuild.py`
**Action**:
- Add Unicode fix at top
- Verify Unicode characters: [X], [✓]

**Note**: Uses [X] and [✓], should work but add fix anyway for consistency

**Status**: [ ] Not Started

---

#### Task 7.4: Fix scripts/maintenance/cleanup_orphaned_transcriptions.py
**File**: `scripts/maintenance/cleanup_orphaned_transcriptions.py`
**Action**:
- Read file to find Unicode characters
- Add Unicode fix at top

**Status**: [ ] Not Started

---

#### Task 7.5: Fix scripts/setup/init_db.py
**File**: `scripts/setup/init_db.py`
**Action**:
- Read file to find Unicode characters
- Add Unicode fix at top

**Status**: [ ] Not Started

---

#### Task 7.6: Fix scripts/setup/download_whisper_model.py
**File**: `scripts/setup/download_whisper_model.py`
**Action**:
- Read file to find Unicode characters
- Add Unicode fix at top

**Status**: [ ] Not Started

---

#### Task 7.7: Fix scripts/migrations/migrate_add_processing_time.py
**File**: `scripts/migrations/migrate_add_processing_time.py`
**Action**:
- Read file to find Unicode characters
- Add Unicode fix at top

**Status**: [ ] Not Started

---

#### Task 7.8: Fix scripts/migrations/migrate_add_model_column.py
**File**: `scripts/migrations/migrate_add_model_column.py`
**Action**:
- Read file to find Unicode characters
- Add Unicode fix at top

**Status**: [ ] Not Started

---

#### Task 7.9: Scan for Any Missed Scripts
**Action**:
- Search entire scripts/ directory for Unicode characters
- Add fix to any missed files

**Command**:
```bash
# Already done in planning phase
grep -r "✓\|✗\|⬇\|❌\|✅\|⊳" scripts/
```

**Status**: [ ] Not Started

---

#### Task 7.10: Test All Scripts on Windows Console
**Action**:
- Run each script on Windows console
- Verify no UnicodeEncodeError
- Verify Unicode characters display correctly

**Test Scripts**:
- [ ] scripts/docker/build.py
- [ ] scripts/docker/clean.py
- [ ] scripts/docker/rebuild.py
- [ ] scripts/docker/preload_models.py
- [ ] scripts/maintenance/cleanup_orphaned_transcriptions.py
- [ ] scripts/setup/init_db.py
- [ ] scripts/setup/download_whisper_model.py
- [ ] scripts/migrations/migrate_add_processing_time.py
- [ ] scripts/migrations/migrate_add_model_column.py

**Status**: [ ] Not Started

---

### Phase 8: Feature 18 - Hot-Reload Verification (Tasks 46-50)

#### Task 8.1: Test Backend Hot-Reload
**Action**:
- Start Docker containers: `python scripts/docker/run.py`
- Make code change in backend (e.g., add comment in `src/presentation/api/main.py`)
- Watch logs: `python scripts/docker/logs.py backend -f`
- Verify Uvicorn detects change and reloads

**Expected Output in Logs**:
```
INFO:     Will watch for changes in these directories: ['/app/src']
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
WARNING:  StatReload detected changes in '/app/src/presentation/api/main.py'. Reloading...
INFO:     Application startup complete.
```

**Validation**:
- [ ] Uvicorn detects file changes
- [ ] Application reloads within 2-3 seconds
- [ ] No "permission denied" or volume mount errors
- [ ] PyTorch not reloaded (only app code)

**Status**: [ ] Not Started

---

#### Task 8.2: Test Frontend Hot-Reload
**Action**:
- Frontend should already be running
- Make code change in frontend (e.g., edit `src/presentation/frontend/src/app/app.component.html`)
- Watch browser and terminal logs
- Verify Angular recompiles and browser auto-refreshes

**Expected Behavior**:
- Angular detects file change
- Recompiles affected modules
- Browser auto-refreshes (or LiveReload triggers)
- No full container rebuild needed

**Validation**:
- [ ] Angular detects file changes
- [ ] Compilation happens within seconds
- [ ] Browser updates (manual refresh or auto)
- [ ] No errors in console

**Status**: [ ] Not Started

---

#### Task 8.3: Investigate Read-Only Volume Issue (if any)
**File**: `docker-compose.yml`
**Action**:
- Volumes currently mounted with `:ro` (read-only)
- Test if this causes issues with some dev tools (file watchers, temp files)
- If issues found, remove `:ro` flag

**Current**:
```yaml
volumes:
  - ./src:/app/src:ro
  - ./scripts:/app/scripts:ro
```

**Alternative** (if `:ro` causes issues):
```yaml
volumes:
  - ./src:/app/src
  - ./scripts:/app/scripts
```

**Decision**:
- Keep `:ro` if no issues (better security)
- Remove `:ro` if file watchers fail

**Status**: [ ] Not Started

---

#### Task 8.4: Document Hot-Reload in README.md
**File**: `README.md`
**Action**:
- Add section explaining hot-reload feature
- Document expected behavior
- Add troubleshooting tips

**Section to Add**:
```markdown
## Development Workflow

### Hot-Reload (No Rebuild Needed)

Both backend and frontend support hot-reload for rapid development:

**Backend (Python/FastAPI)**:
- Source code mounted as volume: `./src:/app/src`
- Uvicorn runs with `--reload` flag
- **Code changes auto-reload in 2-3 seconds**
- Large dependencies (PyTorch, CUDA) stay in container image (not reloaded)

**Frontend (Angular)**:
- Source files mounted as volumes
- Angular dev server watches for changes
- **Browser auto-refreshes on code changes**

**Usage**:
1. Start containers: `python scripts/docker/run.py`
2. Edit code in your IDE (VSCode, PyCharm, etc.)
3. Save file
4. Watch logs: `python scripts/docker/logs.py -f`
5. Backend reloads automatically, frontend recompiles

**Troubleshooting**:
- **Changes not detected**: Check volume mounts in `docker-compose.yml`
- **Permission errors**: Remove `:ro` flag from volumes
- **Slow reload**: Increase poll interval or check file watcher limits
```

**Status**: [ ] Not Started

---

#### Task 8.5: Document Hot-Reload in CLAUDE.md
**File**: `CLAUDE.md`
**Action**:
- Add to "Docker Deployment" section
- Explain volume mounting strategy

**Addition**:
```markdown
### Hot-Reload Configuration

**Volume Mounts for Development**:
```yaml
backend:
  volumes:
    - ./src:/app/src:ro          # Source code (hot-reload)
    - ./scripts:/app/scripts:ro  # Helper scripts
    - whisper-cache:/root/.cache/whisper  # Model cache (persistent)
    - whisper-uploads:/app/uploads        # Audio files (persistent)

frontend:
  volumes:
    - ./src/presentation/frontend/src:/app/src:ro  # Source code (hot-reload)
```

**Benefits**:
- No rebuild needed for code changes
- PyTorch and CUDA stay in image (20GB+ not affected)
- Faster development iteration

**Read-Only Mounts** (`:ro`):
- Prevents container from modifying host files
- Good security practice
- Remove if file watchers fail
```

**Status**: [ ] Not Started

---

### Phase 9: Feature 19 - Agent Code Refactoring (Tasks 51-60)

#### Task 9.1: Create Application Enhancement Directory
**Action**:
- Create `src/application/enhancement/` directory
- Create `__init__.py`

**Commands**:
```bash
mkdir -p src/application/enhancement
touch src/application/enhancement/__init__.py
```

**Status**: [ ] Not Started

---

#### Task 9.2: Create Infrastructure LLM Directory
**Action**:
- Create `src/infrastructure/llm/` directory
- Create `__init__.py`

**Commands**:
```bash
mkdir -p src/infrastructure/llm
touch src/infrastructure/llm/__init__.py
```

**Status**: [ ] Not Started

---

#### Task 9.3: Move Enhancement Agent to Application Layer
**Action**:
- Move `src/presentation/agent/enhancement_agent.py` → `src/application/enhancement/enhancement_agent.py`
- Git track: `git mv src/presentation/agent/enhancement_agent.py src/application/enhancement/enhancement_agent.py`

**Commands**:
```bash
git mv src/presentation/agent/enhancement_agent.py src/application/enhancement/enhancement_agent.py
```

**Status**: [ ] Not Started

---

#### Task 9.4: Move Prompts to Application Layer
**Action**:
- Move `src/presentation/agent/prompts.py` → `src/application/enhancement/prompts.py`
- Git track: `git mv src/presentation/agent/prompts.py src/application/enhancement/prompts.py`

**Commands**:
```bash
git mv src/presentation/agent/prompts.py src/application/enhancement/prompts.py
```

**Status**: [ ] Not Started

---

#### Task 9.5: Move LLM Client to Infrastructure Layer
**Action**:
- Move `src/presentation/agent/llm_client.py` → `src/infrastructure/llm/llm_client.py`
- Git track: `git mv src/presentation/agent/llm_client.py src/infrastructure/llm/llm_client.py`

**Commands**:
```bash
git mv src/presentation/agent/llm_client.py src/infrastructure/llm/llm_client.py
```

**Status**: [ ] Not Started

---

#### Task 9.6: Update Enhancement Agent Imports
**File**: `src/application/enhancement/enhancement_agent.py`
**Action**:
- Update import for llm_client (now in infrastructure)
- Update import for prompts (now in same directory)

**Changes**:
```python
# OLD
from .llm_client import LLMClient
from .prompts import ENHANCEMENT_SYSTEM_PROMPT, ENHANCEMENT_USER_PROMPT_TEMPLATE

# NEW
from ...infrastructure.llm.llm_client import LLMClient
from .prompts import ENHANCEMENT_SYSTEM_PROMPT, ENHANCEMENT_USER_PROMPT_TEMPLATE
```

**Status**: [ ] Not Started

---

#### Task 9.7: Update LLM Enhancement Service Imports
**File**: `src/infrastructure/services/llm_enhancement_service_impl.py`
**Action**:
- Update imports to use new paths

**Changes**:
```python
# OLD
from ...presentation.agent.llm_client import LLMClient
from ...presentation.agent.enhancement_agent import EnhancementAgent

# NEW
from ..llm.llm_client import LLMClient
from ...application.enhancement.enhancement_agent import EnhancementAgent
```

**Status**: [ ] Not Started

---

#### Task 9.8: Update __init__.py Files
**Files**:
- `src/application/enhancement/__init__.py`
- `src/infrastructure/llm/__init__.py`

**Action**:
- Add exports for public API

**Content** (`src/application/enhancement/__init__.py`):
```python
"""LLM transcription enhancement application logic"""
from .enhancement_agent import EnhancementAgent, EnhancementState
from .prompts import ENHANCEMENT_SYSTEM_PROMPT, ENHANCEMENT_USER_PROMPT_TEMPLATE

__all__ = [
    "EnhancementAgent",
    "EnhancementState",
    "ENHANCEMENT_SYSTEM_PROMPT",
    "ENHANCEMENT_USER_PROMPT_TEMPLATE",
]
```

**Content** (`src/infrastructure/llm/__init__.py`):
```python
"""LLM infrastructure - HTTP clients for local LLM APIs"""
from .llm_client import LLMClient

__all__ = ["LLMClient"]
```

**Status**: [ ] Not Started

---

#### Task 9.9: Remove Old Presentation Agent Directory
**Action**:
- Delete `src/presentation/agent/` directory (should be empty after moves)
- Verify with git status

**Commands**:
```bash
# Should be empty now
ls src/presentation/agent/
# Should only show __init__.py

# Remove directory
rm -rf src/presentation/agent/
# Or on Windows:
rmdir src\presentation\agent\ /s
```

**Status**: [ ] Not Started

---

#### Task 9.10: Search for Any Remaining Old Imports
**Action**:
- Search codebase for old import paths
- Update if any found

**Search**:
```bash
grep -r "from.*presentation.agent" src/
grep -r "import.*presentation.agent" src/
```

**Expected**: No matches (all updated)

**Status**: [ ] Not Started

---

#### Task 9.11: Update Tests (if any)
**Action**:
- Check if tests exist that import from presentation.agent
- Update test imports

**Search**:
```bash
find . -name "*test*.py" -type f -exec grep -l "presentation.agent" {} \;
```

**Status**: [ ] Not Started

---

#### Task 9.12: Test Agent Refactoring
**Action**:
- Restart backend: `python scripts/docker/stop.py && python scripts/docker/run.py`
- Test LLM enhancement via frontend
- Verify no import errors in logs

**Validation**:
- [ ] Backend starts without errors
- [ ] LLM enhancement still works
- [ ] No ImportError in logs
- [ ] Enhancement result identical to before

**Status**: [ ] Not Started

---

#### Task 9.13: Update CLAUDE.md Architecture Documentation
**File**: `CLAUDE.md`
**Action**:
- Update architecture diagrams
- Update file structure
- Document clean architecture rationale

**Updates**:
```markdown
### Backend Structure

```
src/
├── domain/                      # Pure business logic
│   ├── entities/
│   ├── repositories/
│   ├── services/              # LLMEnhancementService interface
│   └── exceptions/
│
├── application/                # Use cases and workflows
│   ├── use_cases/             # TranscribeAudioUseCase, EnhanceTranscriptionUseCase
│   ├── dto/
│   └── enhancement/           # LLM enhancement workflow
│       ├── enhancement_agent.py    # LangGraph agent
│       └── prompts.py             # System/user prompts
│
├── infrastructure/             # External implementations
│   ├── persistence/
│   ├── services/              # LLMEnhancementServiceImpl, WhisperService
│   ├── llm/                   # LLM infrastructure
│   │   └── llm_client.py      # OpenAI-compatible HTTP client
│   └── storage/
│
└── presentation/
    ├── api/                   # FastAPI routers, schemas
    └── frontend/              # Angular SPA
```

**Clean Architecture Note**:
- Enhancement agent moved from presentation to application (orchestration logic)
- LLM client in infrastructure (external HTTP dependency)
- Follows dependency rule: outer layers depend on inner, not vice versa
```

**Status**: [ ] Not Started

---

### Phase 10: Testing & Validation (Tasks 61-70)

#### Task 8.1: Full Docker Rebuild Test
**Action**:
- Clean all Docker resources: `python scripts/docker/clean.py --all`
- Set BuildKit: `$env:DOCKER_BUILDKIT=1`
- Rebuild: `python scripts/docker/rebuild.py`
- Measure build time

**Validation**:
- [ ] Backend builds successfully
- [ ] Frontend builds successfully
- [ ] All containers start healthy
- [ ] No errors in logs: `python scripts/docker/logs.py`

**Metrics**:
- Backend build time: `_____ seconds`
- Frontend build time: `_____ seconds`
- Improvement vs baseline: `_____% faster`

**Status**: [ ] Not Started

---

#### Task 8.2: Incremental Build Test (Cache Validation)
**Action**:
- Make minor code change (add comment)
- Rebuild: `docker-compose build backend`
- Verify cache hits in build output

**Expected**: Should see "CACHED" for dependency installation layers

**Status**: [ ] Not Started

---

#### Task 8.3: Test Backend Functionality
**Action**:
- Access API docs: http://localhost:8001/docs
- Upload audio file via frontend
- Transcribe with different models
- Verify LLM enhancement works
- Check database persistence

**Test Cases**:
- [ ] Upload MP3 file
- [ ] Upload WAV file
- [ ] Record audio in browser
- [ ] Transcribe with base model
- [ ] Transcribe with large model
- [ ] Re-transcribe with different model
- [ ] LLM enhancement toggle
- [ ] Audio playback
- [ ] Delete transcription
- [ ] View history

**Status**: [ ] Not Started

---

#### Task 8.4: Test Frontend Functionality
**Action**:
- Access frontend: http://localhost:4200
- Verify all UI features work
- Check console for errors

**Test Cases**:
- [ ] Upload form works
- [ ] Recording works
- [ ] Model selection dropdown
- [ ] LLM enhancement checkbox
- [ ] History view loads
- [ ] Detail view loads
- [ ] Model tabs switch correctly
- [ ] Audio player works
- [ ] Download button works
- [ ] Copy buttons work
- [ ] Delete confirmation popup

**Status**: [ ] Not Started

---

#### Task 8.5: Test Environment Variable Loading
**Action**:
- Verify backend loads from `src/presentation/api/.env`
- Verify frontend loads from `src/presentation/frontend/.env`
- Change values and restart to confirm

**Test**:
```bash
# Check backend env
docker exec whisper-backend env | grep DATABASE_URL
docker exec whisper-backend env | grep WHISPER_MODEL

# Check frontend env
docker exec whisper-frontend env | grep API_URL
```

**Status**: [ ] Not Started

---

#### Task 8.6: Test Model Cache Persistence
**Action**:
- Download model (e.g., large)
- Stop containers: `python scripts/docker/stop.py`
- Start containers: `python scripts/docker/run.py`
- Verify model not re-downloaded (check logs)

**Expected**: "Model 'large' found in cache"

**Status**: [ ] Not Started

---

#### Task 8.7: Test UV Performance (Build Time Comparison)
**Action**:
- Clear Docker cache: `docker builder prune --all`
- Build with UV: Measure time
- Compare to baseline (pip build time)

**Metrics**:
- UV build time: `_____ seconds`
- Pip baseline: `_____ seconds`
- Improvement: `_____x faster`

**Status**: [ ] Not Started

---

#### Task 8.8: Test All Python Scripts
**Action**:
- Run each script in scripts/ directory
- Verify no errors
- Verify Unicode displays correctly

**Scripts to Test**:
- [ ] scripts/docker/build.py
- [ ] scripts/docker/run.py
- [ ] scripts/docker/stop.py
- [ ] scripts/docker/logs.py
- [ ] scripts/docker/shell.py
- [ ] scripts/docker/clean.py
- [ ] scripts/docker/rebuild.py
- [ ] scripts/docker/preload_models.py
- [ ] scripts/setup/init_db.py
- [ ] scripts/setup/download_whisper_model.py
- [ ] scripts/setup/install_uv.py (new)
- [ ] scripts/server/run_backend.py
- [ ] scripts/server/run_frontend.py
- [ ] scripts/server/stop_all.py

**Status**: [ ] Not Started

---

#### Task 8.9: Test Cross-Platform Compatibility
**Action**:
- If possible, test on Linux (WSL or VM)
- Verify Docker builds work
- Verify scripts work

**Status**: [ ] Not Started (Optional)

---

#### Task 8.10: Performance Benchmarks
**Action**:
- Document final build times
- Document runtime performance
- Compare to baseline

**Metrics Table**:

| Metric | Baseline (pip) | Optimized (uv) | Improvement |
|--------|---------------|----------------|-------------|
| Backend build (cold) | ___s | ___s | ___% |
| Backend build (warm) | ___s | ___s | ___% |
| Frontend build (cold) | ___s | ___s | ___% |
| Frontend build (warm) | ___s | ___s | ___% |
| Total docker-compose up | ___s | ___s | ___% |
| Transcription latency | ___s | ___s | ___% |

**Status**: [ ] Not Started

---

### Phase 9: Documentation Updates (Tasks 56-60)

#### Task 9.1: Update README.md - Installation Section
**File**: `README.md`
**Action**:
- Update installation instructions for UV
- Update .env configuration steps
- Update requirements.txt path
- Update Docker build instructions

**Sections to Update**:
1. System Requirements (add UV)
2. Installation steps
3. Configuration (.env files)
4. Docker deployment
5. Performance notes (UV benefits)

**Status**: [ ] Not Started

---

#### Task 9.2: Update CLAUDE.md - Architecture Section
**File**: `CLAUDE.md`
**Action**:
- Update file structure diagram
- Update Docker architecture section
- Update development commands
- Add UV usage notes

**Sections to Update**:
```markdown
### Backend Structure
src/presentation/api/
├── .env                       # Backend environment config
├── .env.example              # Backend env template
├── requirements.txt          # Python dependencies
├── Dockerfile               # Backend Docker build
└── ...

### Frontend Structure
src/presentation/frontend/
├── .env                      # Frontend environment config
├── .env.example             # Frontend env template
├── Dockerfile              # Frontend Docker build
└── ...

### Development Commands

#### Using UV (Recommended)
```bash
# Install UV
python scripts/setup/install_uv.py

# Install dependencies (10-100x faster than pip)
uv pip install -r src/presentation/api/requirements.txt
```

#### Using pip (Fallback)
```bash
pip install -r src/presentation/api/requirements.txt
```
```

**Status**: [ ] Not Started

---

#### Task 9.3: Update Docker Documentation
**File**: `README.md` and/or `docs/DOCKER.md` (if exists)
**Action**:
- Document BuildKit requirement
- Document cache strategy
- Document .env file structure
- Update troubleshooting section

**Add Section**:
```markdown
## Docker Build Optimization

This project uses Docker BuildKit for optimized builds:

### Enable BuildKit
```bash
# Windows PowerShell
$env:DOCKER_BUILDKIT=1

# Linux/Mac
export DOCKER_BUILDKIT=1
```

### Build Caching
- **UV Cache**: Python packages cached in BuildKit mounts (~10-100x faster installs)
- **APT Cache**: System packages cached in BuildKit mounts
- **NPM Cache**: Node modules cached in BuildKit mounts
- **Whisper Models**: Persisted in named Docker volume `whisper-cache`

### Performance
- Cold build: ~X minutes
- Warm build (cached dependencies): ~X seconds
- Incremental rebuild: ~X seconds
```

**Status**: [ ] Not Started

---

#### Task 9.4: Create UV Migration Guide
**File**: `docs/UV_MIGRATION.md` (new)
**Action**:
- Document migration from pip to UV
- Installation instructions
- Comparison benchmarks
- Troubleshooting

**Content**:
```markdown
# UV Package Manager Migration Guide

## What is UV?
UV is a ultra-fast Python package installer written in Rust, designed as a drop-in replacement for pip.

## Performance Benefits
- 10-100x faster than pip
- Parallel downloads
- Global package cache
- Zero-copy installations (when possible)

## Installation

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/Mac
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Verify
```bash
uv --version
```

## Usage

UV is a drop-in replacement for pip. Simply replace `pip` with `uv pip`:

```bash
# Install dependencies
uv pip install -r src/presentation/api/requirements.txt

# Install PyTorch with CUDA
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install single package
uv pip install package-name

# Uninstall
uv pip uninstall package-name
```

## Docker Integration

UV is integrated into our Docker builds for maximum performance. No action needed.

## Troubleshooting

### UV not found
Make sure UV is in your PATH. Restart your terminal after installation.

### Slower than expected
UV's speed advantage is most apparent with:
- Large dependency trees
- Repeated installations (cache hits)
- Parallel downloads

First install is still fast, but subsequent installs are 100x+ faster.

## Fallback to pip

If you encounter issues with UV, you can always fall back to pip:
```bash
pip install -r src/presentation/api/requirements.txt
```

Our scripts automatically detect UV availability and use it when present.
```

**Status**: [ ] Not Started

---

#### Task 9.5: Update this Plan with Final Results
**File**: `plans/DOCKER_OPTIMIZATION_AND_STRUCTURE_PLAN.md`
**Action**:
- Fill in all performance metrics
- Mark all tasks complete
- Add lessons learned section
- Document any issues encountered

**Status**: [ ] Not Started

---

### Phase 10: Cleanup & Finalization (Tasks 61-65)

#### Task 10.1: Remove Deprecated Files
**Files**:
- `.env.docker.deprecated` (if not needed as reference)
- Any backup files created during migration

**Action**:
- Review deprecated files
- Move to archive or delete
- Update .gitignore

**Status**: [ ] Not Started

---

#### Task 10.2: Update .gitignore Final Review
**File**: `.gitignore`
**Action**:
- Ensure all new .env files are ignored
- Ensure .env.example files are tracked
- Remove obsolete patterns

**Status**: [ ] Not Started

---

#### Task 10.3: Git Commit - Phase by Phase
**Action**:
- Commit each phase separately for clear history
- Use descriptive commit messages

**Commit Strategy**:
```bash
# After Phase 2 (UV)
git add .
git commit -m "Feat: Migrate to UV package manager for 10-100x faster builds

- Add UV installation in Dockerfile builder stage
- Implement BuildKit cache mounts for /root/.cache/uv
- Add npm cache mount for frontend
- Create install_uv.py setup script
- Update all scripts to detect and use UV when available

Performance improvement: XX% faster builds on incremental rebuilds

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After Phase 3 (Requirements.txt)
git add .
git commit -m "Refactor: Move requirements.txt to backend folder

- Move requirements.txt to src/presentation/api/
- Update Dockerfile, README.md, CLAUDE.md references
- Update all scripts that reference requirements path

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After Phase 4 (Dockerfile relocation)
git add .
git commit -m "Refactor: Move backend Dockerfile to API folder

- Move Dockerfile to src/presentation/api/Dockerfile
- Update docker-compose.yml build context
- Update documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After Phase 5 (.env separation)
git add .
git commit -m "Feat: Implement separate environment files for better isolation

- Create src/presentation/api/.env for backend configs
- Create src/presentation/frontend/.env for frontend configs
- Update docker-compose.yml to use multiple env_file
- Deprecate .env.docker
- Update documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After Phase 6 (Model cache)
git add .
git commit -m "Fix: Enhance Whisper model cache detection for all versions

- Update model_exists() to check all Whisper version variants
- Check large-v1/v2/v3, turbo variants, .en variants
- Consistent detection across all scripts

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After Phase 7 (Unicode)
git add .
git commit -m "Fix: Handle Unicode characters in all Python scripts for Windows

- Add UTF-8 encoding fix for Windows console
- Fix 9 scripts in docker/, setup/, maintenance/, migrations/
- Prevents UnicodeEncodeError on Windows console

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# After Phase 9 (Documentation)
git add .
git commit -m "Docs: Update documentation for project structure changes

- Update README.md for UV, new .env structure, file paths
- Update CLAUDE.md architecture diagrams and commands
- Create UV_MIGRATION.md guide
- Update Docker documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Status**: [ ] Not Started

---

#### Task 10.4: Final Integration Test
**Action**:
- Clean slate: `python scripts/docker/clean.py --all`
- Fresh clone simulation: Delete and re-clone repo (or test on different machine)
- Follow README.md instructions from scratch
- Verify everything works

**Validation**:
- [ ] Can clone and setup project from README
- [ ] Docker build succeeds
- [ ] All containers start
- [ ] Frontend accessible
- [ ] Backend API works
- [ ] Transcription end-to-end works

**Status**: [ ] Not Started

---

#### Task 10.5: Create Summary Report
**File**: `plans/DOCKER_OPTIMIZATION_SUMMARY.md` (new)
**Action**:
- Summarize all changes
- Document performance improvements
- List breaking changes (if any)
- Provide migration instructions for existing deployments

**Content**:
```markdown
# Docker Optimization and Structure Enhancement - Summary Report

## Date Completed
2026-01-XX

## Features Implemented
✅ Feature 11: Docker build performance (BuildKit cache mounts)
✅ Feature 12: Backend Dockerfile relocation
✅ Feature 13: Separate environment files
✅ Feature 14: Requirements.txt relocation
✅ Feature 15: UV package manager migration
✅ Feature 16: Enhanced model cache detection
✅ Feature 17: Unicode character handling

## Performance Improvements
- Backend build time: XX% faster (cold), XX% faster (warm)
- Frontend build time: XX% faster (cold), XX% faster (warm)
- Package installation: 10-100x faster with UV
- Developer experience: Improved with better file organization

## Breaking Changes
⚠️ **Environment Variables**: .env files moved to component folders
⚠️ **BuildKit Required**: Docker builds now require DOCKER_BUILDKIT=1
⚠️ **File Paths Changed**: requirements.txt and Dockerfile moved

## Migration Instructions for Existing Deployments

### Step 1: Update .env files
```bash
# Create backend .env
cp .env.docker src/presentation/api/.env
# Edit src/presentation/api/.env - remove frontend-specific vars

# Create frontend .env
echo "API_URL=http://localhost:8001/api/v1" > src/presentation/frontend/.env
```

### Step 2: Enable BuildKit
```bash
# Windows
$env:DOCKER_BUILDKIT=1

# Linux
export DOCKER_BUILDKIT=1
```

### Step 3: Rebuild
```bash
python scripts/docker/rebuild.py
```

## Files Changed
- Added: 15 files
- Modified: 20 files
- Removed: 1 file (.env.docker)

## Lessons Learned
- UV significantly improves build performance
- BuildKit cache mounts are effective for Docker optimization
- Nested .env files improve project organization
- Unicode handling is critical for cross-platform scripts

## Next Steps
- Monitor build performance in CI/CD
- Consider uv for other Python projects
- Explore additional BuildKit optimizations
```

**Status**: [ ] Not Started

---

## Testing Strategy

### Unit Testing
- No unit tests needed (infrastructure changes only)

### Integration Testing
- Docker build succeeds
- Containers start and communicate
- Environment variables loaded correctly
- Model cache detection works

### End-to-End Testing
- Full transcription workflow
- Frontend to backend communication
- Database persistence
- LLM enhancement

### Performance Testing
- Build time measurements
- Cache hit rate
- Incremental build speed

### Cross-Platform Testing
- Windows (primary)
- Linux (Docker containers)
- WSL (optional)

---

## Documentation Updates

### Files to Update
1. ✅ `README.md` - Installation, configuration, Docker instructions
2. ✅ `CLAUDE.md` - Architecture, file structure, commands
3. ✅ `plans/DOCKER_OPTIMIZATION_AND_STRUCTURE_PLAN.md` - This plan
4. ✅ `docs/UV_MIGRATION.md` - New guide for UV
5. ✅ `plans/DOCKER_OPTIMIZATION_SUMMARY.md` - Final summary

### Documentation Checklist
- [ ] Installation instructions updated for UV
- [ ] Configuration section updated for new .env structure
- [ ] File paths corrected (requirements.txt, Dockerfile)
- [ ] Docker BuildKit requirement documented
- [ ] Performance benchmarks included
- [ ] Migration guide for existing users
- [ ] Troubleshooting section expanded

---

## Progress Tracking

### Overall Progress: 0% Complete

### Phase 1: Preparation (0/5 tasks)
- [ ] Task 1.1: Enable Docker BuildKit
- [ ] Task 1.2: Create Plans Directory Backup
- [ ] Task 1.3: Research UV Installation
- [ ] Task 1.4: Backup Current Configuration
- [ ] Task 1.5: Test Current Docker Setup

### Phase 2: UV Migration (0/10 tasks)
- [ ] Task 2.1: Install UV Locally
- [ ] Task 2.2: Update Backend Dockerfile (Builder)
- [ ] Task 2.3: Update Backend Dockerfile (Runtime)
- [ ] Task 2.4: Update Frontend Dockerfile
- [ ] Task 2.5: Update Docker Compose
- [ ] Task 2.6: Test UV Docker Build
- [ ] Task 2.7: Update Scripts for UV
- [ ] Task 2.8: Create UV Installation Script
- [ ] Task 2.9: Test UV with Requirements
- [ ] Task 2.10: Update Requirements Comments

### Phase 3: Requirements.txt Relocation (0/7 tasks)
- [ ] Task 3.1: Move Requirements.txt
- [ ] Task 3.2: Update Dockerfile Path
- [ ] Task 3.3: Update README.md
- [ ] Task 3.4: Update CLAUDE.md
- [ ] Task 3.5: Update Scripts
- [ ] Task 3.6: Update .gitignore
- [ ] Task 3.7: Test Requirements Path

### Phase 4: Dockerfile Relocation (0/6 tasks)
- [ ] Task 4.1: Move Dockerfile
- [ ] Task 4.2: Update Context Paths
- [ ] Task 4.3: Update docker-compose.yml
- [ ] Task 4.4: Update Docker Scripts
- [ ] Task 4.5: Update Documentation
- [ ] Task 4.6: Test Dockerfile Relocation

### Phase 5: Separate .env Files (0/13 tasks)
- [ ] Task 5.1: Create Backend .env.example
- [ ] Task 5.2: Create Backend .env
- [ ] Task 5.3: Create Frontend .env.example
- [ ] Task 5.4: Create Frontend .env
- [ ] Task 5.5: Update .gitignore
- [ ] Task 5.6: Update docker-compose.yml
- [ ] Task 5.7: Update Backend Loading
- [ ] Task 5.8: Update Frontend Loading
- [ ] Task 5.9: Update README.md
- [ ] Task 5.10: Update CLAUDE.md
- [ ] Task 5.11: Deprecate .env.docker
- [ ] Task 5.12: Create Migration Script
- [ ] Task 5.13: Test .env Configuration

### Phase 6: Model Cache Detection (0/5 tasks)
- [ ] Task 6.1: Research Model Versions
- [ ] Task 6.2: Update preload_models.py
- [ ] Task 6.3: Check WhisperService
- [ ] Task 6.4: Verify Download Logic
- [ ] Task 6.5: Test Cache Detection

### Phase 7: Unicode Handling (0/10 tasks)
- [ ] Task 7.1: Create Unicode Fix Template
- [ ] Task 7.2: Fix clean.py
- [ ] Task 7.3: Fix rebuild.py
- [ ] Task 7.4: Fix cleanup_orphaned_transcriptions.py
- [ ] Task 7.5: Fix init_db.py
- [ ] Task 7.6: Fix download_whisper_model.py
- [ ] Task 7.7: Fix migrate_add_processing_time.py
- [ ] Task 7.8: Fix migrate_add_model_column.py
- [ ] Task 7.9: Scan for Missed Scripts
- [ ] Task 7.10: Test All Scripts

### Phase 8: Hot-Reload Verification (0/5 tasks)
- [ ] Task 8.1: Test Backend Hot-Reload
- [ ] Task 8.2: Test Frontend Hot-Reload
- [ ] Task 8.3: Investigate Read-Only Volume
- [ ] Task 8.4: Document in README.md
- [ ] Task 8.5: Document in CLAUDE.md

### Phase 9: Agent Refactoring (0/13 tasks)
- [ ] Task 9.1: Create Application Enhancement Directory
- [ ] Task 9.2: Create Infrastructure LLM Directory
- [ ] Task 9.3: Move Enhancement Agent
- [ ] Task 9.4: Move Prompts
- [ ] Task 9.5: Move LLM Client
- [ ] Task 9.6: Update Enhancement Agent Imports
- [ ] Task 9.7: Update LLM Service Imports
- [ ] Task 9.8: Update __init__.py Files
- [ ] Task 9.9: Remove Old Agent Directory
- [ ] Task 9.10: Search for Remaining Imports
- [ ] Task 9.11: Update Tests
- [ ] Task 9.12: Test Agent Refactoring
- [ ] Task 9.13: Update CLAUDE.md

### Phase 10: Testing & Validation (0/10 tasks)
- [ ] Task 10.1: Full Rebuild Test
- [ ] Task 10.2: Incremental Build Test
- [ ] Task 10.3: Backend Functionality
- [ ] Task 10.4: Frontend Functionality
- [ ] Task 10.5: Environment Loading
- [ ] Task 10.6: Model Cache Persistence
- [ ] Task 10.7: UV Performance Test
- [ ] Task 10.8: Python Scripts Test
- [ ] Task 10.9: Cross-Platform Test
- [ ] Task 10.10: Performance Benchmarks

### Phase 11: Documentation (0/5 tasks)
- [ ] Task 11.1: Update README.md
- [ ] Task 11.2: Update CLAUDE.md
- [ ] Task 11.3: Update Docker Docs
- [ ] Task 11.4: Create UV Guide
- [ ] Task 11.5: Update This Plan

### Phase 12: Cleanup & Finalization (0/5 tasks)
- [ ] Task 12.1: Remove Deprecated Files
- [ ] Task 12.2: Final .gitignore Review
- [ ] Task 12.3: Git Commits (Phase by Phase)
- [ ] Task 12.4: Final Integration Test
- [ ] Task 12.5: Create Summary Report

---

## Risk Assessment

### High Risk
- **BuildKit Compatibility**: Older Docker versions may not support BuildKit
  - *Mitigation*: Check Docker version in Phase 1, document minimum version

- **Environment Variable Loading**: New .env paths might break existing deployments
  - *Mitigation*: Create migration guide, test thoroughly in Phase 5

### Medium Risk
- **UV Compatibility**: Some packages might have issues with UV
  - *Mitigation*: Test with current requirements.txt in Phase 2, maintain pip fallback

- **File Path Changes**: Scripts might break with new paths
  - *Mitigation*: Thorough testing in Phase 3-4, update all references

### Low Risk
- **Unicode Handling**: Already tested pattern in 2 scripts
  - *Mitigation*: Use consistent fix across all scripts

- **Model Cache Detection**: Logic already partially implemented
  - *Mitigation*: Extend existing working code

---

## Success Criteria

### Performance
- ✅ 40%+ faster incremental Docker builds
- ✅ 10x+ faster package installation with UV
- ✅ Build cache hit rate >80% on unchanged dependencies

### Functionality
- ✅ All existing features work unchanged
- ✅ Transcription workflow end-to-end
- ✅ Environment variables load correctly
- ✅ Model cache detection works for all versions

### Quality
- ✅ No errors in Docker build logs
- ✅ No errors in container logs
- ✅ No UnicodeEncodeError in scripts
- ✅ All scripts execute successfully

### Documentation
- ✅ README.md accurately reflects new structure
- ✅ CLAUDE.md updated with all changes
- ✅ Migration guide provided
- ✅ Performance metrics documented

---

## Notes

### UV Package Manager
- Drop-in replacement for pip
- Written in Rust for maximum performance
- Compatible with all pip commands (uv pip install, uv pip uninstall, etc.)
- Global cache reduces disk usage
- Parallel downloads significantly faster

### Docker BuildKit
- Cache mounts persist between builds (not in image)
- Requires DOCKER_BUILDKIT=1 environment variable
- Supported in Docker 18.09+
- More efficient than traditional caching

### Environment Files
- Backend: Database, API, Whisper, LLM configs
- Frontend: API URL only (Angular doesn't read .env at runtime)
- Docker Compose loads both files per service

### Model Cache
- Whisper models have version suffixes (large-v3.pt)
- Also has language-specific variants (.en.pt)
- Cache detection should accept any valid version
- Prevents unnecessary re-downloads

---

## Appendix

### References
1. [UV Documentation](https://docs.astral.sh/uv/)
2. [Docker BuildKit Documentation](https://docs.docker.com/build/buildkit/)
3. [Whisper Model Naming](https://github.com/openai/whisper)
4. [Production Python Docker with UV](https://hynek.me/articles/docker-uv/)
5. [UV vs pip Benchmark](https://realpython.com/uv-vs-pip/)

### Version Information
- Docker: 20.10+ (BuildKit support)
- UV: 0.9.21 (pinned in Dockerfile)
- Python: 3.10
- Node: 18
- CUDA: 12.8

---

**End of Plan**
