"""
Centralized Whisper model information and configuration.

This module provides a single source of truth for all Whisper model specifications,
ensuring consistency across the backend API, frontend components, and documentation.

Model specifications are based on OpenAI's official Whisper repository:
https://github.com/openai/whisper
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ModelInfo:
    """
    Immutable value object containing specifications for a Whisper model.

    Attributes:
        code: Model identifier (e.g., 'tiny', 'base', 'small')
        name: Display name (e.g., 'Tiny', 'Base')
        description: Human-readable description of model characteristics
        parameters: Number of parameters (e.g., '39M', '74M')
        download_size_mb: Approximate model file size in megabytes
        vram_required_gb: GPU VRAM required for inference in gigabytes
        speed_multiplier: Speed relative to large model (higher = faster)
        use_case: Recommended use case or scenario
    """
    code: str
    name: str
    description: str
    parameters: str
    download_size_mb: int
    vram_required_gb: int
    speed_multiplier: float
    use_case: str

    def to_dict(self) -> Dict:
        """Convert ModelInfo to dictionary for API responses."""
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "download_size_mb": self.download_size_mb,
            "vram_required_gb": self.vram_required_gb,
            "speed_multiplier": self.speed_multiplier,
            "use_case": self.use_case,
            "size": f"~{self.download_size_mb}MB" if self.download_size_mb < 1000 else f"~{self.download_size_mb / 1000:.1f}GB",
            "size_bytes": self.download_size_mb * 1024 * 1024
        }


# Canonical Whisper Model Specifications
# Source: OpenAI Whisper GitHub repository
# Last Updated: December 2025
WHISPER_MODELS: Dict[str, ModelInfo] = {
    'tiny': ModelInfo(
        code='tiny',
        name='Tiny',
        description='Fastest model with acceptable accuracy, ideal for quick drafts and testing',
        parameters='39M',
        download_size_mb=75,
        vram_required_gb=1,
        speed_multiplier=10.0,
        use_case='Quick transcriptions, testing, real-time applications'
    ),
    'base': ModelInfo(
        code='base',
        name='Base',
        description='Recommended for general use, excellent balance of speed and accuracy',
        parameters='74M',
        download_size_mb=150,
        vram_required_gb=1,
        speed_multiplier=7.0,
        use_case='General purpose transcriptions (recommended default)'
    ),
    'small': ModelInfo(
        code='small',
        name='Small',
        description='Balanced performance with better accuracy than base model',
        parameters='244M',
        download_size_mb=500,
        vram_required_gb=2,
        speed_multiplier=4.0,
        use_case='Higher quality transcriptions without large resource requirements'
    ),
    'medium': ModelInfo(
        code='medium',
        name='Medium',
        description='High accuracy model suitable for important transcriptions',
        parameters='769M',
        download_size_mb=1500,
        vram_required_gb=5,
        speed_multiplier=2.0,
        use_case='Professional transcriptions requiring high accuracy'
    ),
    'large': ModelInfo(
        code='large',
        name='Large',
        description='Best accuracy available, recommended for critical transcriptions',
        parameters='1550M',
        download_size_mb=3000,
        vram_required_gb=10,
        speed_multiplier=1.0,
        use_case='Maximum accuracy for critical or challenging audio'
    ),
    'turbo': ModelInfo(
        code='turbo',
        name='Turbo',
        description='Optimized for speed and accuracy, excellent all-around performance',
        parameters='809M',
        download_size_mb=3000,
        vram_required_gb=6,
        speed_multiplier=8.0,
        use_case='High-quality transcriptions with faster processing (not for translation)'
    )
}


def get_model_info(model_code: str) -> ModelInfo:
    """
    Get information for a specific Whisper model.

    Args:
        model_code: Model identifier (tiny, base, small, medium, large, turbo)

    Returns:
        ModelInfo object containing model specifications

    Raises:
        KeyError: If model_code is not a valid Whisper model
    """
    if model_code not in WHISPER_MODELS:
        valid_models = ', '.join(WHISPER_MODELS.keys())
        raise KeyError(f"Invalid model code '{model_code}'. Valid models: {valid_models}")

    return WHISPER_MODELS[model_code]


def get_all_models() -> List[ModelInfo]:
    """
    Get information for all available Whisper models.

    Returns:
        List of ModelInfo objects in order: tiny, base, small, medium, large, turbo
    """
    return [
        WHISPER_MODELS['tiny'],
        WHISPER_MODELS['base'],
        WHISPER_MODELS['small'],
        WHISPER_MODELS['medium'],
        WHISPER_MODELS['large'],
        WHISPER_MODELS['turbo']
    ]


def get_model_codes() -> List[str]:
    """
    Get list of all valid model codes.

    Returns:
        List of model codes: ['tiny', 'base', 'small', 'medium', 'large', 'turbo']
    """
    return list(WHISPER_MODELS.keys())


def get_model_size_bytes(model_code: str) -> int:
    """
    Get approximate download size in bytes for a model.

    Args:
        model_code: Model identifier

    Returns:
        Approximate model size in bytes

    Raises:
        KeyError: If model_code is invalid
    """
    model = get_model_info(model_code)
    return model.download_size_mb * 1024 * 1024


# Model ordering by size (for UI display)
MODEL_ORDER = ['tiny', 'base', 'small', 'medium', 'large', 'turbo']

# Validation regex pattern for model names
MODEL_VALIDATION_PATTERN = r"^(tiny|base|small|medium|large|turbo)$"
