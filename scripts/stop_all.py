"""Script to stop both backend and frontend servers"""
import sys
import subprocess

def stop_all():
    """Stop both backend and frontend servers"""
    print("=" * 50)
    print("Stopping all servers...")
    print("=" * 50)

    # Stop backend
    print("\n1. Stopping Backend Server:")
    backend_result = subprocess.run([sys.executable, "scripts/stop_backend.py"])

    # Stop frontend
    print("\n2. Stopping Frontend Server:")
    frontend_result = subprocess.run([sys.executable, "scripts/stop_frontend.py"])

    print("\n" + "=" * 50)
    if backend_result.returncode == 0 or frontend_result.returncode == 0:
        print("✓ Server shutdown complete!")
    else:
        print("⚠ No servers were running")
    print("=" * 50)

    return 0

if __name__ == "__main__":
    sys.exit(stop_all())
