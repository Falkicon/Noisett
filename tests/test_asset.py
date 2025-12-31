"""Tests for asset commands."""

import pytest
from src.commands.asset import AssetGenerateInput, generate, types
from src.core.types import AssetType, ModelId, QualityPreset


@pytest.mark.asyncio
async def test_asset_generate_success():
    """Test successful image generation."""
    input_data = AssetGenerateInput(
        prompt="A cloud computing concept illustration",
        asset_type=AssetType.PRODUCT,
        model=ModelId.HIDREAM,
        quality=QualityPreset.STANDARD,
        count=2,
    )
    
    result = await generate(input_data)
    
    assert result.success is True
    assert result.data is not None
    assert result.data.job.prompt == input_data.prompt
    assert result.data.job.count == 2
    assert result.data.job.status.value == "queued"
    assert result.reasoning is not None


@pytest.mark.asyncio
async def test_asset_generate_empty_prompt():
    """Test that empty prompt returns error."""
    input_data = AssetGenerateInput(
        prompt="   ",  # Whitespace-only prompt
        asset_type=AssetType.PRODUCT,
    )
    
    result = await generate(input_data)
    
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "PROMPT_EMPTY"


@pytest.mark.asyncio
async def test_asset_generate_unavailable_model():
    """Test that unavailable model returns error."""
    input_data = AssetGenerateInput(
        prompt="Test prompt",
        model=ModelId.SD35,  # SD35 is marked unavailable
    )
    
    result = await generate(input_data)
    
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "MODEL_UNAVAILABLE"


@pytest.mark.asyncio
async def test_asset_generate_non_commercial_warning():
    """Test that non-commercial model adds warning."""
    input_data = AssetGenerateInput(
        prompt="Test prompt",
        model=ModelId.FLUX,  # FLUX is non-commercial
    )
    
    result = await generate(input_data)
    
    assert result.success is True
    assert result.warnings is not None
    assert any(w.code == "NON_COMMERCIAL" for w in result.warnings)


@pytest.mark.asyncio
async def test_asset_types_success():
    """Test listing asset types."""
    result = await types()
    
    assert result.success is True
    assert result.data is not None
    assert len(result.data.types) == 4  # icons, product, logo, premium
    
    # Check all expected types are present
    type_ids = {t.id for t in result.data.types}
    assert AssetType.ICONS in type_ids
    assert AssetType.PRODUCT in type_ids
    assert AssetType.LOGO in type_ids
    assert AssetType.PREMIUM in type_ids
