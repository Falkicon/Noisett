"""Model Registry - Load models.json configuration for Director Mode.

This module provides access to the model registry configuration defined in
models.json. It supports dynamic model loading without code changes, as
specified in the Director Mode implementation plan.

Usage:
    from src.ml.registry import get_model, list_models

    # Get specific model configuration
    model = get_model("replicate:flux-dev-lora")

    # List all available models
    models = list_models()
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def _get_models_path() -> Path:
    """Get the path to the models.json configuration file."""
    # Get the directory where this file is located (src/ml/)
    current_dir = Path(__file__).parent
    models_path = current_dir / "models.json"

    if not models_path.exists():
        raise FileNotFoundError(f"Models configuration not found at {models_path}")

    return models_path


def _load_models() -> Dict[str, Any]:
    """Load and parse the models.json configuration file.

    Returns:
        Dict containing all model configurations.

    Raises:
        FileNotFoundError: If models.json is not found.
        json.JSONDecodeError: If models.json contains invalid JSON.
    """
    models_path = _get_models_path()

    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            models_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in models.json: {e.msg}",
            e.doc,
            e.pos
        ) from e

    if not isinstance(models_data, dict):
        raise ValueError("models.json must contain a JSON object at the root level")

    return models_data


def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific model.

    Args:
        model_id: The model identifier (e.g., "replicate:flux-dev-lora")

    Returns:
        Model configuration dictionary if found, None if not found.

    Example:
        model = get_model("replicate:flux-dev-lora")
        if model:
            print(f"Model name: {model['name']}")
            print(f"Supports LoRA: {model['capabilities']['supportsLora']}")
    """
    models = _load_models()
    return models.get(model_id)


def list_models() -> Dict[str, Any]:
    """List all available models and their configurations.

    Returns:
        Dictionary mapping model IDs to their configuration objects.

    Example:
        models = list_models()
        for model_id, config in models.items():
            print(f"{model_id}: {config['name']}")
    """
    return _load_models()


def validate_model_settings(model_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Validate model settings against the schema and apply defaults.

    Args:
        model_id: The model identifier
        settings: User-provided settings to validate

    Returns:
        Validated and normalized settings with defaults applied.

    Raises:
        ValueError: If model not found or settings are invalid.

    Example:
        # User provides partial settings
        user_settings = {"guidance_scale": 4.0}

        # Get validated settings with defaults
        validated = validate_model_settings("replicate:flux-dev-lora", user_settings)
        # Result: {"num_inference_steps": 28, "guidance_scale": 4.0, "aspect_ratio": "1:1"}
    """
    model = get_model(model_id)
    if not model:
        raise ValueError(f"Model '{model_id}' not found in registry")

    model_settings = model.get("settings", [])
    validated = {}

    for setting in model_settings:
        key = setting["key"]
        setting_type = setting["type"]
        default_value = setting["default"]

        # Use provided value or default
        value = settings.get(key, default_value)

        # Validate based on setting type
        if setting_type == "range":
            min_val = setting.get("min")
            max_val = setting.get("max")

            if not isinstance(value, (int, float)):
                raise ValueError(f"Setting '{key}' must be a number")

            if min_val is not None and value < min_val:
                raise ValueError(f"Setting '{key}' must be >= {min_val}")

            if max_val is not None and value > max_val:
                raise ValueError(f"Setting '{key}' must be <= {max_val}")

        elif setting_type == "select":
            options = setting.get("options", [])
            if value not in options:
                raise ValueError(f"Setting '{key}' must be one of: {options}")

        elif setting_type == "checkbox":
            if not isinstance(value, bool):
                raise ValueError(f"Setting '{key}' must be a boolean")

        elif setting_type == "number":
            if not isinstance(value, (int, float)):
                raise ValueError(f"Setting '{key}' must be a number")

        validated[key] = value

    return validated


def model_supports_lora(model_id: str) -> bool:
    """Check if a model supports LoRA fine-tuning.

    Args:
        model_id: The model identifier

    Returns:
        True if the model supports LoRA, False otherwise.

    Example:
        if model_supports_lora("replicate:flux-dev-lora"):
            print("This model can use LoRA fine-tuning")
    """
    model = get_model(model_id)
    if not model:
        return False

    capabilities = model.get("capabilities", {})
    return capabilities.get("supportsLora", False)


def get_model_max_images(model_id: str) -> int:
    """Get the maximum number of images this model can generate at once.

    Args:
        model_id: The model identifier

    Returns:
        Maximum number of images (defaults to 1 if not specified).

    Example:
        max_images = get_model_max_images("replicate:flux-dev-lora")
        print(f"This model can generate up to {max_images} images")
    """
    model = get_model(model_id)
    if not model:
        return 1

    capabilities = model.get("capabilities", {})
    return capabilities.get("maxImages", 1)