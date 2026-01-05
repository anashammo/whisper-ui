#!/usr/bin/env python3
"""View Docker container logs

Available services:
- postgres: PostgreSQL database
- backend: FastAPI + Whisper API
- frontend: Angular SPA
- ngrok-whisper-backend: Ngrok tunnel for backend
- ngrok-whisper-frontend: Ngrok tunnel for frontend
- ngrok-whisper-llm: Ngrok tunnel for LLM service

Usage:
    python scripts/docker/logs.py              # View all logs (core services)
    python scripts/docker/logs.py --ngrok      # View all logs including ngrok
    python scripts/docker/logs.py backend      # View backend logs
    python scripts/docker/logs.py -f           # Follow all logs
    python scripts/docker/logs.py backend -f   # Follow backend logs
    python scripts/docker/logs.py --tail 100   # Show last 100 lines
"""
import subprocess
import sys
import argparse

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Valid service names
SERVICES = [
    "postgres",
    "backend",
    "frontend",
    "ngrok-whisper-backend",
    "ngrok-whisper-frontend",
    "ngrok-whisper-llm"
]


def main():
    parser = argparse.ArgumentParser(description="View Docker container logs")
    parser.add_argument("service", nargs="?", choices=SERVICES,
                       help=f"Service name: {', '.join(SERVICES)}")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")
    parser.add_argument("--tail", type=int, help="Number of lines to show from end")
    parser.add_argument("--ngrok", action="store_true", help="Include ngrok services in logs")

    args = parser.parse_args()

    # Base command
    cmd = ["docker-compose"]

    # Add profile if ngrok requested or if viewing ngrok service
    if args.ngrok or (args.service and args.service.startswith("ngrok")):
        cmd.extend(["--profile", "ngrok"])

    cmd.append("logs")

    if args.follow:
        cmd.append("-f")

    if args.tail:
        cmd.extend(["--tail", str(args.tail)])

    if args.service:
        cmd.append(args.service)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
