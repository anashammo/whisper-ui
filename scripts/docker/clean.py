#!/usr/bin/env python3
"""Clean up Docker resources

Cleans up all services:
- postgres: PostgreSQL database (container: whisper-postgres)
- backend: FastAPI + Whisper API (container: whisper-backend)
- frontend: Angular SPA (container: whisper-frontend)
- ngrok-backend: Ngrok tunnel for backend (container: ngrok-whisper-backend)
- ngrok-frontend: Ngrok tunnel for frontend (container: ngrok-whisper-frontend)
- ngrok-llm: Ngrok tunnel for LLM service (container: ngrok-whisper-llm)

Usage:
    python scripts/docker/clean.py             # Stop and remove containers
    python scripts/docker/clean.py --images    # Remove images only
    python scripts/docker/clean.py --volumes   # Remove volumes (deletes data)
    python scripts/docker/clean.py --all       # Remove everything (WARNING!)
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
    parser = argparse.ArgumentParser(description="Clean up Docker resources")
    parser.add_argument("--all", action="store_true",
                       help="Remove images and volumes (WARNING: deletes everything)")
    parser.add_argument("--images", action="store_true", help="Remove images only")
    parser.add_argument("--volumes", action="store_true", help="Remove volumes only")

    args = parser.parse_args()

    # Env file for docker-compose
    env_file = ["--env-file", "src/presentation/api/.env"]

    if args.all:
        print("WARNING: This will remove all containers, images, and volumes!")
        print("All data will be deleted!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

        # Stop and remove containers and volumes (include ngrok profile)
        subprocess.run(["docker-compose"] + env_file + ["--profile", "ngrok", "down", "-v"])

        # Remove images (only backend/frontend, ngrok uses Docker Hub image)
        subprocess.run(["docker", "rmi", "whisper-backend", "whisper-frontend"],
                      stderr=subprocess.DEVNULL)

        print("[OK] Cleanup complete!")

    elif args.images:
        print("Removing Docker images...")
        subprocess.run(["docker", "rmi", "whisper-backend", "whisper-frontend"],
                      stderr=subprocess.DEVNULL)
        print("[OK] Images removed!")

    elif args.volumes:
        print("WARNING: This will remove all volumes and delete data!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled.")
            sys.exit(0)

        subprocess.run(["docker-compose"] + env_file + ["--profile", "ngrok", "down", "-v"])
        print("[OK] Volumes removed!")

    else:
        # Just stop and remove containers (default) - include ngrok profile
        subprocess.run(["docker-compose"] + env_file + ["--profile", "ngrok", "down"])
        print("[OK] Containers stopped and removed!")


if __name__ == "__main__":
    main()
