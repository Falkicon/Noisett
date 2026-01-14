"""Tests for LoRA training commands (Phase 1 - Convex Storage Migration)."""

import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from src.commands.lora import (
    CreateLoraInput,
    LoraActivateInput,
    LoraDeleteInput,
    LoraListInput,
    LoraStatusInput,
    TrainLoraInput,
    UploadImagesInput,
    activate,
    create,
    delete,
    list_loras,
    status,
    train,
    upload_images,
)
from src.core.types import BaseModelType, LoraStatus


# Mock Convex data for tests
MOCK_LORA_DATA = {
    "_id": "lora_123456",
    "name": "Test LoRA",
    "triggerWord": "teststyle",
    "baseModel": "flux",
    "status": "created",
    "steps": 1000,
    "isActive": False,
    "createdAt": int(time.time() * 1000),
}


@pytest.fixture
def mock_convex_client():
    """Mock ConvexClient for tests."""
    mock_client = AsyncMock()

    # Store created LoRAs to simulate persistence
    mock_client._loras = {}
    mock_client._trigger_words = set()

    def get_lora_side_effect(lora_id):
        return mock_client._loras.get(lora_id)

    def get_lora_by_trigger_word_side_effect(trigger_word):
        if trigger_word in mock_client._trigger_words:
            return MOCK_LORA_DATA  # Return existing LoRA
        return None

    def create_lora_side_effect(lora_data):
        lora_id = "lora_123456"
        mock_client._loras[lora_id] = {**MOCK_LORA_DATA, **lora_data, "_id": lora_id}
        mock_client._trigger_words.add(lora_data["triggerWord"])
        return lora_id

    # Set up side effects
    mock_client.get_lora.side_effect = get_lora_side_effect
    mock_client.get_lora_by_trigger_word.side_effect = get_lora_by_trigger_word_side_effect
    mock_client.create_lora.side_effect = create_lora_side_effect

    # Default return values for other methods
    mock_client.list_loras.return_value = []
    mock_client.update_lora.return_value = None
    mock_client.delete_lora.return_value = None

    # Phase 2 training images methods
    mock_client.create_training_image.return_value = "image_123456"
    mock_client.list_training_images_by_lora.return_value = []
    mock_client.count_training_images_by_lora.return_value = 0
    mock_client.delete_training_image.return_value = None
    mock_client.delete_training_images_by_lora.return_value = None

    # Phase 2 storage methods
    mock_client.generate_upload_url.return_value = "https://convex.storage/upload/abc123"
    mock_client.get_storage_usage.return_value = {
        "used_bytes": 0,
        "quota_bytes": 10737418240,
        "usage_percent": 0
    }

    return mock_client


@pytest.fixture(autouse=True)
def mock_get_convex_client(mock_convex_client):
    """Auto-mock get_convex_client for all tests."""
    with patch('src.commands.lora.get_convex_client', return_value=mock_convex_client):
        yield mock_convex_client


# =============================================================================
# lora.create tests
# =============================================================================


@pytest.mark.asyncio
async def test_lora_create_success():
    """Test successful LoRA creation."""
    input_data = CreateLoraInput(
        name="Xbox Brand Style",
        trigger_word="xboxstyle",
        base_model=BaseModelType.FLUX,
        description="Xbox brand visual style",
        steps=1500,
    )

    result = await create(input_data)

    assert result.success is True
    assert result.data is not None
    assert result.data.lora.name == input_data.name
    assert result.data.lora.trigger_word == input_data.trigger_word
    assert result.data.lora.base_model == BaseModelType.FLUX
    assert result.data.lora.status == LoraStatus.CREATED
    assert result.data.lora.steps == 1500
    assert result.reasoning is not None


@pytest.mark.asyncio
async def test_lora_create_flux_warning():
    """Test that FLUX base model adds non-commercial warning."""
    input_data = CreateLoraInput(
        name="Test LoRA",
        trigger_word="teststyle",
        base_model=BaseModelType.FLUX,
    )

    result = await create(input_data)

    assert result.success is True
    assert result.warnings is not None
    assert any(w.code == "FLUX_NON_COMMERCIAL" for w in result.warnings)


@pytest.mark.asyncio
async def test_lora_create_duplicate_name():
    """Test that duplicate name returns error."""
    input_data = CreateLoraInput(
        name="Xbox Style",
        trigger_word="xboxstyle",
    )
    await create(input_data)

    # Try to create with same name
    duplicate = CreateLoraInput(
        name="Xbox Style",
        trigger_word="othertrigger",
    )
    result = await create(duplicate)

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_lora_create_duplicate_trigger_word():
    """Test that duplicate trigger word returns error."""
    input_data = CreateLoraInput(
        name="Xbox Style",
        trigger_word="xboxstyle",
    )
    await create(input_data)

    # Try to create with same trigger word
    duplicate = CreateLoraInput(
        name="Different Name",
        trigger_word="xboxstyle",
    )
    result = await create(duplicate)

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_ALREADY_EXISTS"


# =============================================================================
# lora.upload-images tests
# =============================================================================


@pytest.mark.asyncio
async def test_upload_images_success():
    """Test successful image upload."""
    # Create LoRA first
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    # Upload images (need at least 5 for Phase 2 validation)
    input_data = UploadImagesInput(
        lora_id=lora_id,
        images=[
            {"url": "https://example.com/img1.jpg", "caption": "Style example 1"},
            {"url": "https://example.com/img2.jpg", "caption": "Style example 2"},
            {"url": "https://example.com/img3.jpg", "caption": "Style example 3"},
            {"url": "https://example.com/img4.jpg", "caption": "Style example 4"},
            {"url": "https://example.com/img5.jpg", "caption": "Style example 5"},
        ],
    )

    result = await upload_images(input_data)

    assert result.success is True
    assert result.data is not None
    assert result.data.uploaded_count == 5
    assert len(result.data.lora.images) == 5


@pytest.mark.asyncio
async def test_upload_images_not_found():
    """Test upload to non-existent LoRA."""
    input_data = UploadImagesInput(
        lora_id="nonexistent",
        images=[{"url": "https://example.com/img1.jpg"}],
    )

    result = await upload_images(input_data)

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_NOT_FOUND"


@pytest.mark.asyncio
async def test_upload_images_ready_to_train():
    """Test that uploading 10+ images sets status to ready_to_train."""
    # Create LoRA
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    # Upload 10 images
    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(10)]
    input_data = UploadImagesInput(lora_id=lora_id, images=images)

    result = await upload_images(input_data)

    assert result.success is True
    assert result.data.lora.status == LoraStatus.READY_TO_TRAIN


@pytest.mark.asyncio
async def test_upload_images_insufficient_warning():
    """Test that insufficient images adds warning."""
    # Create LoRA
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    # Upload fewer than minimum
    input_data = UploadImagesInput(
        lora_id=lora_id,
        images=[{"url": "https://example.com/img1.jpg"}],
    )

    result = await upload_images(input_data)

    assert result.success is True
    assert result.warnings is not None
    assert any(w.code == "INSUFFICIENT_IMAGES" for w in result.warnings)


# =============================================================================
# lora.train tests
# =============================================================================


@pytest.mark.asyncio
async def test_train_success():
    """Test successful training start returns SSE handoff."""
    # Create and upload images
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(15)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))

    # Start training - now returns handoff
    result = await train(TrainLoraInput(lora_id=lora_id))

    assert result.success is True
    assert result.data is not None
    # Check handoff structure
    assert result.data["protocol"] == "sse"
    assert f"/api/training/{lora_id}/events" in result.data["endpoint"]
    assert "progress" in result.data["metadata"]["capabilities"]


@pytest.mark.asyncio
async def test_train_not_found():
    """Test training non-existent LoRA."""
    result = await train(TrainLoraInput(lora_id="nonexistent"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_NOT_FOUND"


@pytest.mark.asyncio
async def test_train_insufficient_images():
    """Test training with insufficient images."""
    # Create LoRA without enough images
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    # Upload only 5 images (minimum is 10)
    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(5)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))

    result = await train(TrainLoraInput(lora_id=lora_id))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "INSUFFICIENT_IMAGES"


# =============================================================================
# lora.status tests
# =============================================================================


@pytest.mark.asyncio
async def test_status_success():
    """Test getting LoRA status."""
    # Create LoRA
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    result = await status(LoraStatusInput(lora_id=lora_id))

    assert result.success is True
    assert result.data is not None
    assert result.data.lora.id == lora_id
    assert result.data.lora.status == LoraStatus.CREATED


@pytest.mark.asyncio
async def test_status_not_found():
    """Test status of non-existent LoRA."""
    result = await status(LoraStatusInput(lora_id="nonexistent"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_NOT_FOUND"


# =============================================================================
# lora.list tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_empty():
    """Test listing when no LoRAs exist."""
    result = await list_loras(LoraListInput())

    assert result.success is True
    assert result.data is not None
    assert result.data.total == 0
    assert len(result.data.loras) == 0


@pytest.mark.asyncio
async def test_list_multiple():
    """Test listing multiple LoRAs."""
    # Create multiple LoRAs
    await create(CreateLoraInput(name="LoRA 1", trigger_word="style1"))
    await create(CreateLoraInput(name="LoRA 2", trigger_word="style2"))
    await create(CreateLoraInput(name="LoRA 3", trigger_word="style3"))

    result = await list_loras(LoraListInput())

    assert result.success is True
    assert result.data.total == 3


@pytest.mark.asyncio
async def test_list_filter_by_status():
    """Test listing with status filter."""
    # Create LoRAs in different states
    create_result = await create(
        CreateLoraInput(name="Trained LoRA", trigger_word="trained")
    )
    lora_id = create_result.data.lora.id

    # Upload images and train one
    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(15)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))
    await train(TrainLoraInput(lora_id=lora_id))
    _complete_training(lora_id)  # Complete training for test

    # Create another that stays in CREATED
    await create(CreateLoraInput(name="New LoRA", trigger_word="newstyle"))

    # Filter by completed
    result = await list_loras(LoraListInput(status=LoraStatus.COMPLETED))

    assert result.success is True
    assert result.data.total == 1
    assert result.data.loras[0].name == "Trained LoRA"


# =============================================================================
# lora.activate tests
# =============================================================================


@pytest.mark.asyncio
async def test_activate_success():
    """Test activating a completed LoRA."""
    # Create, upload, and train
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(15)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))
    await train(TrainLoraInput(lora_id=lora_id))
    _complete_training(lora_id)  # Complete training for test

    # Activate
    result = await activate(LoraActivateInput(lora_id=lora_id, active=True))

    assert result.success is True
    assert result.data.lora.is_active is True


@pytest.mark.asyncio
async def test_activate_not_ready():
    """Test activating an incomplete LoRA."""
    # Create LoRA but don't train it
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    result = await activate(LoraActivateInput(lora_id=lora_id, active=True))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_NOT_READY"


@pytest.mark.asyncio
async def test_deactivate_success():
    """Test deactivating an active LoRA."""
    # Create, upload, train, and activate
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(15)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))
    await train(TrainLoraInput(lora_id=lora_id))
    _complete_training(lora_id)  # Complete training for test
    await activate(LoraActivateInput(lora_id=lora_id, active=True))

    # Deactivate
    result = await activate(LoraActivateInput(lora_id=lora_id, active=False))

    assert result.success is True
    assert result.data.lora.is_active is False


# =============================================================================
# lora.delete tests
# =============================================================================


@pytest.mark.asyncio
async def test_delete_success():
    """Test deleting a LoRA."""
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    result = await delete(LoraDeleteInput(lora_id=lora_id))

    assert result.success is True
    assert result.data.deleted_id == lora_id

    # Verify it's gone
    status_result = await status(LoraStatusInput(lora_id=lora_id))
    assert status_result.success is False


@pytest.mark.asyncio
async def test_delete_not_found():
    """Test deleting non-existent LoRA."""
    result = await delete(LoraDeleteInput(lora_id="nonexistent"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "LORA_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_active_fails():
    """Test that deleting an active LoRA fails."""
    # Create, upload, train, and activate
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(15)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))
    await train(TrainLoraInput(lora_id=lora_id))
    _complete_training(lora_id)  # Complete training for test
    await activate(LoraActivateInput(lora_id=lora_id, active=True))

    # Try to delete
    result = await delete(LoraDeleteInput(lora_id=lora_id))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "CANNOT_DELETE_ACTIVE"
