"""Script to stop the backend server"""
import psutil
import os
import sys

def stop_backend():
    """Stop the backend server running on port 8001"""
    print("Stopping backend server...")

    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a Python process running uvicorn on port 8001
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('uvicorn' in str(arg) for arg in cmdline):
                if any('8001' in str(arg) for arg in cmdline):
                    print(f"Found backend process (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait(timeout=5)
                    print("✓ Backend server stopped successfully!")
                    found = True
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

    if not found:
        print("No backend server found running on port 8001")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(stop_backend())
