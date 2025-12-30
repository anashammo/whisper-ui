"""
System Health Check - Comprehensive system verification

Verifies the entire Whisper transcription system is configured correctly
and ready for development or production use.

Usage:
    python scripts/maintenance/health_check.py
    python scripts/maintenance/health_check.py --verbose
"""

import sys
import os
import subprocess
import sqlite3
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class HealthChecker:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks_passed = 0
        self.checks_total = 0
        self.warnings = []
        self.errors = []

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")

    def check(self, name: str, passed: bool, message: str = "", is_warning: bool = False):
        """Record and print check result"""
        self.checks_total += 1

        if passed:
            self.checks_passed += 1
            status = f"{Colors.GREEN}[OK]{Colors.RESET}"
        elif is_warning:
            status = f"{Colors.YELLOW}[WARN]{Colors.RESET}"
            self.warnings.append(f"{name}: {message}")
        else:
            status = f"{Colors.RED}[FAIL]{Colors.RESET}"
            self.errors.append(f"{name}: {message}")

        print(f"{status} {name}")
        if message and (self.verbose or not passed):
            indent = "  "
            color = Colors.YELLOW if is_warning else (Colors.GREEN if passed else Colors.RED)
            print(f"{indent}{color}{message}{Colors.RESET}")

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run shell command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=10
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def check_python_version(self):
        """Check Python version"""
        version = sys.version_info
        passed = version.major == 3 and version.minor >= 9
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        self.check(
            "Python version",
            passed,
            f"Found Python {version_str} (requires 3.9+)",
            is_warning=not passed
        )

    def check_git_repository(self):
        """Check if in git repository"""
        returncode, stdout, _ = self.run_command(['git', 'rev-parse', '--git-dir'])
        passed = returncode == 0

        if passed:
            returncode, branch, _ = self.run_command(['git', 'branch', '--show-current'])
            branch_name = branch.strip() if returncode == 0 else "unknown"
            self.check("Git repository", passed, f"Current branch: {branch_name}")
        else:
            self.check("Git repository", passed, "Not a git repository")

    def check_database(self):
        """Check database exists and is accessible"""
        db_path = project_root / "whisper_transcriptions.db"

        if not db_path.exists():
            self.check("Database file", False, "Database not found (run: python scripts/setup/init_db.py)")
            return

        # Check if we can connect
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ['audio_files', 'transcriptions']
            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                self.check("Database schema", False, f"Missing tables: {', '.join(missing_tables)}")
            else:
                # Count records
                cursor.execute("SELECT COUNT(*) FROM audio_files")
                audio_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM transcriptions")
                trans_count = cursor.fetchone()[0]

                size_mb = db_path.stat().st_size / (1024 * 1024)

                self.check(
                    "Database",
                    True,
                    f"{audio_count} audio files, {trans_count} transcriptions ({size_mb:.2f} MB)"
                )

            conn.close()
        except Exception as e:
            self.check("Database access", False, str(e))

    def check_uploads_directory(self):
        """Check uploads directory"""
        uploads_dir = project_root / "uploads"

        if not uploads_dir.exists():
            self.check("Uploads directory", False, "Directory does not exist")
            return

        # Count subdirectories and total files
        subdirs = list(uploads_dir.glob("*"))
        audio_files = list(uploads_dir.glob("*/*"))

        total_size_mb = sum(f.stat().st_size for f in audio_files if f.is_file()) / (1024 * 1024)

        self.check(
            "Uploads directory",
            True,
            f"{len(subdirs)} groups, {len(audio_files)} files ({total_size_mb:.1f} MB)"
        )

    def check_python_dependencies(self):
        """Check Python dependencies"""
        requirements_file = project_root / "requirements.txt"

        if not requirements_file.exists():
            self.check("Requirements file", False, "requirements.txt not found")
            return

        # Check if virtual environment is active
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

        self.check(
            "Virtual environment",
            in_venv,
            "Active" if in_venv else "Not activated (recommended to use venv)",
            is_warning=not in_venv
        )

        # Check key packages
        key_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'openai-whisper', 'torch']

        for package in key_packages:
            try:
                __import__(package.replace('-', '_'))
                self.check(f"Package: {package}", True, "Installed")
            except ImportError:
                self.check(f"Package: {package}", False, "Not installed")

    def check_node_dependencies(self):
        """Check Node.js and frontend dependencies"""
        frontend_dir = project_root / "src" / "presentation" / "frontend"
        node_modules = frontend_dir / "node_modules"

        # Check Node.js version
        returncode, stdout, _ = self.run_command(['node', '--version'])
        if returncode == 0:
            node_version = stdout.strip()
            self.check("Node.js", True, f"Version {node_version}")
        else:
            self.check("Node.js", False, "Not installed or not in PATH")
            return

        # Check npm
        returncode, stdout, _ = self.run_command(['npm', '--version'])
        if returncode == 0:
            npm_version = stdout.strip()
            self.check("npm", True, f"Version {npm_version}")
        else:
            self.check("npm", False, "Not installed")

        # Check frontend dependencies
        if node_modules.exists():
            # Count installed packages
            package_count = len(list(node_modules.iterdir()))
            self.check("Frontend dependencies", True, f"{package_count} packages installed")
        else:
            self.check(
                "Frontend dependencies",
                False,
                "Not installed (run: cd src/presentation/frontend && npm install)"
            )

    def check_whisper_models(self):
        """Check Whisper models in cache"""
        cache_dir = Path.home() / ".cache" / "whisper"

        if not cache_dir.exists():
            self.check(
                "Whisper cache",
                False,
                "No models downloaded (run: python scripts/setup/download_whisper_model.py <model>)",
                is_warning=True
            )
            return

        # Check for models
        models = {
            'tiny.pt': 'Tiny (39M params)',
            'base.pt': 'Base (74M params)',
            'small.pt': 'Small (244M params)',
            'medium.pt': 'Medium (769M params)',
            'large-v3.pt': 'Large-v3 (1550M params)',
            'large-v3-turbo.pt': 'Turbo (809M params)',
        }

        found_models = []
        for model_file, model_name in models.items():
            model_path = cache_dir / model_file
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                found_models.append(f"{model_name} ({size_mb:.0f}MB)")
                if self.verbose:
                    self.check(f"Model: {model_file}", True, f"{size_mb:.0f} MB")

        if found_models:
            self.check(
                "Whisper models",
                True,
                f"{len(found_models)} model(s) downloaded: {', '.join([m.split(' (')[0] for m in found_models])}"
            )
        else:
            self.check(
                "Whisper models",
                False,
                "No models found",
                is_warning=True
            )

    def check_ffmpeg(self):
        """Check FFmpeg availability"""
        # Check in PATH
        returncode, stdout, _ = self.run_command(['ffmpeg', '-version'])

        if returncode == 0:
            version_line = stdout.split('\n')[0] if stdout else "unknown"
            self.check("FFmpeg", True, version_line)
        else:
            # Check in project directory
            ffmpeg_dir = project_root / "ffmpeg-8.0.1-essentials_build" / "bin"
            if ffmpeg_dir.exists():
                self.check("FFmpeg", True, f"Found in project directory: {ffmpeg_dir}")
            else:
                self.check("FFmpeg", False, "Not found (required for audio processing)")

    def check_backend_server(self):
        """Check if backend server is running"""
        try:
            response = requests.get("http://localhost:8001/docs", timeout=2)
            if response.status_code == 200:
                self.check("Backend server", True, "Running on http://localhost:8001")
            else:
                self.check("Backend server", False, f"Unexpected status: {response.status_code}")
        except requests.exceptions.RequestException:
            self.check(
                "Backend server",
                False,
                "Not running (start with: python scripts/server/run_backend.py)",
                is_warning=True
            )

    def check_frontend_server(self):
        """Check if frontend server is running"""
        try:
            response = requests.get("http://localhost:4200", timeout=2)
            if response.status_code == 200:
                self.check("Frontend server", True, "Running on http://localhost:4200")
            else:
                self.check("Frontend server", False, f"Unexpected status: {response.status_code}")
        except requests.exceptions.RequestException:
            self.check(
                "Frontend server",
                False,
                "Not running (start with: python scripts/server/run_frontend.py)",
                is_warning=True
            )

    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(project_root)

            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            used_percent = (used / total) * 100

            passed = free_gb > 5.0  # At least 5GB free
            self.check(
                "Disk space",
                passed,
                f"{free_gb:.1f} GB free of {total_gb:.1f} GB ({used_percent:.1f}% used)",
                is_warning=not passed
            )
        except Exception as e:
            self.check("Disk space", False, str(e), is_warning=True)

    def run_all_checks(self):
        """Run all health checks"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}System Health Check{Colors.RESET}")
        print(f"{Colors.BLUE}Project: {project_root}{Colors.RESET}\n")

        self.print_header("1. Environment")
        self.check_python_version()
        self.check_git_repository()
        self.check_disk_space()

        self.print_header("2. Dependencies")
        self.check_python_dependencies()
        self.check_node_dependencies()
        self.check_ffmpeg()

        self.print_header("3. Data & Storage")
        self.check_database()
        self.check_uploads_directory()

        self.print_header("4. Whisper Models")
        self.check_whisper_models()

        self.print_header("5. Servers (Optional)")
        self.check_backend_server()
        self.check_frontend_server()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print health check summary"""
        self.print_header("Health Check Summary")

        pass_rate = (self.checks_passed / self.checks_total * 100) if self.checks_total > 0 else 0

        # Determine status
        if pass_rate == 100 and not self.warnings:
            status_color = Colors.GREEN
            status_text = "EXCELLENT"
            status_icon = "[OK]"
        elif pass_rate >= 90:
            status_color = Colors.GREEN
            status_text = "GOOD"
            status_icon = "[OK]"
        elif pass_rate >= 70:
            status_color = Colors.YELLOW
            status_text = "FAIR"
            status_icon = "[WARN]"
        else:
            status_color = Colors.RED
            status_text = "POOR"
            status_icon = "[FAIL]"

        print(f"{status_color}{Colors.BOLD}{status_icon} System Health: {status_text}{Colors.RESET}")
        print(f"Checks Passed: {Colors.GREEN}{self.checks_passed}/{self.checks_total}{Colors.RESET} ({pass_rate:.1f}%)")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings ({len(self.warnings)}):{Colors.RESET}")
            for warning in self.warnings:
                print(f"  ! {warning}")

        if self.errors:
            print(f"\n{Colors.RED}Errors ({len(self.errors)}):{Colors.RESET}")
            for error in self.errors:
                print(f"  X {error}")

        print(f"\n{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")

        return pass_rate >= 70  # Success if 70% or more checks pass


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='System health check')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    checker = HealthChecker(verbose=args.verbose)
    success = checker.run_all_checks()

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
