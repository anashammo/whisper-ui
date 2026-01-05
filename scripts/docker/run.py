#!/usr/bin/env python3
"""Run Docker Compose services

Starts core services:
- postgres: PostgreSQL database
- backend: FastAPI + Whisper API
- frontend: Angular SPA

Optional ngrok tunnels (use --ngrok flag):
- ngrok-whisper-backend: Ngrok tunnel for backend
- ngrok-whisper-frontend: Ngrok tunnel for frontend
- ngrok-whisper-llm: Ngrok tunnel for LLM service

Usage:
    python scripts/docker/run.py              # Start core services only
    python scripts/docker/run.py --ngrok      # Start with ngrok tunnels
    python scripts/docker/run.py --build      # Build and start
    python scripts/docker/run.py -d           # Start detached

Note: Ngrok requires NGROK_AUTHTOKEN environment variable to be set.
"""
import subprocess
import sys
import argparse

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Run Docker Compose services")
    parser.add_argument("--build", action="store_true", help="Build images before starting")
    parser.add_argument("--detach", "-d", action="store_true", help="Run in detached mode")
    parser.add_argument("--ngrok", action="store_true", help="Include ngrok tunnels (requires NGROK_AUTHTOKEN)")

    args = parser.parse_args()

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
