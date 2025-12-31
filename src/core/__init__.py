"""Core types and utilities for Noisett."""

from src.core.result import CommandResult, CommandError, Warning, success, error
from src.core.errors import ErrorCode
from src.core.types import (
    AssetType,
    ModelId,
    JobStatus,
    QualityPreset,
    GeneratedImage,
    Job,
    Model,
    AssetTypeInfo,
)

__all__ = [
    # Result types
    "CommandResult",
    "CommandError",
    "Warning",
    "success",
    "error",
    # Error codes
    "ErrorCode",
    # Domain types
    "AssetType",
    "ModelId",
    "JobStatus",
    "QualityPreset",
    "GeneratedImage",
    "Job",
    "Model",
    "AssetTypeInfo",
]
