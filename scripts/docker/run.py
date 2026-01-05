#!/usr/bin/env python3
"""Run Docker Compose services

Starts all services by default (including ngrok tunnels):
- postgres: PostgreSQL database (container: whisper-postgres)
- backend: FastAPI + Whisper API (container: whisper-backend)
- frontend: Angular SPA (container: whisper-frontend)
- ngrok-backend: Ngrok tunnel for backend (container: ngrok-whisper-backend)
- ngrok-frontend: Ngrok tunnel for frontend (container: ngrok-whisper-frontend)
- ngrok-llm: Ngrok tunnel for LLM service (container: ngrok-whisper-llm)

Usage:
    python scripts/docker/run.py              # Start all services (including ngrok)
    python scripts/docker/run.py --no-ngrok   # Start without ngrok tunnels
    python scripts/docker/run.py --build      # Build and start
    python scripts/docker/run.py -d           # Start detached

Note: Ngrok requires NGROK_AUTHTOKEN in src/presentation/api/.env
"""
import subprocess
import sys
import argparse
import os

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Set Docker Compose project name for consistent container naming in Docker Desktop
os.environ["COMPOSE_PROJECT_NAME"] = "whisper-ui"


def main():
    parser = argparse.ArgumentParser(description="Run Docker Compose services")
    parser.add_argument("--build", action="store_true", help="Build images before starting")
    parser.add_argument("--detach", "-d", action="store_true", help="Run in detached mode")
    parser.add_argument("--no-ngrok", action="store_true", help="Exclude ngrok tunnels (start core services only)")

    args = parser.parse_args()

    # Base command with env file
    cmd = ["docker-compose", "--env-file", "src/presentation/api/.env"]

    # Add ngrok profile by default (unless --no-ngrok specified)
    if not args.no_ngrok:
        cmd.extend(["--profile", "ngrok"])
        print("Starting all services including ngrok tunnels...")
        print("  Backend tunnel:  https://anas-hammo-whisper-backend.ngrok.dev")
        print("  Frontend tunnel: https://anas-hammo-whisper-frontend.ngrok.dev")
        print("  LLM tunnel:      https://anas-hammo-whisper-llm.ngrok.dev")
        print("\nNgrok Web UI:")
        print("  Backend:  http://localhost:4050")
        print("  Frontend: http://localhost:4051")
        print("  LLM:      http://localhost:4052")
    else:
        print("Starting core services only (postgres, backend, frontend)...")
        print("Use without --no-ngrok to include ngrok tunnels")

    cmd.append("up")

    # Add options
    if args.build:
        cmd.append("--build")

    if args.detach:
        cmd.append("-d")

    # Run command
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
