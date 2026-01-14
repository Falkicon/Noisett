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
import time
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from ..core.errors import ErrorCode
from afd.core import CommandResult, Warning, error, success
from afd.core.handoff import create_handoff
from ..core.convex_client import get_convex_client, ConvexError
from ..core.types import (
    BaseModelType,
    Lora,
    LoraInfo,
    LoraStatus,
    TrainingImage,
)


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_lora_id() -> str:
    """Generate a unique LoRA ID."""
    return f"lora_{uuid.uuid4().hex[:12]}"


def _now() -> datetime:
    """Get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


def _now_timestamp() -> int:
    """Get current UTC time as timestamp in milliseconds."""
    return int(time.time() * 1000)


def _datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to timestamp in milliseconds."""
    return int(dt.timestamp() * 1000)


def _timestamp_to_datetime(ts: int) -> datetime:
    """Convert timestamp in milliseconds to datetime."""
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)


async def _convex_to_lora(convex_data: dict, convex_client=None) -> Lora:
    """Convert Convex LoRA data to Lora object.

    Args:
        convex_data: LoRA data from Convex
        convex_client: Optional Convex client for loading training images
    """
    images = []

    # Load training images if client is provided
    if convex_client:
        try:
            training_images = await convex_client.list_training_images_by_lora(convex_data["_id"])
            images = [
                TrainingImage(
                    filename=img["filename"],
                    url=f"convex-storage://{img['storageId']}",  # Use storage ID as URL
                    caption=img.get("caption"),
                    uploaded_at=_timestamp_to_datetime(img["uploadedAt"]),
                )
                for img in training_images
            ]
        except Exception:
            # If loading images fails, continue without them
            # This maintains backwards compatibility
            pass

    return Lora(
        id=convex_data["_id"],
        name=convex_data["name"],
        description=convex_data.get("description"),
        trigger_word=convex_data["triggerWord"],
        base_model=BaseModelType(convex_data["baseModel"]),
        status=LoraStatus(convex_data["status"]),
        steps=convex_data["steps"],
        learning_rate=1e-4,  # Default learning rate, not stored in Convex yet
        is_active=convex_data["isActive"],
        created_at=_timestamp_to_datetime(convex_data["createdAt"]),
        training_started_at=_timestamp_to_datetime(convex_data["trainStartedAt"]) if convex_data.get("trainStartedAt") else None,
        completed_at=_timestamp_to_datetime(convex_data["completedAt"]) if convex_data.get("completedAt") else None,
        progress=convex_data.get("progress", 0),  # Default to 0 if None
        current_step=convex_data.get("currentStep", 0),  # Default to 0 if None
        error_message=convex_data.get("errorMessage"),
        images=images,
    )


def _lora_to_convex(lora: Lora, lora_id: str = None) -> dict:
    """Convert Lora object to Convex data."""
    convex_data = {
        "name": lora.name,
        "triggerWord": lora.trigger_word,
        "description": lora.description,
        "baseModel": lora.base_model.value,
        "status": lora.status.value,
        "steps": lora.steps,
        "isActive": lora.is_active,
        "createdAt": _datetime_to_timestamp(lora.created_at),
    }

    if lora.training_started_at:
        convex_data["trainStartedAt"] = _datetime_to_timestamp(lora.training_started_at)
    if lora.completed_at:
        convex_data["completedAt"] = _datetime_to_timestamp(lora.completed_at)
    if lora.progress is not None:
        convex_data["progress"] = lora.progress
    if lora.current_step is not None:
        convex_data["currentStep"] = lora.current_step
    if lora.error_message:
        convex_data["errorMessage"] = lora.error_message

    return convex_data


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
        description="List of images with either 'url' (Phase 1) or 'storage_id' (Phase 2) and optional metadata",
    )


class UploadImagesOutput(BaseModel):
    """Output for lora.upload-images command."""

    lora: Lora = Field(..., description="Updated LoRA project")
    uploaded_count: int = Field(..., description="Number of images uploaded")


class TrainLoraInput(BaseModel):
    """Input for lora.train command."""

    lora_id: str = Field(..., description="ID of the LoRA project to train")


class TrainLoraOutput(BaseModel):
    """Output for lora.train command (non-handoff mode)."""

    lora: Lora = Field(..., description="LoRA project with training started")


class TrainLoraHandoffOutput(BaseModel):
    """Output for lora.train command with SSE handoff.
    
    Contains the handoff result with SSE endpoint for progress streaming.
    """

    protocol: str = Field(default="sse", description="Protocol type")
    endpoint: str = Field(..., description="SSE endpoint for training events")
    lora_id: str = Field(..., description="LoRA ID being trained")
    credentials: dict | None = Field(default=None, description="Auth credentials if needed")


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
    try:
        convex = get_convex_client()

        # Check for duplicate trigger word
        existing_lora = await convex.get_lora_by_trigger_word(input.trigger_word.lower())
        if existing_lora:
            return error(
                code=ErrorCode.LORA_ALREADY_EXISTS,
                message=f"Trigger word '{input.trigger_word}' is already in use",
                suggestion="Use a different trigger word",
            )

        # Create the LoRA
        now = _now()
        lora = Lora(
            id="",  # Will be set from Convex
            name=input.name,
            description=input.description,
            trigger_word=input.trigger_word,
            base_model=input.base_model,
            status=LoraStatus.CREATED,
            steps=input.steps,
            learning_rate=input.learning_rate,
            created_at=now,
        )

        # Convert to Convex format and create
        convex_data = _lora_to_convex(lora)
        lora_id = await convex.create_lora(convex_data)
        lora.id = lora_id

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

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to create LoRA: {e}",
            suggestion="Please try again",
        )


async def upload_images(input: UploadImagesInput) -> CommandResult[UploadImagesOutput]:
    """Upload training images to a LoRA project.

    Phase 2: Now supports real Convex file storage with validation.
    Images should be high-quality examples of the style you want to capture.
    Recommended: 20-30 diverse images showing variations of the concept.

    Supports two input formats:
    - Phase 1 (URLs): [{"url": "...", "caption": "..."}]
    - Phase 2 (Storage IDs): [{"storage_id": "...", "filename": "...", "width": 512, "height": 512, "size_bytes": 1024000}]
    """
    try:
        convex = get_convex_client()

        # Find the LoRA
        convex_lora = await convex.get_lora(input.lora_id)
        if not convex_lora:
            return error(
                code=ErrorCode.LORA_NOT_FOUND,
                message=f"LoRA '{input.lora_id}' not found",
                suggestion="Use lora.list to see available LoRAs",
            )

        lora = await _convex_to_lora(convex_lora, convex)

        # Check status - can only upload in CREATED, UPLOADING, or READY_TO_TRAIN state
        valid_statuses = [LoraStatus.CREATED, LoraStatus.UPLOADING, LoraStatus.READY_TO_TRAIN]
        if lora.status not in valid_statuses:
            return error(
                code=ErrorCode.TRAINING_IN_PROGRESS,
                message=f"Cannot upload images while LoRA is in '{lora.status.value}' state",
                suggestion="Wait for training to complete or create a new LoRA",
            )

        # Determine input format and validate
        is_phase2 = any("storage_id" in img for img in input.images)
        is_phase1 = any("url" in img for img in input.images)

        if is_phase1 and is_phase2:
            return error(
                code=ErrorCode.INVALID_TRAINING_DATA,
                message="Mixed input formats not supported - use either URLs or storage IDs",
                suggestion="Provide either Phase 1 format [{url: '...'}] or Phase 2 format [{storage_id: '...', filename: '...'}]",
            )

        # Validate collection size first
        from src.core.image_validation import validate_image_collection, CollectionValidationError

        try:
            collection_warnings = validate_image_collection(len(input.images))
        except CollectionValidationError as e:
            return error(
                code=ErrorCode.TOO_MANY_IMAGES if "too many" in e.message.lower() else ErrorCode.INVALID_TRAINING_DATA,
                message=e.message,
                suggestion="Adjust the number of training images",
            )

        if is_phase2:
            # Phase 2: Handle storage IDs with validation and Convex storage
            training_images = []
            all_warnings = collection_warnings.copy()

            for img in input.images:
                # Validate required fields
                if "storage_id" not in img or "filename" not in img:
                    return error(
                        code=ErrorCode.INVALID_TRAINING_DATA,
                        message="Phase 2 format requires 'storage_id' and 'filename' fields",
                        suggestion="Provide: {storage_id: '...', filename: '...', width: 512, height: 512, size_bytes: 1024000}",
                    )

                # Validate dimensions if provided
                width = img.get("width")
                height = img.get("height")
                if width and height:
                    if width < 512 or height < 512:
                        return error(
                            code=ErrorCode.INVALID_TRAINING_DATA,
                            message=f"Image '{img['filename']}' dimensions {width}x{height} are too small (minimum 512x512)",
                            suggestion="Use images with at least 512x512 resolution",
                        )

                # Create training image record in Convex
                image_data = {
                    "loraId": input.lora_id,
                    "storageId": img["storage_id"],
                    "filename": img["filename"],
                    "caption": img.get("caption"),
                    "sizeBytes": img.get("size_bytes", 0),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "uploadedAt": int(_now().timestamp() * 1000),
                }

                training_image_id = await convex.create_training_image(image_data)

                # Create TrainingImage object for response
                training_images.append(
                    TrainingImage(
                        filename=img["filename"],
                        url=f"convex-storage://{img['storage_id']}",  # Use storage ID as URL
                        caption=img.get("caption"),
                        uploaded_at=_now(),
                    )
                )

            # Get updated image count
            total_images = await convex.count_training_images_by_lora(input.lora_id)

        else:
            # Phase 1: Handle URLs (backwards compatibility)
            for img in input.images:
                if "url" not in img:
                    return error(
                        code=ErrorCode.INVALID_TRAINING_DATA,
                        message="Phase 1 format requires 'url' field",
                        suggestion="Provide images as [{url: '...', caption: '...'}]",
                    )

            # For Phase 1, simulate without actual storage
            total_images = len(input.images)
            all_warnings = collection_warnings.copy()
            training_images = [
                TrainingImage(
                    filename=img.get("filename", f"image_{i}.jpg"),
                    url=img["url"],
                    caption=img.get("caption"),
                    uploaded_at=_now(),
                )
                for i, img in enumerate(input.images)
            ]

        # Update LoRA status based on image count
        min_images = 5
        new_status = LoraStatus.READY_TO_TRAIN if total_images >= min_images else LoraStatus.UPLOADING

        # Update LoRA in Convex
        await convex.update_lora(input.lora_id, {"status": new_status.value})

        # Update local LoRA object
        lora.status = new_status
        lora.images = training_images

        # Convert warnings to Warning objects
        warning_objects = []
        suggestions = []

        for w in all_warnings:
            warning_objects.append(Warning(code="IMAGE_VALIDATION_WARNING", message=w))

        if total_images < min_images:
            warning_objects.append(
                Warning(
                    code="INSUFFICIENT_IMAGES",
                    message=f"Need at least {min_images} images, have {total_images}",
                )
            )
            suggestions.append(f"Upload {min_images - total_images} more images")
        elif total_images >= min_images:
            suggestions.append("Ready to train: use lora.train to start")

        return success(
            data=UploadImagesOutput(lora=lora, uploaded_count=len(input.images)),
            reasoning=f"{'Stored' if is_phase2 else 'Uploaded'} {len(input.images)} images. "
            f"Total: {total_images}. Status: {lora.status.value}.",
            warnings=warning_objects if warning_objects else None,
            suggestions=suggestions if suggestions else None,
        )

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to upload images: {e}",
            suggestion="Please try again",
        )


async def train(input: TrainLoraInput) -> CommandResult[TrainLoraOutput]:
    """Start training on a LoRA project.

    Training typically takes 15-60 minutes depending on steps and base model.
    Use lora.status to monitor progress.

    Note: Phase 1 implementation - actual training will be implemented in Phase 3.
    """
    try:
        convex = get_convex_client()

        # Find the LoRA
        convex_lora = await convex.get_lora(input.lora_id)
        if not convex_lora:
            return error(
                code=ErrorCode.LORA_NOT_FOUND,
                message=f"LoRA '{input.lora_id}' not found",
                suggestion="Use lora.list to see available LoRAs",
            )

        lora = await _convex_to_lora(convex_lora, convex)

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

        # For Phase 1, check minimum images (simulated)
        min_images = 5
        image_count = len(lora.images)  # This is simulated in Phase 1

        if image_count < min_images:
            return error(
                code=ErrorCode.INSUFFICIENT_IMAGES,
                message=f"Need at least {min_images} images, have {image_count}",
                suggestion=f"Upload {min_images - image_count} more images first",
            )

        # Update LoRA to training state
        now = _now()
        updates = {
            "status": LoraStatus.TRAINING.value,
            "trainStartedAt": _datetime_to_timestamp(now),
            "progress": 0,
            "currentStep": 0,
            "errorMessage": None,
        }

        await convex.update_lora(input.lora_id, updates)

        # Update local LoRA object
        lora.status = LoraStatus.TRAINING
        lora.training_started_at = now
        lora.progress = 0
        lora.current_step = 0
        lora.error_message = None

        # Create SSE handoff for real-time progress
        # In Phase 3: start Replicate training job and return handoff
        handoff = create_handoff(
            protocol="sse",
            endpoint=f"/api/training/{lora.id}/events",
            capabilities=["progress", "logs", "completion"],
            reconnect_allowed=True,
            reconnect_max_attempts=5,
            reconnect_backoff_ms=1000,
            description=f"Training progress for '{lora.name}'",
        )

        return success(
            data=handoff,
            reasoning=f"Training started for '{lora.name}'. Connect to SSE endpoint for real-time progress. "
            f"Note: Phase 1 - actual training will be implemented in Phase 3.",
            suggestions=[
                f"Connect to SSE: /api/training/{lora.id}/events",
                "Check status: lora.status",
            ],
        )

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to start training: {e}",
            suggestion="Please try again",
        )


async def status(input: LoraStatusInput) -> CommandResult[LoraStatusOutput]:
    """Get the status of a LoRA project.

    Returns full details including training progress, images, and settings.
    """
    try:
        convex = get_convex_client()

        convex_lora = await convex.get_lora(input.lora_id)
        if not convex_lora:
            return error(
                code=ErrorCode.LORA_NOT_FOUND,
                message=f"LoRA '{input.lora_id}' not found",
                suggestion="Use lora.list to see available LoRAs",
            )

        lora = await _convex_to_lora(convex_lora, convex)

        suggestions = []
        if lora.status == LoraStatus.CREATED:
            suggestions.append("Upload training images: lora.upload-images")
        elif lora.status == LoraStatus.READY_TO_TRAIN:
            suggestions.append("Start training: lora.train")
        elif lora.status == LoraStatus.TRAINING:
            suggestions.append("Training in progress. Check back for updates.")
        elif lora.status in [LoraStatus.COMPLETED, LoraStatus.DEPLOYED] and not lora.is_active:
            suggestions.append("Activate for generation: lora.activate")
        elif lora.status == LoraStatus.FAILED:
            suggestions.append("Retry training: lora.train")
        elif lora.status == LoraStatus.DEPLOYMENT_FAILED:
            suggestions.append("Retry deployment: lora.deploy")

        return success(
            data=LoraStatusOutput(lora=lora),
            reasoning=f"LoRA '{lora.name}' is {lora.status.value}. "
            f"{len(lora.images)} training images. "
            f"{'Active' if lora.is_active else 'Not active'} for generation.",
            suggestions=suggestions if suggestions else None,
        )

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to get LoRA status: {e}",
            suggestion="Please try again",
        )


async def list_loras(input: LoraListInput) -> CommandResult[LoraListOutput]:
    """List all LoRA projects.

    Optional filters: status, base_model, active_only.
    """
    try:
        convex = get_convex_client()

        # Get LoRAs with filters
        convex_loras = await convex.list_loras(
            status=input.status.value if input.status else None,
            base_model=input.base_model.value if input.base_model else None,
            active_only=input.active_only
        )

        # Convert to LoraInfo summaries
        lora_infos = []
        for convex_lora in convex_loras:
            # Get image count for Phase 2
            image_count = await convex.count_training_images_by_lora(convex_lora["_id"])

            lora_info = LoraInfo(
                id=convex_lora["_id"],
                name=convex_lora["name"],
                trigger_word=convex_lora["triggerWord"],
                base_model=BaseModelType(convex_lora["baseModel"]),
                status=LoraStatus(convex_lora["status"]),
                image_count=image_count,
                is_active=convex_lora["isActive"],
                created_at=_timestamp_to_datetime(convex_lora["createdAt"]),
            )
            lora_infos.append(lora_info)

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

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to list LoRAs: {e}",
            suggestion="Please try again",
        )


async def activate(input: LoraActivateInput) -> CommandResult[LoraActivateOutput]:
    """Activate or deactivate a trained LoRA.

    Active LoRAs are available for use in asset.generate with the trigger word.
    """
    try:
        convex = get_convex_client()

        convex_lora = await convex.get_lora(input.lora_id)
        if not convex_lora:
            return error(
                code=ErrorCode.LORA_NOT_FOUND,
                message=f"LoRA '{input.lora_id}' not found",
                suggestion="Use lora.list to see available LoRAs",
            )

        lora = await _convex_to_lora(convex_lora, convex)

        # Can only activate completed/deployed LoRAs
        if input.active and lora.status not in [LoraStatus.COMPLETED, LoraStatus.DEPLOYED]:
            return error(
                code=ErrorCode.LORA_NOT_READY,
                message=f"Cannot activate LoRA in '{lora.status.value}' state",
                suggestion="Wait for training to complete (status: completed or deployed)",
            )

        previous_state = "active" if lora.is_active else "inactive"
        new_state = "active" if input.active else "inactive"

        # Update LoRA in Convex
        await convex.update_lora(input.lora_id, {"isActive": input.active})

        # Update local LoRA object
        lora.is_active = input.active

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

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to update LoRA: {e}",
            suggestion="Please try again",
        )


async def delete(input: LoraDeleteInput) -> CommandResult[LoraDeleteOutput]:
    """Delete a LoRA project.

    This permanently removes the LoRA and all associated training data.
    Use force=true to delete even if training is in progress.
    """
    try:
        convex = get_convex_client()

        convex_lora = await convex.get_lora(input.lora_id)
        if not convex_lora:
            return error(
                code=ErrorCode.LORA_NOT_FOUND,
                message=f"LoRA '{input.lora_id}' not found",
                suggestion="Use lora.list to see available LoRAs",
            )

        lora = await _convex_to_lora(convex_lora, convex)

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

        # Delete training images first
        name = lora.name
        await convex.delete_training_images_by_lora(input.lora_id)

        # Delete the LoRA from Convex
        await convex.delete_lora(input.lora_id)

        return success(
            data=LoraDeleteOutput(deleted_id=input.lora_id, name=name),
            reasoning=f"Deleted LoRA '{name}' and all associated training data.",
        )

    except ConvexError as e:
        return error(
            code=ErrorCode.STORAGE_ERROR,
            message=f"Failed to delete LoRA: {e}",
            suggestion="Please try again",
        )


# =============================================================================
# Test Helpers
# =============================================================================


async def reset_storage():
    """Reset Convex storage. Used for testing.

    Note: This is a placeholder for Phase 1. In future phases, this would
    clear the Convex database for testing purposes.
    """
    # TODO: Implement Convex database clearing for testing
    pass
