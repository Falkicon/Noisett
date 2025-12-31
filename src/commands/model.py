"""Model information commands.

Commands:
- model.list: List available image generation models
- model.info: Get detailed information about a specific model
"""

from typing import List

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode, get_error_template
from src.core.result import CommandResult, Warning, error, success
from src.core.types import MODEL_CONFIGS, Model, ModelId


# --- Input/Output Schemas ---


class ModelListOutput(BaseModel):
    """Output for model.list command."""

    models: List[Model]


class ModelInfoInput(BaseModel):
    """Input for model.info command."""

    model_id: ModelId = Field(..., description="Model ID to get info for")


class ModelInfoOutput(BaseModel):
    """Output for model.info command."""

    model: Model


# --- Command Implementations ---


async def list_models() -> CommandResult[ModelListOutput]:
    """List available image generation models.
    
    Returns information about all models including availability
    and licensing information.
    
    Returns:
        CommandResult with list of models
    """
    models = list(MODEL_CONFIGS.values())
    available_count = sum(1 for m in models if m.available)

    output = ModelListOutput(models=models)

    return success(
        data=output,
        reasoning=f"{len(models)} models ({available_count} available)",
        suggestions=[
            "Use 'hidream' for commercial projects (Apache-2.0 license)",
            "Use 'flux' for highest quality (non-commercial only)",
        ],
    )


async def info(input: ModelInfoInput) -> CommandResult[ModelInfoOutput]:
    """Get detailed information about a specific model.
    
    Returns complete model details including license information
    and recommended settings.
    
    Args:
        input: Model ID to get info for
        
    Returns:
        CommandResult with model details
    """
    model = MODEL_CONFIGS.get(input.model_id)

    if not model:
        template = get_error_template(ErrorCode.MODEL_NOT_FOUND)
        return error(
            code=ErrorCode.MODEL_NOT_FOUND,
            message=f"Model '{input.model_id.value}' not found",
            suggestion=template["suggestion"],
        )

    output = ModelInfoOutput(model=model)

    # Build warnings
    warnings: List[Warning] = []
    if not model.commercial_ok:
        warnings.append(
            Warning(
                code="NON_COMMERCIAL",
                message=f"'{model.name}' is for non-commercial use only",
            )
        )
    if not model.available:
        warnings.append(
            Warning(
                code="UNAVAILABLE",
                message=f"'{model.name}' is not currently available",
            )
        )

    return success(
        data=output,
        reasoning=f"{model.name}: {model.description}",
        warnings=warnings if warnings else None,
    )
