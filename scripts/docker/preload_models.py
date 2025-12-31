#!/usr/bin/env python3
"""
Whisper Model Pre-Download Script for Docker

Downloads Whisper models to cache volume on container startup.
Smart caching: Only downloads missing models unless --force is used.
"""
import argparse
import os
import sys
from pathlib import Path
import whisper

# Available Whisper models
AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]
DEFAULT_MODELS = ["base"]  # Default model to pre-download

# Cache directory (will be volume-mounted in Docker)
CACHE_DIR = Path.home() / ".cache" / "whisper"


def model_exists(model_name: str) -> bool:
    """Check if a Whisper model exists in cache."""
    model_file = CACHE_DIR / f"{model_name}.pt"
    exists = model_file.exists()

    if exists:
        file_size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"✓ Model '{model_name}' found in cache ({file_size_mb:.1f} MB)")
    else:
        print(f"✗ Model '{model_name}' not found in cache")

    return exists


def download_model(model_name: str, force: bool = False) -> bool:
    """Download a Whisper model if missing or force is True."""
    if not force and model_exists(model_name):
        print(f"⊳ Skipping '{model_name}' (already cached, use --force to re-download)")
        return True

    try:
        print(f"⬇ Downloading model '{model_name}'...")
        whisper.load_model(model_name, download_root=str(CACHE_DIR))
        print(f"✓ Successfully downloaded '{model_name}'")
        return True
    except Exception as e:
        print(f"✗ Failed to download '{model_name}': {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Pre-download Whisper models to cache volume"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=AVAILABLE_MODELS,
        default=DEFAULT_MODELS,
        help=f"Models to download (default: {DEFAULT_MODELS})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if models exist in cache"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available models"
    )

    args = parser.parse_args()

    # Determine which models to download
    models_to_download = AVAILABLE_MODELS if args.all else args.models

    print("=" * 60)
    print("Whisper Model Pre-Download Script")
    print("=" * 60)
    print(f"Cache directory: {CACHE_DIR}")
    print(f"Models to process: {', '.join(models_to_download)}")
    print(f"Force re-download: {args.force}")
    print("=" * 60)
    print()

    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Download models
    success_count = 0
    failure_count = 0

    for model in models_to_download:
        if download_model(model, force=args.force):
            success_count += 1
        else:
            failure_count += 1
        print()  # Blank line between models

    # Summary
    print("=" * 60)
    print(f"Summary: {success_count} successful, {failure_count} failed")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(1 if failure_count > 0 else 0)


if __name__ == "__main__":
    main()
