"""Download Whisper model before first run"""
import whisper
import sys
import argparse


def download_model(model_name: str = "base"):
    """
    Download specified Whisper model.

    Args:
        model_name: Name of the model (tiny, base, small, medium, large)
    """
    valid_models = ["tiny", "base", "small", "medium", "large"]

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
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model to download (default: base)"
    )

    args = parser.parse_args()
    download_model(args.model)
