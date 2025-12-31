# ============================================================================
# Stage 1: Builder - Install dependencies and build Python packages
# ============================================================================
FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 AS builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel
RUN python3 -m pip install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /build

# Copy requirements file
COPY requirements.txt .

# Install PyTorch with CUDA 12.8 support FIRST (before other packages)
# This ensures CUDA-enabled PyTorch with RTX 5090 support (sm_120) is installed
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal runtime image with GPU support
# ============================================================================
FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
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
RUN mkdir -p /app/uploads /root/.cache/whisper

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
echo "Starting Whisper Backend Container..."\n\
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
