"""Asset generation commands.

Commands:
- asset.generate: Generate images from a text prompt
- asset.types: List available asset types
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode, get_error_template
from src.core.result import CommandResult, Warning, error, success
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
        default=4,
        ge=1,
        le=4,
        description="Number of variations to generate",
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
        input: Generation parameters including prompt, asset_type, model, quality, count
        
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

    # Build suggestions
    suggestions: list[str] = []
    if input.quality == QualityPreset.DRAFT:
        suggestions.append("Use 'standard' quality for better results")
    if input.asset_type == AssetType.PRODUCT:
        suggestions.append("Try 'premium' asset type for marketing-grade quality")

    output = AssetGenerateOutput(job=job, estimated_seconds=estimated_seconds)

    return success(
        data=output,
        reasoning=f"Started generation of {input.count} {input.asset_type.value} images using {model_info.name}",
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
