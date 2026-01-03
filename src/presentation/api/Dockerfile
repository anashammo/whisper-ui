# ============================================================================
# Stage 1: Builder - Install dependencies with UV and BuildKit caching
# ============================================================================
# Using CUDA 12.8 with cuDNN 9 for RTX 5090 (Blackwell architecture, sm_120)
# CUDA 12.8+ is required for full sm_120 compute capability support
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 AS builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building Python packages with BuildKit cache
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

# Install UV package manager (pinned version for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /uvx /bin/

# Set UV environment variables for optimal Docker builds
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300

# Set working directory
WORKDIR /build

# Copy requirements file from backend folder
COPY src/presentation/api/requirements.txt .

# Install PyTorch with CUDA 12.8 support FIRST (before other packages)
# CUDA 12.8 wheels provide full support for RTX 5090 (Blackwell, sm_120)
# Using UV with BuildKit cache mount for fast installs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install remaining Python dependencies with UV and BuildKit cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal runtime image with GPU support
# ============================================================================
# CUDA 12.8 runtime with cuDNN 9 for RTX 5090 (Blackwell, sm_120)
FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies with BuildKit cache
# Note: FFmpeg not needed - PyAV (bundled with faster-whisper) includes FFmpeg libraries
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy model preload script
COPY scripts/docker/preload_models.py /usr/local/bin/preload_models.py
RUN chmod +x /usr/local/bin/preload_models.py

# Create necessary directories
# - /app/uploads: uploaded audio files
# - /root/.cache/huggingface: faster-whisper model cache (HuggingFace Hub)
RUN mkdir -p /app/uploads /root/.cache/huggingface

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:$PATH"

# Expose backend port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

# Create entrypoint script that runs model preload before starting app
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting faster-whisper Backend Container..."\n\
echo ""\n\
\n\
# Run model preload script\n\
echo "Running model pre-download check..."\n\
python3 /usr/local/bin/preload_models.py --models ${PRELOAD_MODELS:-base} ${FORCE_DOWNLOAD:+--force}\n\
echo ""\n\
\n\
# Start the application\n\
echo "Starting FastAPI application..."\n\
exec python3 -m uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8001\n\
' > /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

# Use entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
