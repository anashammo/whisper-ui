#!/usr/bin/env python3
"""Open shell in running container

Available services:
- backend: FastAPI + Whisper API (bash)
- frontend: Angular SPA (sh)
- postgres: PostgreSQL database (sh)
- ngrok-whisper-backend: Ngrok tunnel for backend (sh)
- ngrok-whisper-frontend: Ngrok tunnel for frontend (sh)
- ngrok-whisper-llm: Ngrok tunnel for LLM service (sh)

Usage:
    python scripts/docker/shell.py backend     # Open bash in backend
    python scripts/docker/shell.py postgres    # Open sh in postgres
"""
import subprocess
import sys
import argparse

# Container name and shell mapping
CONTAINER_MAP = {
    "backend": ("whisper-backend", "bash"),
    "frontend": ("whisper-frontend", "sh"),
    "postgres": ("whisper-postgres", "sh"),
    "ngrok-whisper-backend": ("ngrok-whisper-backend", "sh"),
    "ngrok-whisper-frontend": ("ngrok-whisper-frontend", "sh"),
    "ngrok-whisper-llm": ("ngrok-whisper-llm", "sh")
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
