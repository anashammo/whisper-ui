#!/usr/bin/env python3
"""Rebuild and restart Docker containers

Rebuilds all services by default (including ngrok tunnels):
- postgres: PostgreSQL database (container: whisper-postgres)
- backend: FastAPI + Whisper API (container: whisper-backend)
- frontend: Angular SPA (container: whisper-frontend)
- ngrok-backend: Ngrok tunnel for backend (container: ngrok-whisper-backend)
- ngrok-frontend: Ngrok tunnel for frontend (container: ngrok-whisper-frontend)
- ngrok-llm: Ngrok tunnel for LLM service (container: ngrok-whisper-llm)

Usage:
    python scripts/docker/rebuild.py             # Rebuild all services (including ngrok)
    python scripts/docker/rebuild.py --no-ngrok  # Rebuild without ngrok tunnels

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
    parser = argparse.ArgumentParser(description="Rebuild and restart Docker containers")
    parser.add_argument("--no-ngrok", action="store_true", help="Exclude ngrok tunnels (rebuild core services only)")

    args = parser.parse_args()

    # Env file for docker-compose
    env_file = ["--env-file", "src/presentation/api/.env"]

    print("Stopping containers...")
    subprocess.run(["docker-compose"] + env_file + ["--profile", "ngrok", "down"])

    print("\nRebuilding images...")
    result = subprocess.run(["docker-compose"] + env_file + ["build"])

    if result.returncode != 0:
        print("\n[X] Build failed!")
        sys.exit(1)

    print("\nStarting containers...")

    # Base command with env file
    cmd = ["docker-compose"] + env_file

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

    cmd.extend(["up", "-d"])

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n[OK] Rebuild and restart complete!")
        print("\nView logs with: python scripts/docker/logs.py -f")
    else:
        print("\n[X] Failed to start containers!")
        sys.exit(1)


if __name__ == "__main__":
    main()
