#!/usr/bin/env python3
"""Stop Docker Compose services

Stops all services including:
- postgres: PostgreSQL database (container: whisper-postgres)
- backend: FastAPI + Whisper API (container: whisper-backend)
- frontend: Angular SPA (container: whisper-frontend)
- ngrok-backend: Ngrok tunnel for backend (container: ngrok-whisper-backend)
- ngrok-frontend: Ngrok tunnel for frontend (container: ngrok-whisper-frontend)
- ngrok-llm: Ngrok tunnel for LLM service (container: ngrok-whisper-llm)

Usage:
    python scripts/docker/stop.py              # Stop all services
    python scripts/docker/stop.py -v           # Stop and remove volumes (WARNING: deletes data)
    python scripts/docker/stop.py --ngrok-only # Stop only ngrok tunnels
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
    parser = argparse.ArgumentParser(description="Stop Docker Compose services")
    parser.add_argument("--remove-volumes", "-v", action="store_true",
                       help="Remove volumes as well (WARNING: deletes data)")
    parser.add_argument("--ngrok-only", action="store_true",
                       help="Stop only ngrok tunnel services")

    args = parser.parse_args()

    # Env file for docker-compose
    env_file = ["--env-file", "src/presentation/api/.env"]

    if args.ngrok_only:
        # Stop only ngrok containers by name
        print("Stopping ngrok tunnel services...")
        cmd = ["docker", "stop",
               "ngrok-whisper-backend",
               "ngrok-whisper-frontend",
               "ngrok-whisper-llm"]
        subprocess.run(cmd, stderr=subprocess.DEVNULL)
        print("[OK] Ngrok tunnels stopped!")
        sys.exit(0)

    # Stop all services (with profile to include ngrok if running)
    cmd = ["docker-compose"] + env_file + ["--profile", "ngrok", "down"]

    if args.remove_volumes:
        print("WARNING: This will remove all volumes and delete data!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)
        cmd.append("-v")

    print("Stopping all services...")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
