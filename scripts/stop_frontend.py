"""Script to stop the Angular frontend server"""
import psutil
import os
import sys

def stop_frontend():
    """Stop the Angular dev server running on port 4200"""
    print("Stopping frontend server...")

    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if it's a Node process running on port 4200
            cmdline = proc.info.get('cmdline', [])
            if cmdline and proc.info.get('name', '').lower().startswith('node'):
                # Check if it's related to Angular (ng serve)
                if any('ng' in str(arg) or '4200' in str(arg) for arg in cmdline):
                    print(f"Found frontend process (PID: {proc.info['pid']})")
                    # Kill the process and all its children
                    parent = psutil.Process(proc.info['pid'])
                    children = parent.children(recursive=True)
                    for child in children:
                        child.terminate()
                    parent.terminate()

                    # Wait for processes to terminate
                    gone, alive = psutil.wait_procs(children + [parent], timeout=5)

                    print("✓ Frontend server stopped successfully!")
                    found = True
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

    if not found:
        print("No frontend server found running on port 4200")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(stop_frontend())
