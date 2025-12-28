"""Script to start the FastAPI backend server"""
import subprocess
import sys
import os
from pathlib import Path

def run_backend():
    """Start the FastAPI backend server with uvicorn"""
    print("=" * 50)
    print("Starting FastAPI Backend Server...")
    print("=" * 50)

    # Get the project root directory
    project_root = Path(__file__).parent.parent

    print(f"\nProject root: {project_root}")
    print("Server: http://0.0.0.0:8001")
    print("API Docs: http://localhost:8001/docs")
    print("Health Check: http://localhost:8001/api/v1/health")
    print("\nPress CTRL+C to stop the server")
    print("-" * 50)

    try:
        # Run uvicorn from the project root
        result = subprocess.run(
            [
                sys.executable,
                "-m", "uvicorn",
                "src.presentation.api.main:app",
                "--host", "0.0.0.0",
                "--port", "8001",
                "--reload"
            ],
            cwd=str(project_root)
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nBackend server stopped by user")
        return 0
    except Exception as e:
        print(f"\nError starting backend: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_backend())
