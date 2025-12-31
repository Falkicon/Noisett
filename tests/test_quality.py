"""Tests for quality pipeline commands (Phase 6)."""

import pytest

from src.commands.quality import (
    PostProcessInput,
    QualityPresetsInput,
    RefineInput,
    UpscaleInput,
    VariationsInput,
    post_process,
    presets,
    refine,
    reset_storage,
    upscale,
    variations,
)
from src.core.errors import ErrorCode
from src.core.types import OutputFormat, QualityPreset, UpscaleModel


@pytest.fixture(autouse=True)
def reset_state():
    """Reset storage before each test."""
    reset_storage()
    yield
    reset_storage()


# =============================================================================
# quality.presets tests
# =============================================================================


@pytest.mark.asyncio
async def test_presets_returns_all_presets():
    """quality.presets should return all available presets."""
    result = await presets(QualityPresetsInput())
    
    assert result.success is True
    assert result.data is not None
    assert result.data.total == 3  # DRAFT, STANDARD, HIGH
    assert len(result.data.presets) == 3
    
    # Check preset names
    preset_names = [p.name for p in result.data.presets]
    assert QualityPreset.DRAFT in preset_names
    assert QualityPreset.STANDARD in preset_names
    assert QualityPreset.HIGH in preset_names


@pytest.mark.asyncio
async def test_presets_includes_preset_details():
    """quality.presets should include preset configuration details."""
    result = await presets(QualityPresetsInput())
    
    assert result.success is True
    
    # Find the STANDARD preset
    standard = next(p for p in result.data.presets if p.name == QualityPreset.STANDARD)
    
    assert standard.width == 1024
    assert standard.height == 1024
    assert standard.steps > 0
    assert standard.description is not None


# =============================================================================
# refine tests
# =============================================================================


@pytest.mark.asyncio
async def test_refine_valid_image():
    """refine should accept valid image URL."""
    result = await refine(RefineInput(
        image_url="https://example.com/image.jpg",
        denoise_strength=0.3,
        steps=20,
    ))
    
    assert result.success is True
    assert result.data is not None
    assert result.data.refined.original_url == "https://example.com/image.jpg"
    assert result.data.refined.denoise_strength == 0.3
    assert result.data.refined.steps == 20


@pytest.mark.asyncio
async def test_refine_with_prompt():
    """refine should accept optional prompt."""
    result = await refine(RefineInput(
        image_url="https://example.com/image.jpg",
        prompt="enhance details, sharper edges",
    ))
    
    assert result.success is True
    assert result.data is not None


@pytest.mark.asyncio
async def test_refine_invalid_url():
    """refine should reject invalid URLs."""
    result = await refine(RefineInput(
        image_url="not-a-valid-url",
    ))
    
    assert result.success is False
    assert result.error is not None
    assert result.error.code == ErrorCode.IMAGE_URL_INVALID.value


@pytest.mark.asyncio
async def test_refine_has_reasoning():
    """refine should include reasoning metadata."""
    result = await refine(RefineInput(
        image_url="https://example.com/image.jpg",
    ))
    
    assert result.success is True
    assert result.reasoning is not None
    assert "denoise" in result.reasoning.lower()


# =============================================================================
# upscale tests
# =============================================================================


@pytest.mark.asyncio
async def test_upscale_2x():
    """upscale should support 2x scaling."""
    result = await upscale(UpscaleInput(
        image_url="https://example.com/image.jpg",
        scale=2,
    ))
    
    assert result.success is True
    assert result.data is not None
    assert result.data.upscaled.scale == 2
    assert result.data.upscaled.width == 2048  # 1024 * 2
    assert result.data.upscaled.height == 2048


@pytest.mark.asyncio
async def test_upscale_4x():
    """upscale should support 4x scaling."""
    result = await upscale(UpscaleInput(
        image_url="https://example.com/image.jpg",
        scale=4,
    ))
    
    assert result.success is True
    assert result.data is not None
    assert result.data.upscaled.scale == 4
    assert result.data.upscaled.width == 4096  # 1024 * 4


@pytest.mark.asyncio
async def test_upscale_with_supir_model():
    """upscale should support SUPIR model."""
    result = await upscale(UpscaleInput(
        image_url="https://example.com/image.jpg",
        model=UpscaleModel.SUPIR,
    ))
    
    assert result.success is True
    assert result.data.upscaled.model == UpscaleModel.SUPIR
    assert "supir" in result.reasoning.lower()


@pytest.mark.asyncio
async def test_upscale_invalid_url():
    """upscale should reject invalid URLs."""
    result = await upscale(UpscaleInput(
        image_url="file://local/path/image.jpg",
    ))
    
    assert result.success is False
    assert result.error.code == ErrorCode.IMAGE_URL_INVALID.value


# =============================================================================
# variations tests
# =============================================================================


@pytest.mark.asyncio
async def test_variations_default_count():
    """variations should generate 4 variations by default."""
    result = await variations(VariationsInput(
        source_image="https://example.com/image.jpg",
    ))
    
    assert result.success is True
    assert len(result.data.variations) == 4
    assert result.data.source_image == "https://example.com/image.jpg"


@pytest.mark.asyncio
async def test_variations_custom_count():
    """variations should respect custom count."""
    result = await variations(VariationsInput(
        source_image="https://example.com/image.jpg",
        count=2,
    ))
    
    assert result.success is True
    assert len(result.data.variations) == 2


@pytest.mark.asyncio
async def test_variations_have_unique_seeds():
    """variations should have unique seeds."""
    result = await variations(VariationsInput(
        source_image="https://example.com/image.jpg",
        count=4,
    ))
    
    assert result.success is True
    seeds = [v.seed for v in result.data.variations]
    assert len(seeds) == len(set(seeds))  # All unique


@pytest.mark.asyncio
async def test_variations_invalid_url():
    """variations should reject invalid URLs."""
    result = await variations(VariationsInput(
        source_image="invalid-url",
    ))
    
    assert result.success is False
    assert result.error.code == ErrorCode.IMAGE_URL_INVALID.value


@pytest.mark.asyncio
async def test_variations_with_strength():
    """variations should accept variation_strength."""
    result = await variations(VariationsInput(
        source_image="https://example.com/image.jpg",
        variation_strength=0.5,
    ))
    
    assert result.success is True
    assert result.data.variation_strength == 0.5


# =============================================================================
# post-process tests
# =============================================================================


@pytest.mark.asyncio
async def test_post_process_format_conversion():
    """post-process should convert format."""
    result = await post_process(PostProcessInput(
        image_url="https://example.com/image.jpg",
        format=OutputFormat.WEBP,
    ))
    
    assert result.success is True
    assert result.data.processed.format == OutputFormat.WEBP
    assert ".webp" in result.data.processed.url


@pytest.mark.asyncio
async def test_post_process_sharpen():
    """post-process should apply sharpening."""
    result = await post_process(PostProcessInput(
        image_url="https://example.com/image.jpg",
        sharpen=True,
    ))
    
    assert result.success is True
    assert result.data.processed.sharpened is True
    assert "_sharp" in result.data.processed.url


@pytest.mark.asyncio
async def test_post_process_color_correct():
    """post-process should apply color correction."""
    result = await post_process(PostProcessInput(
        image_url="https://example.com/image.jpg",
        color_correct=True,
    ))
    
    assert result.success is True
    assert result.data.processed.color_corrected is True
    assert "_cc" in result.data.processed.url


@pytest.mark.asyncio
async def test_post_process_all_options():
    """post-process should apply multiple options."""
    result = await post_process(PostProcessInput(
        image_url="https://example.com/image.jpg",
        sharpen=True,
        color_correct=True,
        format=OutputFormat.PNG,
    ))
    
    assert result.success is True
    assert result.data.processed.sharpened is True
    assert result.data.processed.color_corrected is True
    assert result.data.processed.format == OutputFormat.PNG


@pytest.mark.asyncio
async def test_post_process_invalid_url():
    """post-process should reject invalid URLs."""
    result = await post_process(PostProcessInput(
        image_url="ftp://invalid.com/image.jpg",
    ))
    
    assert result.success is False
    assert result.error.code == ErrorCode.IMAGE_URL_INVALID.value


@pytest.mark.asyncio
async def test_post_process_has_suggestions():
    """post-process should include format suggestions."""
    result = await post_process(PostProcessInput(
        image_url="https://example.com/image.jpg",
    ))
    
    assert result.success is True
    assert result.suggestions is not None
    assert len(result.suggestions) > 0
