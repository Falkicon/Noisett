"""Tests for model commands."""

import pytest
from src.commands.model import ModelInfoInput, info, list_models
from src.core.types import ModelId


@pytest.mark.asyncio
async def test_model_list_success():
    """Test listing models."""
    result = await list_models()
    
    assert result.success is True
    assert result.data is not None
    assert len(result.data.models) == 3  # hidream, flux, sd35
    
    # Check all expected models are present
    model_ids = {m.id for m in result.data.models}
    assert ModelId.HIDREAM in model_ids
    assert ModelId.FLUX in model_ids
    assert ModelId.SD35 in model_ids


@pytest.mark.asyncio
async def test_model_info_hidream():
    """Test getting HiDream model info."""
    input_data = ModelInfoInput(model_id=ModelId.HIDREAM)
    
    result = await info(input_data)
    
    assert result.success is True
    assert result.data is not None
    assert result.data.model.id == ModelId.HIDREAM
    assert result.data.model.commercial_ok is True
    assert result.data.model.available is True


@pytest.mark.asyncio
async def test_model_info_flux_warning():
    """Test that FLUX model shows non-commercial warning."""
    input_data = ModelInfoInput(model_id=ModelId.FLUX)
    
    result = await info(input_data)
    
    assert result.success is True
    assert result.warnings is not None
    assert any(w.code == "NON_COMMERCIAL" for w in result.warnings)


@pytest.mark.asyncio
async def test_model_info_unavailable_warning():
    """Test that unavailable model shows warning."""
    input_data = ModelInfoInput(model_id=ModelId.SD35)
    
    result = await info(input_data)
    
    assert result.success is True
    assert result.warnings is not None
    assert any(w.code == "UNAVAILABLE" for w in result.warnings)
