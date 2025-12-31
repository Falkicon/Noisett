"""LoRA training commands for Noisett (Phase 5).

Commands for creating, managing, and training custom LoRA models:
- lora.create: Create a new LoRA training project
- lora.upload-images: Upload training images to a LoRA project
- lora.train: Start training on a LoRA project
- lora.status: Get the status of a LoRA project
- lora.list: List all LoRA projects
- lora.activate: Activate/deactivate a trained LoRA
- lora.delete: Delete a LoRA project
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from ..core.errors import ErrorCode
from ..core.result import CommandResult, Warning, error, success
from ..core.types import (
    BaseModelType,
    Lora,
    LoraInfo,
    LoraStatus,
    TrainingImage,
)


# =============================================================================
# In-Memory Storage (MVP - will be replaced with persistent storage in Phase 8)
# =============================================================================

_loras: dict[str, Lora] = {}


def _generate_lora_id() -> str:
    """Generate a unique LoRA ID."""
    return f"lora_{uuid.uuid4().hex[:12]}"


def _now() -> datetime:
    """Get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


# =============================================================================
# Input/Output Schemas
# =============================================================================


class CreateLoraInput(BaseModel):
    """Input for lora.create command."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Human-readable name for the LoRA"
    )
    trigger_word: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique trigger word/phrase to activate this style",
    )
    base_model: BaseModelType = Field(
        default=BaseModelType.FLUX,
        description="Base model to fine-tune (flux or sdxl)",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional description of what this LoRA captures",
    )
    steps: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Number of training steps",
    )
    learning_rate: float = Field(
        default=1e-4,
        gt=0,
        lt=1,
        description="Learning rate for training",
    )


class CreateLoraOutput(BaseModel):
    """Output for lora.create command."""

    lora: Lora = Field(..., description="Created LoRA project")


class UploadImagesInput(BaseModel):
    """Input for lora.upload-images command."""

    lora_id: str = Field(..., description="ID of the LoRA project")
    images: list[dict] = Field(
        ...,
        min_length=1,
        description="List of images with 'url' and optional 'caption' keys",
    )


class UploadImagesOutput(BaseModel):
    """Output for lora.upload-images command."""

    lora: Lora = Field(..., description="Updated LoRA project")
    uploaded_count: int = Field(..., description="Number of images uploaded")


class TrainLoraInput(BaseModel):
    """Input for lora.train command."""

    lora_id: str = Field(..., description="ID of the LoRA project to train")


class TrainLoraOutput(BaseModel):
    """Output for lora.train command."""

    lora: Lora = Field(..., description="LoRA project with training started")


class LoraStatusInput(BaseModel):
    """Input for lora.status command."""

    lora_id: str = Field(..., description="ID of the LoRA project")


class LoraStatusOutput(BaseModel):
    """Output for lora.status command."""

    lora: Lora = Field(..., description="Full LoRA project details")


class LoraListInput(BaseModel):
    """Input for lora.list command."""

    status: LoraStatus | None = Field(
        default=None, description="Filter by status"
    )
    base_model: BaseModelType | None = Field(
        default=None, description="Filter by base model"
    )
    active_only: bool = Field(
        default=False, description="Only show active LoRAs"
    )


class LoraListOutput(BaseModel):
    """Output for lora.list command."""

    loras: list[LoraInfo] = Field(..., description="List of LoRA summaries")
    total: int = Field(..., description="Total count")


class LoraActivateInput(BaseModel):
    """Input for lora.activate command."""

    lora_id: str = Field(..., description="ID of the LoRA to activate/deactivate")
    active: bool = Field(default=True, description="Whether to activate or deactivate")


class LoraActivateOutput(BaseModel):
    """Output for lora.activate command."""

    lora: Lora = Field(..., description="Updated LoRA project")


class LoraDeleteInput(BaseModel):
    """Input for lora.delete command."""

    lora_id: str = Field(..., description="ID of the LoRA to delete")
    force: bool = Field(
        default=False,
        description="Force delete even if training is in progress",
    )


class LoraDeleteOutput(BaseModel):
    """Output for lora.delete command."""

    deleted_id: str = Field(..., description="ID of the deleted LoRA")
    name: str = Field(..., description="Name of the deleted LoRA")


# =============================================================================
# Command Implementations
# =============================================================================


async def create(input: CreateLoraInput) -> CommandResult[CreateLoraOutput]:
    """Create a new LoRA training project.
    
    This creates a project container for LoRA training. Next step is to
    upload training images with lora.upload-images.
    """
    # Check for duplicate name
    for lora in _loras.values():
        if lora.name.lower() == input.name.lower():
            return error(
                code=ErrorCode.LORA_ALREADY_EXISTS,
                message=f"A LoRA named '{input.name}' already exists",
                suggestion="Use a different name or delete the existing LoRA",
            )

    # Check for duplicate trigger word
    for lora in _loras.values():
        if lora.trigger_word.lower() == input.trigger_word.lower():
            return error(
                code=ErrorCode.LORA_ALREADY_EXISTS,
                message=f"Trigger word '{input.trigger_word}' is already in use",
                suggestion="Use a different trigger word",
            )

    # Create the LoRA
    lora_id = _generate_lora_id()
    now = _now()

    lora = Lora(
        id=lora_id,
        name=input.name,
        description=input.description,
        trigger_word=input.trigger_word,
        base_model=input.base_model,
        status=LoraStatus.CREATED,
        steps=input.steps,
        learning_rate=input.learning_rate,
        created_at=now,
    )

    _loras[lora_id] = lora

    warnings = []
    if input.base_model == BaseModelType.FLUX:
        warnings.append(
            Warning(
                code="FLUX_NON_COMMERCIAL",
                message="FLUX base model is non-commercial. Resulting LoRA inherits this license.",
            )
        )

    return success(
        data=CreateLoraOutput(lora=lora),
        reasoning=f"Created LoRA project '{input.name}' with trigger word '{input.trigger_word}'. "
        f"Next: upload 10-100 training images with lora.upload-images.",
        warnings=warnings if warnings else None,
        suggestions=["Upload training images: lora.upload-images"],
    )


async def upload_images(input: UploadImagesInput) -> CommandResult[UploadImagesOutput]:
    """Upload training images to a LoRA project.
    
    Images should be high-quality examples of the style you want to capture.
    Recommended: 20-30 diverse images showing variations of the concept.
    """
    # Find the LoRA
    lora = _loras.get(input.lora_id)
    if not lora:
        return error(
            code=ErrorCode.LORA_NOT_FOUND,
            message=f"LoRA '{input.lora_id}' not found",
            suggestion="Use lora.list to see available LoRAs",
        )

    # Check status - can only upload in CREATED or READY_TO_TRAIN state
    if lora.status not in [LoraStatus.CREATED, LoraStatus.READY_TO_TRAIN]:
        return error(
            code=ErrorCode.TRAINING_IN_PROGRESS,
            message=f"Cannot upload images while LoRA is in '{lora.status.value}' state",
            suggestion="Wait for training to complete or create a new LoRA",
        )

    # Check image count limits
    current_count = len(lora.images)
    new_count = len(input.images)
    total_count = current_count + new_count

    if total_count > lora.max_images:
        return error(
            code=ErrorCode.TOO_MANY_IMAGES,
            message=f"Would exceed maximum of {lora.max_images} images "
            f"(current: {current_count}, uploading: {new_count})",
            suggestion=f"Remove {total_count - lora.max_images} images from the upload",
        )

    # Process images
    now = _now()
    new_images = []

    for img in input.images:
        if "url" not in img:
            return error(
                code=ErrorCode.INVALID_TRAINING_DATA,
                message="Each image must have a 'url' field",
                suggestion="Provide images as [{url: '...', caption: '...'}]",
            )

        training_image = TrainingImage(
            filename=img.get("filename", f"image_{len(new_images)}.jpg"),
            url=img["url"],
            caption=img.get("caption"),
            uploaded_at=now,
        )
        new_images.append(training_image)

    # Update LoRA
    lora.images.extend(new_images)
    lora.status = LoraStatus.UPLOADING if total_count < lora.min_images else LoraStatus.READY_TO_TRAIN

    warnings = []
    suggestions = []

    if total_count < lora.min_images:
        warnings.append(
            Warning(
                code="INSUFFICIENT_IMAGES",
                message=f"Need at least {lora.min_images} images, have {total_count}",
            )
        )
        suggestions.append(f"Upload {lora.min_images - total_count} more images")
    elif total_count < 20:
        warnings.append(
            Warning(
                code="LOW_IMAGE_COUNT",
                message="20-30 images recommended for best results",
            )
        )
        suggestions.append("Consider uploading more diverse examples")
    else:
        suggestions.append("Ready to train: use lora.train to start")

    return success(
        data=UploadImagesOutput(lora=lora, uploaded_count=new_count),
        reasoning=f"Uploaded {new_count} images. Total: {total_count}/{lora.max_images}. "
        f"Status: {lora.status.value}",
        warnings=warnings if warnings else None,
        suggestions=suggestions if suggestions else None,
    )


async def train(input: TrainLoraInput) -> CommandResult[TrainLoraOutput]:
    """Start training on a LoRA project.
    
    Training typically takes 15-60 minutes depending on steps and base model.
    Use lora.status to monitor progress.
    """
    # Find the LoRA
    lora = _loras.get(input.lora_id)
    if not lora:
        return error(
            code=ErrorCode.LORA_NOT_FOUND,
            message=f"LoRA '{input.lora_id}' not found",
            suggestion="Use lora.list to see available LoRAs",
        )

    # Check status
    if lora.status == LoraStatus.TRAINING:
        return error(
            code=ErrorCode.TRAINING_IN_PROGRESS,
            message="Training is already in progress",
            suggestion="Use lora.status to check progress",
        )

    if lora.status == LoraStatus.COMPLETED:
        return error(
            code=ErrorCode.TRAINING_IN_PROGRESS,
            message="Training has already completed",
            suggestion="Use lora.activate to enable this LoRA for generation",
        )

    if lora.status not in [LoraStatus.CREATED, LoraStatus.UPLOADING, LoraStatus.READY_TO_TRAIN, LoraStatus.FAILED]:
        return error(
            code=ErrorCode.TRAINING_NOT_STARTED,
            message=f"Cannot start training from '{lora.status.value}' state",
            suggestion="LoRA must be in 'ready_to_train' state",
        )

    # Check minimum images
    if len(lora.images) < lora.min_images:
        return error(
            code=ErrorCode.INSUFFICIENT_IMAGES,
            message=f"Need at least {lora.min_images} images, have {len(lora.images)}",
            suggestion=f"Upload {lora.min_images - len(lora.images)} more images first",
        )

    # Start training (in MVP, this is simulated)
    now = _now()
    lora.status = LoraStatus.TRAINING
    lora.training_started_at = now
    lora.progress = 0
    lora.current_step = 0
    lora.error_message = None

    # Simulate training completion for MVP
    # In production, this would start a Replicate training job
    lora.status = LoraStatus.COMPLETED
    lora.completed_at = now
    lora.progress = 100
    lora.current_step = lora.steps
    lora.lora_url = f"https://storage.noisett.ai/loras/{lora.id}/weights.safetensors"

    return success(
        data=TrainLoraOutput(lora=lora),
        reasoning=f"Training completed for '{lora.name}' using {len(lora.images)} images. "
        f"LoRA is ready to use with trigger word '{lora.trigger_word}'.",
        suggestions=["Activate for generation: lora.activate", "Test with: asset.generate"],
    )


async def status(input: LoraStatusInput) -> CommandResult[LoraStatusOutput]:
    """Get the status of a LoRA project.
    
    Returns full details including training progress, images, and settings.
    """
    lora = _loras.get(input.lora_id)
    if not lora:
        return error(
            code=ErrorCode.LORA_NOT_FOUND,
            message=f"LoRA '{input.lora_id}' not found",
            suggestion="Use lora.list to see available LoRAs",
        )

    suggestions = []
    if lora.status == LoraStatus.CREATED:
        suggestions.append("Upload training images: lora.upload-images")
    elif lora.status == LoraStatus.READY_TO_TRAIN:
        suggestions.append("Start training: lora.train")
    elif lora.status == LoraStatus.TRAINING:
        suggestions.append("Training in progress. Check back for updates.")
    elif lora.status == LoraStatus.COMPLETED and not lora.is_active:
        suggestions.append("Activate for generation: lora.activate")
    elif lora.status == LoraStatus.FAILED:
        suggestions.append("Retry training: lora.train")

    return success(
        data=LoraStatusOutput(lora=lora),
        reasoning=f"LoRA '{lora.name}' is {lora.status.value}. "
        f"{len(lora.images)} training images. "
        f"{'Active' if lora.is_active else 'Not active'} for generation.",
        suggestions=suggestions if suggestions else None,
    )


async def list_loras(input: LoraListInput) -> CommandResult[LoraListOutput]:
    """List all LoRA projects.
    
    Optional filters: status, base_model, active_only.
    """
    loras = list(_loras.values())

    # Apply filters
    if input.status:
        loras = [l for l in loras if l.status == input.status]
    if input.base_model:
        loras = [l for l in loras if l.base_model == input.base_model]
    if input.active_only:
        loras = [l for l in loras if l.is_active]

    # Convert to LoraInfo summaries
    lora_infos = [
        LoraInfo(
            id=l.id,
            name=l.name,
            trigger_word=l.trigger_word,
            base_model=l.base_model,
            status=l.status,
            image_count=len(l.images),
            is_active=l.is_active,
            created_at=l.created_at,
        )
        for l in loras
    ]

    # Sort by creation date (newest first)
    lora_infos.sort(key=lambda x: x.created_at, reverse=True)

    filters_applied = []
    if input.status:
        filters_applied.append(f"status={input.status.value}")
    if input.base_model:
        filters_applied.append(f"base_model={input.base_model.value}")
    if input.active_only:
        filters_applied.append("active_only=true")

    filter_str = f" (filters: {', '.join(filters_applied)})" if filters_applied else ""

    return success(
        data=LoraListOutput(loras=lora_infos, total=len(lora_infos)),
        reasoning=f"Found {len(lora_infos)} LoRAs{filter_str}",
    )


async def activate(input: LoraActivateInput) -> CommandResult[LoraActivateOutput]:
    """Activate or deactivate a trained LoRA.
    
    Active LoRAs are available for use in asset.generate with the trigger word.
    """
    lora = _loras.get(input.lora_id)
    if not lora:
        return error(
            code=ErrorCode.LORA_NOT_FOUND,
            message=f"LoRA '{input.lora_id}' not found",
            suggestion="Use lora.list to see available LoRAs",
        )

    # Can only activate completed LoRAs
    if input.active and lora.status != LoraStatus.COMPLETED:
        return error(
            code=ErrorCode.LORA_NOT_READY,
            message=f"Cannot activate LoRA in '{lora.status.value}' state",
            suggestion="Wait for training to complete (status: completed)",
        )

    previous_state = "active" if lora.is_active else "inactive"
    lora.is_active = input.active
    new_state = "active" if lora.is_active else "inactive"

    suggestions = []
    if input.active:
        suggestions.append(
            f"Generate with: asset.generate --prompt '{lora.trigger_word} your description'"
        )

    return success(
        data=LoraActivateOutput(lora=lora),
        reasoning=f"LoRA '{lora.name}' changed from {previous_state} to {new_state}. "
        + (f"Use trigger word '{lora.trigger_word}' in prompts." if input.active else ""),
        suggestions=suggestions if suggestions else None,
    )


async def delete(input: LoraDeleteInput) -> CommandResult[LoraDeleteOutput]:
    """Delete a LoRA project.
    
    This permanently removes the LoRA and all associated training data.
    Use force=true to delete even if training is in progress.
    """
    lora = _loras.get(input.lora_id)
    if not lora:
        return error(
            code=ErrorCode.LORA_NOT_FOUND,
            message=f"LoRA '{input.lora_id}' not found",
            suggestion="Use lora.list to see available LoRAs",
        )

    # Check if active
    if lora.is_active:
        return error(
            code=ErrorCode.CANNOT_DELETE_ACTIVE,
            message="Cannot delete an active LoRA",
            suggestion="Deactivate first: lora.activate --lora_id ... --active false",
        )

    # Check if training in progress
    if lora.status == LoraStatus.TRAINING and not input.force:
        return error(
            code=ErrorCode.TRAINING_IN_PROGRESS,
            message="Cannot delete while training is in progress",
            suggestion="Wait for training to complete or use force=true to cancel and delete",
        )

    # Delete the LoRA
    name = lora.name
    del _loras[input.lora_id]

    return success(
        data=LoraDeleteOutput(deleted_id=input.lora_id, name=name),
        reasoning=f"Deleted LoRA '{name}' and all associated training data.",
    )


# =============================================================================
# Test Helpers
# =============================================================================


def reset_storage():
    """Reset in-memory storage. Used for testing."""
    global _loras
    _loras = {}
