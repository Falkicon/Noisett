"""Quality Pipeline commands for Noisett.

Phase 6: Multi-stage refinement, upscaling, variations, and post-processing.

Commands:
- quality.presets: List available quality presets
- refine: Apply refinement pass to an image
- upscale: Upscale an image using AI upscalers
- variations: Generate variations of an existing image
- post-process: Apply post-processing (sharpen, color correct, format)
"""

import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode
from src.core.result import CommandResult, error, success
from src.core.types import (
    ImageVariation,
    OutputFormat,
    PostProcessedImage,
    QualityPreset,
    QualityPresetInfo,
    QUALITY_PRESET_CONFIGS,
    RefinedImage,
    UpscaledImage,
    UpscaleModel,
)


def _now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# =============================================================================
# quality.presets Command
# =============================================================================


class QualityPresetsInput(BaseModel):
    """Input for quality.presets command."""

    pass  # No input required


class QualityPresetsOutput(BaseModel):
    """Output for quality.presets command."""

    presets: list[QualityPresetInfo] = Field(..., description="Available quality presets")
    total: int = Field(..., description="Total number of presets")


async def presets(input: QualityPresetsInput) -> CommandResult[QualityPresetsOutput]:
    """List available quality presets.
    
    Returns all quality preset configurations with their settings
    and estimated generation times.
    """
    preset_list = list(QUALITY_PRESET_CONFIGS.values())
    
    return success(
        data=QualityPresetsOutput(
            presets=preset_list,
            total=len(preset_list),
        ),
        reasoning=f"Found {len(preset_list)} quality presets: {', '.join(p.name.value for p in preset_list)}",
    )


# =============================================================================
# refine Command
# =============================================================================


class RefineInput(BaseModel):
    """Input for refine command."""

    image_url: str = Field(..., description="URL of the image to refine")
    denoise_strength: float = Field(
        default=0.3,
        ge=0.1,
        le=0.5,
        description="Denoise strength (0.1-0.5, lower preserves more of original)",
    )
    steps: int = Field(
        default=20,
        ge=10,
        le=50,
        description="Number of refinement steps",
    )
    prompt: str | None = Field(
        default=None,
        description="Optional prompt to guide refinement",
    )


class RefineOutput(BaseModel):
    """Output for refine command."""

    refined: RefinedImage = Field(..., description="Refined image details")


async def refine(input: RefineInput) -> CommandResult[RefineOutput]:
    """Apply refinement pass to an image.
    
    Uses img2img at low denoise to add detail while preserving composition.
    Best for premium illustrations and marketing assets.
    
    MVP: Returns mock refined image URL.
    """
    # Validate URL format
    if not input.image_url.startswith(("http://", "https://")):
        return error(
            code=ErrorCode.IMAGE_URL_INVALID.value,
            message="Image URL must start with http:// or https://",
            suggestion="Provide a valid URL to an image",
        )
    
    # MVP: Simulate refinement by returning mock URL
    # In production, this would call Fireworks/Replicate img2img API
    
    # Generate mock refined image path
    temp_dir = Path(tempfile.gettempdir()) / "noisett" / "refined"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(_now().timestamp())
    refined_path = temp_dir / f"refined_{timestamp}_{int(input.denoise_strength * 100)}.jpg"
    
    # MVP: Just create a placeholder file reference
    refined_url = f"file://{refined_path}"
    
    refined_image = RefinedImage(
        url=refined_url,
        original_url=input.image_url,
        denoise_strength=input.denoise_strength,
        steps=input.steps,
    )
    
    return success(
        data=RefineOutput(refined=refined_image),
        reasoning=f"Applied refinement with denoise={input.denoise_strength}, steps={input.steps}",
        suggestions=["Use denoise 0.2-0.3 for subtle improvements, 0.4-0.5 for more dramatic changes"],
    )


# =============================================================================
# upscale Command
# =============================================================================


class UpscaleInput(BaseModel):
    """Input for upscale command."""

    image_url: str = Field(..., description="URL of the image to upscale")
    scale: Literal[2, 4] = Field(
        default=2,
        description="Upscale factor (2x or 4x)",
    )
    model: UpscaleModel = Field(
        default=UpscaleModel.REAL_ESRGAN,
        description="Upscaling model to use",
    )


class UpscaleOutput(BaseModel):
    """Output for upscale command."""

    upscaled: UpscaledImage = Field(..., description="Upscaled image details")


async def upscale(input: UpscaleInput) -> CommandResult[UpscaleOutput]:
    """Upscale an image using AI upscalers.
    
    Supports 2x and 4x upscaling with Real-ESRGAN (fast) or SUPIR (high quality).
    
    MVP: Returns mock upscaled image URL.
    """
    # Validate URL format
    if not input.image_url.startswith(("http://", "https://")):
        return error(
            code=ErrorCode.IMAGE_URL_INVALID.value,
            message="Image URL must start with http:// or https://",
            suggestion="Provide a valid URL to an image",
        )
    
    # MVP: Simulate upscaling
    # In production, this would call Replicate Real-ESRGAN or SUPIR API
    
    # Assume original is 1024x1024
    original_width = 1024
    original_height = 1024
    new_width = original_width * input.scale
    new_height = original_height * input.scale
    
    temp_dir = Path(tempfile.gettempdir()) / "noisett" / "upscaled"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(_now().timestamp())
    upscaled_path = temp_dir / f"upscaled_{input.scale}x_{input.model.value}_{timestamp}.jpg"
    
    upscaled_url = f"file://{upscaled_path}"
    
    upscaled_image = UpscaledImage(
        url=upscaled_url,
        original_url=input.image_url,
        scale=input.scale,
        model=input.model,
        width=new_width,
        height=new_height,
    )
    
    model_note = "fast, good quality" if input.model == UpscaleModel.REAL_ESRGAN else "slow, excellent quality"
    
    return success(
        data=UpscaleOutput(upscaled=upscaled_image),
        reasoning=f"Upscaled {input.scale}x using {input.model.value} ({model_note}) to {new_width}x{new_height}",
        suggestions=[
            "Use 2x for most cases, 4x for print/large displays",
            "SUPIR produces better results but is slower",
        ],
    )


# =============================================================================
# variations Command
# =============================================================================


class VariationsInput(BaseModel):
    """Input for variations command."""

    source_image: str = Field(..., description="URL of the source image")
    count: int = Field(
        default=4,
        ge=1,
        le=8,
        description="Number of variations to generate (1-8)",
    )
    variation_strength: float = Field(
        default=0.3,
        ge=0.1,
        le=0.7,
        description="How different from original (0.1=similar, 0.7=very different)",
    )
    prompt: str | None = Field(
        default=None,
        description="Optional prompt to guide variations",
    )


class VariationsOutput(BaseModel):
    """Output for variations command."""

    variations: list[ImageVariation] = Field(..., description="Generated variations")
    source_image: str = Field(..., description="URL of the source image")
    variation_strength: float = Field(..., description="Strength used")


async def variations(input: VariationsInput) -> CommandResult[VariationsOutput]:
    """Generate variations of an existing image.
    
    Creates multiple alternative versions while maintaining the overall style
    and composition of the original.
    
    MVP: Returns mock variation URLs.
    """
    # Validate URL format
    if not input.source_image.startswith(("http://", "https://")):
        return error(
            code=ErrorCode.IMAGE_URL_INVALID.value,
            message="Source image URL must start with http:// or https://",
            suggestion="Provide a valid URL to an image",
        )
    
    # MVP: Simulate variation generation
    # In production, this would call img2img with different seeds
    
    temp_dir = Path(tempfile.gettempdir()) / "noisett" / "variations"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(_now().timestamp())
    variation_list: list[ImageVariation] = []
    
    for i in range(input.count):
        seed = random.randint(1, 999999999)
        var_path = temp_dir / f"variation_{timestamp}_{i}_{seed}.jpg"
        
        variation_list.append(ImageVariation(
            index=i,
            url=f"file://{var_path}",
            seed=seed,
        ))
    
    return success(
        data=VariationsOutput(
            variations=variation_list,
            source_image=input.source_image,
            variation_strength=input.variation_strength,
        ),
        reasoning=f"Generated {input.count} variations with strength={input.variation_strength}",
        suggestions=[
            "Use 0.1-0.3 for subtle variations, 0.4-0.7 for more creative alternatives",
            "Re-run with a specific seed to reproduce a variation you like",
        ],
    )


# =============================================================================
# post-process Command
# =============================================================================


class PostProcessInput(BaseModel):
    """Input for post-process command."""

    image_url: str = Field(..., description="URL of the image to process")
    sharpen: bool = Field(
        default=False,
        description="Apply sharpening (good for icons)",
    )
    color_correct: bool = Field(
        default=False,
        description="Apply color correction",
    )
    format: OutputFormat = Field(
        default=OutputFormat.PNG,
        description="Output format (png, webp, jpeg)",
    )


class PostProcessOutput(BaseModel):
    """Output for post-process command."""

    processed: PostProcessedImage = Field(..., description="Processed image details")


async def post_process(input: PostProcessInput) -> CommandResult[PostProcessOutput]:
    """Apply post-processing to an image.
    
    Available operations:
    - Sharpening: Crisp edges, especially good for icons
    - Color correction: Adjust to brand palette
    - Format conversion: PNG (lossless), WebP (efficient), JPEG (small)
    
    MVP: Returns mock processed image URL.
    """
    # Validate URL format
    if not input.image_url.startswith(("http://", "https://")):
        return error(
            code=ErrorCode.IMAGE_URL_INVALID.value,
            message="Image URL must start with http:// or https://",
            suggestion="Provide a valid URL to an image",
        )
    
    # MVP: Simulate post-processing
    # In production, this would use Pillow or similar for image processing
    
    temp_dir = Path(tempfile.gettempdir()) / "noisett" / "processed"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(_now().timestamp())
    ext = input.format.value
    suffix = ""
    if input.sharpen:
        suffix += "_sharp"
    if input.color_correct:
        suffix += "_cc"
    
    processed_path = temp_dir / f"processed_{timestamp}{suffix}.{ext}"
    
    processed_image = PostProcessedImage(
        url=f"file://{processed_path}",
        original_url=input.image_url,
        format=input.format,
        sharpened=input.sharpen,
        color_corrected=input.color_correct,
    )
    
    operations = []
    if input.sharpen:
        operations.append("sharpening")
    if input.color_correct:
        operations.append("color correction")
    if not operations:
        operations.append("format conversion")
    
    return success(
        data=PostProcessOutput(processed=processed_image),
        reasoning=f"Applied {', '.join(operations)}; output format: {input.format.value}",
        suggestions=[
            "Use PNG for icons and assets with transparency",
            "Use WebP for web with good compression",
            "Use JPEG for photos where smaller size is needed",
        ],
    )


# =============================================================================
# Test Helper
# =============================================================================


def reset_storage() -> None:
    """Reset any in-memory storage for testing.
    
    Quality commands are stateless (operate on URLs), so this is a no-op.
    Kept for consistency with other command modules.
    """
    pass
