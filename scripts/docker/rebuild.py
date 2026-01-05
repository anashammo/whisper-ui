#!/usr/bin/env python3
"""Rebuild and restart Docker containers

Rebuilds core services:
- postgres: PostgreSQL database
- backend: FastAPI + Whisper API
- frontend: Angular SPA

Optional ngrok tunnels (use --ngrok flag):
- ngrok-whisper-backend: Ngrok tunnel for backend
- ngrok-whisper-frontend: Ngrok tunnel for frontend
- ngrok-whisper-llm: Ngrok tunnel for LLM service

Usage:
    python scripts/docker/rebuild.py           # Rebuild and restart core services
    python scripts/docker/rebuild.py --ngrok   # Rebuild with ngrok tunnels

Note: Ngrok requires NGROK_AUTHTOKEN environment variable to be set.
"""
import subprocess
import sys
import argparse

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Rebuild and restart Docker containers")
    parser.add_argument("--ngrok", action="store_true", help="Include ngrok tunnels (requires NGROK_AUTHTOKEN)")

    args = parser.parse_args()

    print("Stopping containers...")
    subprocess.run(["docker-compose", "down"])

    print("\nRebuilding images...")
    result = subprocess.run(["docker-compose", "build"])

    if result.returncode != 0:
        print("\n[X] Build failed!")
        sys.exit(1)

    print("\nStarting containers...")

    # Base command
    cmd = ["docker-compose"]

    # Add profile if ngrok requested
    if args.ngrok:
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
        print("Starting core services (postgres, backend, frontend)...")
        print("Use --ngrok flag to include ngrok tunnels")

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
