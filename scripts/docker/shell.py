#!/usr/bin/env python3
"""Open shell in running container

Available services (use service names, maps to container names):
- backend: FastAPI + Whisper API (container: whisper-backend, shell: bash)
- frontend: Angular SPA (container: whisper-frontend, shell: sh)
- postgres: PostgreSQL database (container: whisper-postgres, shell: sh)
- ngrok-backend: Ngrok tunnel for backend (container: ngrok-whisper-backend, shell: sh)
- ngrok-frontend: Ngrok tunnel for frontend (container: ngrok-whisper-frontend, shell: sh)
- ngrok-llm: Ngrok tunnel for LLM service (container: ngrok-whisper-llm, shell: sh)

Usage:
    python scripts/docker/shell.py backend   # Open bash in backend container
    python scripts/docker/shell.py postgres  # Open sh in postgres container
"""
import subprocess
import sys
import argparse
import os

# Set Docker Compose project name for consistent container naming in Docker Desktop
os.environ["COMPOSE_PROJECT_NAME"] = "whisper-ui"

# Service name to (container name, shell) mapping
CONTAINER_MAP = {
    "backend": ("whisper-backend", "bash"),
    "frontend": ("whisper-frontend", "sh"),
    "postgres": ("whisper-postgres", "sh"),
    "ngrok-backend": ("ngrok-whisper-backend", "sh"),
    "ngrok-frontend": ("ngrok-whisper-frontend", "sh"),
    "ngrok-llm": ("ngrok-whisper-llm", "sh")
}


def main():
    parser = argparse.ArgumentParser(description="Open shell in running container")
    parser.add_argument("service", choices=list(CONTAINER_MAP.keys()),
                       help="Service to open shell in")

    args = parser.parse_args()

    container_name, shell = CONTAINER_MAP[args.service]

    cmd = ["docker", "exec", "-it", container_name, shell]

    print(f"Opening {shell} in {container_name}...")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
