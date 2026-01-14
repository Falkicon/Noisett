"""Asset generation commands.

Commands:
- asset.generate: Generate images from a text prompt
- asset.types: List available asset types
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode, get_error_template
from afd.core import CommandResult, Warning, error, success
from src.core.types import (
    ASSET_TYPE_CONFIGS,
    MODEL_CONFIGS,
    AssetType,
    AssetTypeInfo,
    Job,
    JobStatus,
    ModelId,
    QualityPreset,
)

# In-memory job store (will be replaced with proper storage)
_jobs: dict[str, Job] = {}


# --- Input/Output Schemas ---


class AssetGenerateInput(BaseModel):
    """Input for asset.generate command."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Text description of the image to generate",
    )
    asset_type: AssetType = Field(
        default=AssetType.PRODUCT,
        description="Type of asset to generate",
    )
    model: ModelId = Field(
        default=ModelId.HIDREAM,
        description="Model to use for generation",
    )
    quality: QualityPreset = Field(
        default=QualityPreset.STANDARD,
        description="Quality preset affecting speed vs quality",
    )
    count: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Number of variations to generate",
    )
    lora: str | None = Field(
        default=None,
        description="LoRA ID to use for styled generation (Fireworks inference)",
    )


class AssetGenerateOutput(BaseModel):
    """Output for asset.generate command."""

    job: Job
    estimated_seconds: int


class AssetTypesOutput(BaseModel):
    """Output for asset.types command."""

    types: list[AssetTypeInfo]


# --- Command Implementations ---


async def generate(input: AssetGenerateInput) -> CommandResult[AssetGenerateOutput]:
    """Generate images from a text prompt.

    Creates a generation job and returns immediately with job ID.
    Use job.status to poll for completion.

    Args:
        input: Generation parameters including prompt, asset_type, model, quality, count, lora

    Returns:
        CommandResult with job information and estimated completion time
    """
    # Validate prompt
    if not input.prompt.strip():
        template = get_error_template(ErrorCode.PROMPT_EMPTY)
        return error(
            code=ErrorCode.PROMPT_EMPTY,
            message=template["message"],
            suggestion=template["suggestion"],
        )

    # Validate LoRA if provided
    lora_info = None
    if input.lora:
        try:
            from src.core.convex_client import get_convex_client
            from src.core.types import LoraStatus

            convex = get_convex_client()
            convex_lora = await convex.get_lora(input.lora)

            if not convex_lora:
                return error(
                    code=ErrorCode.LORA_NOT_FOUND,
                    message=f"LoRA '{input.lora}' not found",
                    suggestion="Use lora.list to see available LoRAs",
                )

            # Check if LoRA is deployed and ready for use
            lora_status = convex_lora["status"]
            if lora_status != "deployed":
                return error(
                    code=ErrorCode.LORA_NOT_READY,
                    message=f"LoRA is not deployed (status: {lora_status})",
                    suggestion="Wait for deployment to complete or use lora.deploy to retry",
                )

            # Check if LoRA is active
            if not convex_lora.get("isActive", False):
                return error(
                    code=ErrorCode.LORA_NOT_READY,
                    message="LoRA is not active",
                    suggestion="Activate the LoRA first: lora.activate",
                )

            lora_info = {
                "id": convex_lora["_id"],
                "name": convex_lora["name"],
                "trigger_word": convex_lora["triggerWord"],
                "fireworks_model_id": convex_lora.get("fireworksModelId"),
            }

            # Ensure Fireworks model ID is available
            if not lora_info["fireworks_model_id"]:
                return error(
                    code=ErrorCode.LORA_NOT_READY,
                    message="LoRA deployment incomplete - no Fireworks model ID",
                    suggestion="Use lora.deploy to retry deployment",
                )

        except Exception as e:
            return error(
                code=ErrorCode.STORAGE_ERROR,
                message=f"Failed to validate LoRA: {e}",
                suggestion="Check the LoRA ID and try again",
            )

    # Validate model availability
    model_info = MODEL_CONFIGS.get(input.model)
    if not model_info or not model_info.available:
        template = get_error_template(ErrorCode.MODEL_UNAVAILABLE)
        return error(
            code=ErrorCode.MODEL_UNAVAILABLE,
            message=f"Model '{input.model.value}' is not currently available",
            suggestion="Try 'hidream' which is commercially licensed and available",
        )

    # Create job
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    job = Job(
        id=job_id,
        status=JobStatus.QUEUED,
        prompt=input.prompt,
        asset_type=input.asset_type,
        model=input.model,
        quality=input.quality,
        count=input.count,
        progress=0,
        images=[],
        created_at=now,
        lora_id=input.lora if lora_info else None,  # Store LoRA ID in job
    )

    # Store job
    _jobs[job_id] = job

    # Estimate time based on quality and count
    base_seconds = {"draft": 10, "standard": 20, "high": 40}
    estimated_seconds = base_seconds.get(input.quality.value, 20) * input.count

    # Build warnings
    warnings: list[Warning] = []
    if not model_info.commercial_ok:
        warnings.append(
            Warning(
                code="NON_COMMERCIAL",
                message=f"Model '{model_info.name}' is for non-commercial use only",
            )
        )

    # Add LoRA-related warnings if using LoRA
    if lora_info:
        if lora_info["trigger_word"].lower() not in input.prompt.lower():
            warnings.append(
                Warning(
                    code="LORA_TRIGGER_MISSING",
                    message=f"Prompt does not contain trigger word '{lora_info['trigger_word']}' - LoRA style may not be applied",
                )
            )

    # Build suggestions
    suggestions: list[str] = []
    if input.quality == QualityPreset.DRAFT:
        suggestions.append("Use 'standard' quality for better results")
    if input.asset_type == AssetType.PRODUCT:
        suggestions.append("Try 'premium' asset type for marketing-grade quality")

    # Add LoRA-specific suggestions
    if lora_info:
        suggestions.append(f"Using LoRA '{lora_info['name']}' with trigger word '{lora_info['trigger_word']}'")
        if lora_info["trigger_word"].lower() not in input.prompt.lower():
            suggestions.append(f"Include '{lora_info['trigger_word']}' in your prompt for better LoRA styling")

    output = AssetGenerateOutput(job=job, estimated_seconds=estimated_seconds)

    # Build reasoning message
    reasoning_parts = [f"Started generation of {input.count} {input.asset_type.value} images using {model_info.name}"]
    if lora_info:
        reasoning_parts.append(f"with LoRA '{lora_info['name']}'")

    return success(
        data=output,
        reasoning=" ".join(reasoning_parts),
        warnings=warnings if warnings else None,
        suggestions=suggestions if suggestions else None,
    )


async def types() -> CommandResult[AssetTypesOutput]:
    """List available asset types and their configurations.
    
    Returns information about each asset type including name,
    description, prompt template, and recommended use cases.
    
    Returns:
        CommandResult with list of asset type configurations
    """
    asset_types = list(ASSET_TYPE_CONFIGS.values())

    output = AssetTypesOutput(types=asset_types)

    return success(
        data=output,
        reasoning=f"{len(asset_types)} asset types available",
    )


# Export job store for job commands
def get_job(job_id: str) -> Job | None:
    """Get a job by ID."""
    return _jobs.get(job_id)


def update_job(job: Job) -> None:
    """Update a job in the store."""
    _jobs[job.id] = job


def list_all_jobs() -> list[Job]:
    """List all jobs, newest first."""
    return sorted(_jobs.values(), key=lambda j: j.created_at, reverse=True)
