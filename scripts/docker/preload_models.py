#!/usr/bin/env python3
"""
faster-whisper Model Pre-Download Script for Docker

Downloads faster-whisper models from HuggingFace Hub to cache volume on container startup.
Smart caching: Only downloads missing models unless --force is used.
"""
import argparse
import os
import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Available faster-whisper models
AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]
DEFAULT_MODELS = ["base"]  # Default model to pre-download

# Cache directory for HuggingFace Hub (faster-whisper uses this)
CACHE_DIR = Path.home() / ".cache" / "huggingface"


def get_repo_id(model_name: str) -> str:
    """Get HuggingFace repo ID for a model name."""
    repo_map = {
        "tiny": "Systran/faster-whisper-tiny",
        "tiny.en": "Systran/faster-whisper-tiny.en",
        "base": "Systran/faster-whisper-base",
        "base.en": "Systran/faster-whisper-base.en",
        "small": "Systran/faster-whisper-small",
        "small.en": "Systran/faster-whisper-small.en",
        "medium": "Systran/faster-whisper-medium",
        "medium.en": "Systran/faster-whisper-medium.en",
        "large": "Systran/faster-whisper-large-v3",
        "large-v1": "Systran/faster-whisper-large-v1",
        "large-v2": "Systran/faster-whisper-large-v2",
        "large-v3": "Systran/faster-whisper-large-v3",
        "turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
        "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    }
    return repo_map.get(model_name, f"Systran/faster-whisper-{model_name}")


def model_exists(model_name: str) -> bool:
    """Check if a faster-whisper model exists in HuggingFace cache."""
    try:
        from huggingface_hub import try_to_load_from_cache

        repo_id = get_repo_id(model_name)

        # Check if model.bin exists in cache (main CTranslate2 model file)
        cached = try_to_load_from_cache(repo_id, "model.bin")
        if cached is not None:
            # Get file size
            file_size_mb = os.path.getsize(cached) / (1024 * 1024)
            print(f"  Model '{model_name}' found in cache ({file_size_mb:.1f} MB)")
            return True

        print(f"  Model '{model_name}' not found in cache")
        return False

    except Exception as e:
        print(f"  Error checking cache for '{model_name}': {e}")
        return False


def download_model(model_name: str, force: bool = False) -> bool:
    """Download a faster-whisper model if missing or force is True."""
    if not force and model_exists(model_name):
        print(f"  Skipping '{model_name}' (already cached, use --force to re-download)")
        return True

    try:
        from faster_whisper import WhisperModel

        print(f"  Downloading model '{model_name}' from HuggingFace Hub...")

        # Loading the model triggers download if not cached
        # Use CPU and int8 to minimize memory during preload
        model = WhisperModel(model_name, device="cpu", compute_type="int8")

        # Release model from memory
        del model

        print(f"  Successfully downloaded '{model_name}'")
        return True

    except Exception as e:
        print(f"  Failed to download '{model_name}': {e}")
        return False


def parse_models(models_input):
    """Parse model list from comma or space-separated string."""
    models = []
    for item in models_input:
        # Handle comma-separated values
        if "," in item:
            models.extend([m.strip() for m in item.split(",") if m.strip()])
        else:
            models.append(item.strip())
    # Validate models
    valid_models = [m for m in models if m in AVAILABLE_MODELS]
    invalid_models = [m for m in models if m not in AVAILABLE_MODELS]
    if invalid_models:
        print(f"Warning: Ignoring invalid models: {', '.join(invalid_models)}")
    return valid_models if valid_models else DEFAULT_MODELS


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Pre-download faster-whisper models to HuggingFace cache volume"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help=f"Models to download (comma or space-separated). Available: {', '.join(AVAILABLE_MODELS)} (default: {DEFAULT_MODELS})"
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
    if args.all:
        models_to_download = AVAILABLE_MODELS
    else:
        models_to_download = parse_models(args.models)

    print("=" * 60)
    print("faster-whisper Model Pre-Download Script")
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
        print(f"Processing '{model}':")
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
