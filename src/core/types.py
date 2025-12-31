"""Domain types for Noisett.

These types define the core domain model including asset types,
models, jobs, and generated images.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Available asset types for generation."""

    ICONS = "icons"
    PRODUCT = "product"
    LOGO = "logo"
    PREMIUM = "premium"


class ModelId(str, Enum):
    """Available image generation models."""

    HIDREAM = "hidream"
    FLUX = "flux"
    SD35 = "sd35"


class JobStatus(str, Enum):
    """Generation job status."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityPreset(str, Enum):
    """Generation quality presets."""

    DRAFT = "draft"  # Fast, lower quality
    STANDARD = "standard"  # Balanced
    HIGH = "high"  # Slower, higher quality


class GeneratedImage(BaseModel):
    """A single generated image."""

    index: int = Field(..., description="Image index in the batch (0-based)")
    url: str = Field(..., description="URL to access the generated image")
    width: int = Field(default=1024, description="Image width in pixels")
    height: int = Field(default=1024, description="Image height in pixels")
    seed: int | None = Field(default=None, description="Seed used for generation")


class Job(BaseModel):
    """Image generation job.
    
    Represents a single generation request that may produce multiple images.
    """

    id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    prompt: str = Field(..., description="Original prompt text")
    asset_type: AssetType = Field(..., description="Type of asset being generated")
    model: ModelId = Field(..., description="Model used for generation")
    quality: QualityPreset = Field(..., description="Quality preset selected")
    count: int = Field(..., ge=1, le=4, description="Number of images requested")
    progress: float = Field(default=0, ge=0, le=100, description="Progress percentage")
    images: list[GeneratedImage] = Field(
        default_factory=list, description="Generated images (populated when complete)"
    )
    created_at: datetime = Field(..., description="When the job was created")
    completed_at: datetime | None = Field(
        default=None, description="When the job completed"
    )
    error_message: str | None = Field(
        default=None, description="Error message if status is 'failed'"
    )


class Model(BaseModel):
    """Image generation model information."""

    id: ModelId = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable model name")
    description: str = Field(..., description="Model description")
    license: str = Field(..., description="License type")
    commercial_ok: bool = Field(..., description="Whether commercial use is allowed")
    available: bool = Field(..., description="Whether the model is currently available")
    default_steps: int = Field(..., description="Default inference steps")
    default_guidance: float = Field(..., description="Default guidance scale")


class AssetTypeInfo(BaseModel):
    """Asset type configuration and metadata."""

    id: AssetType = Field(..., description="Asset type identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Asset type description")
    prompt_template: str = Field(
        ..., description="Template applied to user prompts"
    )
    negative_prompt: str = Field(
        ..., description="Negative prompt for this asset type"
    )
    recommended_for: list[str] = Field(
        ..., description="Recommended use cases"
    )


# Default configurations for asset types
ASSET_TYPE_CONFIGS: dict[AssetType, AssetTypeInfo] = {
    AssetType.ICONS: AssetTypeInfo(
        id=AssetType.ICONS,
        name="Icons (Fluent 2)",
        description="Minimal vector-style icons for UI",
        prompt_template="{subject}, Fluent 2 design icon, minimal vector style, simple shapes, clean lines, professional UI icon",
        negative_prompt="photorealistic, 3d render, complex, detailed background, shadows",
        recommended_for=["UI elements", "app icons", "buttons", "navigation"],
    ),
    AssetType.PRODUCT: AssetTypeInfo(
        id=AssetType.PRODUCT,
        name="Product Illustrations",
        description="Clean illustrations for product pages and documentation",
        prompt_template="{subject}, product illustration style, clean modern design, soft gradients, professional, brand-aligned",
        negative_prompt="cluttered, amateur, stock photo, watermark, text",
        recommended_for=["documentation", "product pages", "feature callouts", "diagrams"],
    ),
    AssetType.LOGO: AssetTypeInfo(
        id=AssetType.LOGO,
        name="Logo Illustrations",
        description="Simple iconic illustrations for branding",
        prompt_template="{subject}, simple iconic illustration, minimal design, memorable, scalable, brand-friendly",
        negative_prompt="complex, detailed, photorealistic, busy background",
        recommended_for=["app tiles", "feature icons", "badges", "small graphics"],
    ),
    AssetType.PREMIUM: AssetTypeInfo(
        id=AssetType.PREMIUM,
        name="Premium Illustrations",
        description="Rich marketing-grade illustrations",
        prompt_template="{subject}, premium editorial illustration, high quality, detailed, professional marketing art, rich colors",
        negative_prompt="amateur, stock photo, generic, watermark, low quality",
        recommended_for=["marketing", "hero images", "campaigns", "presentations"],
    ),
}


# Default configurations for models
MODEL_CONFIGS: dict[ModelId, Model] = {
    ModelId.HIDREAM: Model(
        id=ModelId.HIDREAM,
        name="HiDream-I1",
        description="High-quality image generation model with commercial license",
        license="Apache-2.0",
        commercial_ok=True,
        available=True,
        default_steps=28,
        default_guidance=5.0,
    ),
    ModelId.FLUX: Model(
        id=ModelId.FLUX,
        name="FLUX.1-dev",
        description="State-of-the-art image generation (non-commercial)",
        license="FLUX.1-dev Non-Commercial License",
        commercial_ok=False,
        available=True,
        default_steps=30,
        default_guidance=3.5,
    ),
    ModelId.SD35: Model(
        id=ModelId.SD35,
        name="Stable Diffusion 3.5",
        description="Stable Diffusion with improved quality",
        license="Stability AI Community License",
        commercial_ok=True,
        available=False,  # Not yet integrated
        default_steps=28,
        default_guidance=7.0,
    ),
}


# =============================================================================
# LoRA Training Types (Phase 5)
# =============================================================================


class LoraStatus(str, Enum):
    """LoRA training job status."""

    CREATED = "created"  # Initial state, awaiting images
    UPLOADING = "uploading"  # Images being uploaded
    READY_TO_TRAIN = "ready_to_train"  # Images uploaded, awaiting train command
    TRAINING = "training"  # Training in progress
    COMPLETED = "completed"  # Training complete, LoRA ready
    FAILED = "failed"  # Training failed


class BaseModelType(str, Enum):
    """Base models supported for LoRA training."""

    FLUX = "flux"  # FLUX.1-dev
    SDXL = "sdxl"  # Stable Diffusion XL


class TrainingImage(BaseModel):
    """A single training image with optional caption."""

    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="URL to access the image")
    caption: str | None = Field(
        default=None, description="Optional caption/description for the image"
    )
    uploaded_at: datetime = Field(..., description="When the image was uploaded")


class Lora(BaseModel):
    """LoRA training job and model.
    
    Represents a LoRA fine-tuning project from creation through training to deployment.
    """

    id: str = Field(..., description="Unique LoRA identifier")
    name: str = Field(..., description="Human-readable name")
    description: str | None = Field(
        default=None, description="Optional description of what this LoRA captures"
    )
    trigger_word: str = Field(
        ..., description="Word/phrase to trigger this style in prompts"
    )
    base_model: BaseModelType = Field(..., description="Base model for fine-tuning")
    status: LoraStatus = Field(..., description="Current training status")
    
    # Training data
    images: list[TrainingImage] = Field(
        default_factory=list, description="Training images"
    )
    min_images: int = Field(default=10, description="Minimum images required")
    max_images: int = Field(default=100, description="Maximum images allowed")
    
    # Training parameters
    steps: int = Field(default=1000, ge=100, le=5000, description="Training steps")
    learning_rate: float = Field(
        default=1e-4, gt=0, lt=1, description="Learning rate"
    )
    
    # Output
    lora_url: str | None = Field(
        default=None, description="URL to download trained LoRA weights"
    )
    is_active: bool = Field(
        default=False, description="Whether this LoRA is active for generation"
    )
    
    # Timestamps
    created_at: datetime = Field(..., description="When the LoRA was created")
    training_started_at: datetime | None = Field(
        default=None, description="When training started"
    )
    completed_at: datetime | None = Field(
        default=None, description="When training completed"
    )
    
    # Progress tracking
    progress: float = Field(
        default=0, ge=0, le=100, description="Training progress percentage"
    )
    current_step: int = Field(default=0, ge=0, description="Current training step")
    
    # Error handling
    error_message: str | None = Field(
        default=None, description="Error message if status is 'failed'"
    )


class LoraInfo(BaseModel):
    """Summary info for LoRA listing."""

    id: str = Field(..., description="Unique LoRA identifier")
    name: str = Field(..., description="Human-readable name")
    trigger_word: str = Field(..., description="Trigger word for this style")
    base_model: BaseModelType = Field(..., description="Base model")
    status: LoraStatus = Field(..., description="Current status")
    image_count: int = Field(..., description="Number of training images")
    is_active: bool = Field(..., description="Whether currently active")
    created_at: datetime = Field(..., description="When created")


# =============================================================================
# Quality Pipeline Types (Phase 6)
# =============================================================================


class UpscaleModel(str, Enum):
    """Available upscaling models."""

    REAL_ESRGAN = "real-esrgan"  # Fast, good general quality
    SUPIR = "supir"  # Slow, excellent quality


class OutputFormat(str, Enum):
    """Output image formats."""

    PNG = "png"  # Lossless, best for icons
    WEBP = "webp"  # Efficient web format
    JPEG = "jpeg"  # Lossy, smaller files


class QualityPresetInfo(BaseModel):
    """Quality preset configuration and metadata."""

    name: QualityPreset = Field(..., description="Preset identifier")
    steps: int = Field(..., description="Number of inference steps")
    width: int = Field(..., description="Output width in pixels")
    height: int = Field(..., description="Output height in pixels")
    use_refiner: bool = Field(..., description="Whether to apply refinement pass")
    use_upscaler: bool = Field(..., description="Whether to upscale output")
    description: str = Field(..., description="Human-readable description")
    estimated_seconds: int = Field(..., description="Estimated generation time")


# Quality preset configurations
QUALITY_PRESET_CONFIGS: dict[QualityPreset, QualityPresetInfo] = {
    QualityPreset.DRAFT: QualityPresetInfo(
        name=QualityPreset.DRAFT,
        steps=4,
        width=512,
        height=512,
        use_refiner=False,
        use_upscaler=False,
        description="Quick ideation, lower quality",
        estimated_seconds=2,
    ),
    QualityPreset.STANDARD: QualityPresetInfo(
        name=QualityPreset.STANDARD,
        steps=8,
        width=1024,
        height=1024,
        use_refiner=False,
        use_upscaler=False,
        description="Balanced quality for most use cases",
        estimated_seconds=5,
    ),
    QualityPreset.HIGH: QualityPresetInfo(
        name=QualityPreset.HIGH,
        steps=12,
        width=1024,
        height=1024,
        use_refiner=False,
        use_upscaler=True,
        description="Higher quality with upscaling",
        estimated_seconds=10,
    ),
}


class RefinedImage(BaseModel):
    """A refined image with metadata."""

    url: str = Field(..., description="URL to access the refined image")
    original_url: str = Field(..., description="URL of the original image")
    denoise_strength: float = Field(..., description="Denoise strength used")
    steps: int = Field(..., description="Number of refinement steps")


class UpscaledImage(BaseModel):
    """An upscaled image with metadata."""

    url: str = Field(..., description="URL to access the upscaled image")
    original_url: str = Field(..., description="URL of the original image")
    scale: int = Field(..., description="Upscale factor (2 or 4)")
    model: UpscaleModel = Field(..., description="Upscaling model used")
    width: int = Field(..., description="Output width in pixels")
    height: int = Field(..., description="Output height in pixels")


class ImageVariation(BaseModel):
    """A single image variation."""

    index: int = Field(..., description="Variation index (0-based)")
    url: str = Field(..., description="URL to access the variation")
    seed: int = Field(..., description="Seed used for this variation")


class PostProcessedImage(BaseModel):
    """A post-processed image with metadata."""

    url: str = Field(..., description="URL to access the processed image")
    original_url: str = Field(..., description="URL of the original image")
    format: OutputFormat = Field(..., description="Output format")
    sharpened: bool = Field(..., description="Whether sharpening was applied")
    color_corrected: bool = Field(..., description="Whether color correction was applied")


# =============================================================================
# Auth & History Types (Phase 8)
# =============================================================================


class User(BaseModel):
    """Authenticated user information extracted from JWT."""

    user_id: str = Field(..., description="Unique user identifier (Entra ID oid)")
    email: str | None = Field(default=None, description="User's email address")
    name: str | None = Field(default=None, description="User's display name")


class GenerationRecord(BaseModel):
    """A single generation record for history."""

    job_id: str = Field(..., description="Original job ID")
    user_id: str = Field(..., description="User who generated this")
    prompt: str = Field(..., description="Original prompt text")
    asset_type: AssetType = Field(..., description="Asset type used")
    quality: QualityPreset | None = Field(default=None, description="Quality preset used")
    model: ModelId | None = Field(default=None, description="Model used for generation")
    images: list[str] = Field(default_factory=list, description="List of image URLs")
    created_at: datetime = Field(..., description="When the generation occurred")


class Favorite(BaseModel):
    """A favorited image."""

    user_id: str = Field(..., description="User who favorited")
    job_id: str = Field(..., description="Job ID of the generation")
    image_index: int = Field(..., ge=0, le=7, description="Index of favorited image")
    image_url: str = Field(..., description="URL of the favorited image")
    prompt: str | None = Field(default=None, description="Original prompt")
    created_at: datetime = Field(..., description="When the favorite was added")


class HistoryListInput(BaseModel):
    """Input for listing generation history."""

    limit: int = Field(default=50, ge=1, le=200, description="Max results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class HistoryListOutput(BaseModel):
    """Output for listing generation history."""

    generations: list[GenerationRecord] = Field(..., description="Generation records")
    total_count: int = Field(..., description="Total number of generations")
    has_more: bool = Field(..., description="Whether more results exist")


class FavoriteInput(BaseModel):
    """Input for adding/removing a favorite."""

    job_id: str = Field(..., description="Job ID of the generation")
    image_index: int = Field(..., ge=0, le=7, description="Index of image to favorite")


class FavoritesListOutput(BaseModel):
    """Output for listing favorites."""

    favorites: list[Favorite] = Field(..., description="Favorited images")
    total_count: int = Field(..., description="Total number of favorites")
