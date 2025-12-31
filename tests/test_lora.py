"""Tests for LoRA training commands (Phase 5)."""

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
    reset_storage,
    status,
    train,
    upload_images,
)
from src.core.types import BaseModelType, LoraStatus


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset storage before each test."""
    reset_storage()
    yield
    reset_storage()


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

    # Upload images
    input_data = UploadImagesInput(
        lora_id=lora_id,
        images=[
            {"url": "https://example.com/img1.jpg", "caption": "Style example 1"},
            {"url": "https://example.com/img2.jpg", "caption": "Style example 2"},
        ],
    )

    result = await upload_images(input_data)

    assert result.success is True
    assert result.data is not None
    assert result.data.uploaded_count == 2
    assert len(result.data.lora.images) == 2


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
    """Test successful training start."""
    # Create and upload images
    create_result = await create(
        CreateLoraInput(name="Test LoRA", trigger_word="teststyle")
    )
    lora_id = create_result.data.lora.id

    images = [{"url": f"https://example.com/img{i}.jpg"} for i in range(15)]
    await upload_images(UploadImagesInput(lora_id=lora_id, images=images))

    # Start training
    result = await train(TrainLoraInput(lora_id=lora_id))

    assert result.success is True
    assert result.data is not None
    # In MVP, training completes immediately
    assert result.data.lora.status == LoraStatus.COMPLETED
    assert result.data.lora.lora_url is not None


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
    await activate(LoraActivateInput(lora_id=lora_id, active=True))

    # Try to delete
    result = await delete(LoraDeleteInput(lora_id=lora_id))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "CANNOT_DELETE_ACTIVE"
