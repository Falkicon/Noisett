"""Domain types for Noisett.

These types define the core domain model including asset types,
models, jobs, and generated images.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

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
    seed: Optional[int] = Field(default=None, description="Seed used for generation")


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
    images: List[GeneratedImage] = Field(
        default_factory=list, description="Generated images (populated when complete)"
    )
    created_at: datetime = Field(..., description="When the job was created")
    completed_at: Optional[datetime] = Field(
        default=None, description="When the job completed"
    )
    error_message: Optional[str] = Field(
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
    recommended_for: List[str] = Field(
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
