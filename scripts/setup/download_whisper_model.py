"""
Download Whisper models for transcription.

This script downloads and caches Whisper models to ~/.cache/whisper/
Models only need to be downloaded once and will be cached for future use.

Supported Models:
    - tiny:   ~75MB  download, ~1GB  VRAM (fastest, least accurate)
    - base:   ~150MB download, ~1GB  VRAM (recommended for general use)
    - small:  ~500MB download, ~2GB  VRAM (balanced performance)
    - medium: ~1.5GB download, ~5GB  VRAM (better quality)
    - large:  ~3GB   download, ~10GB VRAM (best accuracy)
    - turbo:  ~3GB   download, ~6GB  VRAM (speed + accuracy optimized)

Cache Location:
    Models are cached in: ~/.cache/whisper/
    (Windows: C:\\Users\\<username>\\.cache\\whisper\\)

Usage:
    python scripts/download_whisper_model.py [MODEL_NAME]

Arguments:
    MODEL_NAME: Optional model name (default: base)
                Choices: tiny, base, small, medium, large, turbo

Examples:
    # Download the recommended base model
    python scripts/download_whisper_model.py base

    # Download the fastest model for testing
    python scripts/download_whisper_model.py tiny

    # Download the most accurate model (requires ~10GB VRAM)
    python scripts/download_whisper_model.py large

    # Download the turbo model (optimized for speed)
    python scripts/download_whisper_model.py turbo

    # Default to base if no argument provided
    python scripts/download_whisper_model.py

Exit Codes:
    0: Success - Model downloaded or already cached
    1: Failure - Invalid model name or download error

Notes:
    - First download may take several minutes depending on internet speed
    - Models are downloaded from OpenAI's servers
    - Downloaded models are reused across all runs
    - Turbo model is not suitable for translation tasks
"""
import whisper
import sys
import argparse


def download_model(model_name: str = "base"):
    """
    Download specified Whisper model.

    Args:
        model_name: Name of the model (tiny, base, small, medium, large, turbo)
    """
    valid_models = ["tiny", "base", "small", "medium", "large", "turbo"]

    if model_name not in valid_models:
        print(f"Error: Invalid model name '{model_name}'")
        print(f"Valid models: {', '.join(valid_models)}")
        sys.exit(1)

    print(f"Downloading Whisper model: {model_name}")
    print("This may take a few minutes depending on your internet connection...")

    try:
        whisper.load_model(model_name)
        print(f"✓ Model '{model_name}' downloaded successfully!")
        print(f"✓ Model is ready to use")
    except Exception as e:
        print(f"✗ Error downloading model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Whisper model")
    parser.add_argument(
        "model",
        nargs="?",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper model to download (default: base)"
    )

    args = parser.parse_args()
    download_model(args.model)
