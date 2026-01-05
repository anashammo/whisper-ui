#!/usr/bin/env python3
"""Stop Docker Compose services

Stops all services including:
- postgres: PostgreSQL database
- backend: FastAPI + Whisper API
- frontend: Angular SPA
- ngrok-whisper-backend: Ngrok tunnel for backend (if running)
- ngrok-whisper-frontend: Ngrok tunnel for frontend (if running)
- ngrok-whisper-llm: Ngrok tunnel for LLM service (if running)

Usage:
    python scripts/docker/stop.py              # Stop all services
    python scripts/docker/stop.py -v           # Stop and remove volumes (WARNING: deletes data)
    python scripts/docker/stop.py --ngrok-only # Stop only ngrok tunnels
"""
import subprocess
import sys
import argparse

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Stop Docker Compose services")
    parser.add_argument("--remove-volumes", "-v", action="store_true",
                       help="Remove volumes as well (WARNING: deletes data)")
    parser.add_argument("--ngrok-only", action="store_true",
                       help="Stop only ngrok tunnel services")

    args = parser.parse_args()

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
    cmd = ["docker-compose", "--profile", "ngrok", "down"]

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
