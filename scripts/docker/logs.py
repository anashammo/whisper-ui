#!/usr/bin/env python3
"""View Docker container logs

Available services (service names for docker-compose):
- postgres: PostgreSQL database (container: whisper-postgres)
- backend: FastAPI + Whisper API (container: whisper-backend)
- frontend: Angular SPA (container: whisper-frontend)
- ngrok-backend: Ngrok tunnel for backend (container: ngrok-whisper-backend)
- ngrok-frontend: Ngrok tunnel for frontend (container: ngrok-whisper-frontend)
- ngrok-llm: Ngrok tunnel for LLM service (container: ngrok-whisper-llm)

Usage:
    python scripts/docker/logs.py                # View all logs (including ngrok)
    python scripts/docker/logs.py --no-ngrok     # View core services logs only
    python scripts/docker/logs.py backend        # View backend logs
    python scripts/docker/logs.py -f             # Follow all logs
    python scripts/docker/logs.py backend -f     # Follow backend logs
    python scripts/docker/logs.py --tail 100     # Show last 100 lines
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

# Valid service names (simple names as defined in docker-compose.yml)
SERVICES = [
    "postgres",
    "backend",
    "frontend",
    "ngrok-backend",
    "ngrok-frontend",
    "ngrok-llm"
]


def main():
    parser = argparse.ArgumentParser(description="View Docker container logs")
    parser.add_argument("service", nargs="?", choices=SERVICES,
                       help=f"Service name: {', '.join(SERVICES)}")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow log output")
    parser.add_argument("--tail", type=int, help="Number of lines to show from end")
    parser.add_argument("--no-ngrok", action="store_true", help="Exclude ngrok services from logs")

    args = parser.parse_args()

    # Base command with env file
    cmd = ["docker-compose", "--env-file", "src/presentation/api/.env"]

    # Add ngrok profile by default (unless --no-ngrok specified or viewing ngrok service only)
    if not args.no_ngrok or (args.service and args.service.startswith("ngrok-")):
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
