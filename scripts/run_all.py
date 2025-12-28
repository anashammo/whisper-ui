"""Script to start both backend and frontend servers"""
import subprocess
import sys
import os
import time

def run_all():
    """Start both backend and frontend servers in separate processes"""
    print("=" * 50)
    print("Starting All Servers...")
    print("=" * 50)

    backend_process = None
    frontend_process = None

    try:
        # Start backend server
        print("\n1. Starting Backend Server...")
        backend_process = subprocess.Popen(
            [sys.executable, "scripts/run_backend.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        print("   ✓ Backend starting (PID: {})".format(backend_process.pid))

        # Wait a bit for backend to initialize
        time.sleep(3)

        # Start frontend server
        print("\n2. Starting Frontend Server...")
        frontend_process = subprocess.Popen(
            [sys.executable, "scripts/run_frontend.py"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        print("   ✓ Frontend starting (PID: {})".format(frontend_process.pid))

        print("\n" + "=" * 50)
        print("All servers started successfully!")
        print("=" * 50)
        print("\nBackend:  http://localhost:8001")
        print("API Docs: http://localhost:8001/docs")
        print("Frontend: http://localhost:4200")
        print("\nPress CTRL+C to stop all servers")
        print("=" * 50)

        # Wait for processes
        backend_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        print("\n\nStopping all servers...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("✓ All servers stopped")
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        return 1

if __name__ == "__main__":
    sys.exit(run_all())
