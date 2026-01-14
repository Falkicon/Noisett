"""Tests for LoRA Phase 2 implementation.

Tests the new Phase 2 features:
- Image validation (dimensions, size, format)
- Collection validation (5-100 images)
- Convex storage integration
- Storage quota handling
"""

import pytest
from unittest.mock import patch, AsyncMock

from src.core.image_validation import (
    validate_image_data,
    validate_image_collection,
    ImageValidationError,
    CollectionValidationError,
)
from src.commands.lora import upload_images, UploadImagesInput


class TestImageValidation:
    """Test individual image validation."""

    def test_validate_image_success(self):
        """Test successful image validation."""
        # Create a simple JPEG image data (minimal JPEG header)
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xfe'
        # Add some dummy data to make it look like a real image
        image_data = jpeg_header + b'\x00' * 1000  # 1KB image

        metadata, warnings = validate_image_data(image_data, "test.jpg")

        assert metadata["filename"] == "test.jpg"
        assert metadata["sizeBytes"] == len(image_data)
        assert metadata["format"] == "image/jpeg"
        assert isinstance(warnings, list)

    def test_validate_image_too_large(self):
        """Test file size validation."""
        # Create file larger than 10MB
        large_data = b'\xff\xd8\xff\xe0' + b'\x00' * (11 * 1024 * 1024)

        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_data(large_data, "large.jpg")

        assert exc_info.value.code == "FILE_TOO_LARGE"
        assert "10MB" in exc_info.value.message

    def test_validate_image_empty(self):
        """Test empty file validation."""
        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_data(b'', "empty.jpg")

        assert exc_info.value.code == "EMPTY_FILE"

    def test_validate_image_unsupported_format(self):
        """Test unsupported format validation."""
        # BMP header
        bmp_data = b'BM' + b'\x00' * 100

        with pytest.raises(ImageValidationError) as exc_info:
            validate_image_data(bmp_data, "test.bmp")

        assert exc_info.value.code in ["UNSUPPORTED_FORMAT", "CORRUPT_IMAGE"]


class TestCollectionValidation:
    """Test image collection validation."""

    def test_collection_validation_success(self):
        """Test successful collection validation."""
        warnings = validate_image_collection(15)  # Good number of images
        assert isinstance(warnings, list)

    def test_collection_validation_too_few(self):
        """Test collection with too few images."""
        with pytest.raises(CollectionValidationError) as exc_info:
            validate_image_collection(3)  # Less than minimum 5

        assert exc_info.value.code == "TOO_FEW_IMAGES"
        assert "minimum required is 5" in exc_info.value.message

    def test_collection_validation_too_many(self):
        """Test collection with too many images."""
        with pytest.raises(CollectionValidationError) as exc_info:
            validate_image_collection(150)  # More than maximum 100

        assert exc_info.value.code == "TOO_MANY_IMAGES"
        assert "maximum allowed is 100" in exc_info.value.message

    def test_collection_validation_warning_low(self):
        """Test collection with low but valid count generates warning."""
        warnings = validate_image_collection(8)  # Valid but low
        assert any("best results" in w for w in warnings)

    def test_collection_validation_warning_high(self):
        """Test collection with high count generates warning."""
        warnings = validate_image_collection(80)  # Valid but high
        assert any("training may take longer" in w for w in warnings)


class TestPhase2UploadImages:
    """Test Phase 2 upload images functionality."""

    @pytest.fixture
    def mock_convex_client(self):
        """Mock ConvexClient for Phase 2 tests."""
        mock_client = AsyncMock()
        mock_client.get_lora.return_value = {
            "_id": "test_lora_id",
            "name": "Test LoRA",
            "triggerWord": "teststyle",
            "baseModel": "flux",
            "status": "created",
            "steps": 1000,
            "isActive": False,
            "createdAt": 1640995200000,  # Fixed timestamp
        }
        mock_client.create_training_image.return_value = "image_123"
        mock_client.count_training_images_by_lora.return_value = 5
        mock_client.list_training_images_by_lora.return_value = []
        mock_client.update_lora.return_value = None
        return mock_client

    @pytest.mark.asyncio
    async def test_upload_images_phase2_format(self, mock_convex_client):
        """Test uploading images with Phase 2 format (storage IDs)."""
        with patch('src.commands.lora.get_convex_client', return_value=mock_convex_client):
            input_data = UploadImagesInput(
                lora_id="test_lora_id",
                images=[
                    {
                        "storage_id": "storage_123",
                        "filename": "image1.jpg",
                        "width": 512,
                        "height": 512,
                        "size_bytes": 1024000,
                    },
                    {
                        "storage_id": "storage_124",
                        "filename": "image2.jpg",
                        "width": 1024,
                        "height": 1024,
                        "size_bytes": 2048000,
                        "caption": "Test caption",
                    },
                    {
                        "storage_id": "storage_125",
                        "filename": "image3.png",
                        "width": 768,
                        "height": 768,
                        "size_bytes": 1500000,
                    },
                    {
                        "storage_id": "storage_126",
                        "filename": "image4.jpg",
                        "width": 600,
                        "height": 600,
                        "size_bytes": 900000,
                    },
                    {
                        "storage_id": "storage_127",
                        "filename": "image5.jpg",
                        "width": 512,
                        "height": 512,
                        "size_bytes": 800000,
                    },
                ],
            )

            result = await upload_images(input_data)

            # Should succeed with Phase 2 format
            assert result.success is True
            assert result.data.uploaded_count == 5

            # Verify training images were created in Convex
            assert mock_convex_client.create_training_image.call_count == 5

            # Verify LoRA status was updated
            mock_convex_client.update_lora.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_images_phase1_format(self, mock_convex_client):
        """Test uploading images with Phase 1 format (URLs) for backwards compatibility."""
        with patch('src.commands.lora.get_convex_client', return_value=mock_convex_client):
            input_data = UploadImagesInput(
                lora_id="test_lora_id",
                images=[
                    {"url": "https://example.com/img1.jpg"},
                    {"url": "https://example.com/img2.jpg"},
                    {"url": "https://example.com/img3.jpg"},
                    {"url": "https://example.com/img4.jpg"},
                    {"url": "https://example.com/img5.jpg"},
                ],
            )

            result = await upload_images(input_data)

            # Should succeed with Phase 1 format for backwards compatibility
            assert result.success is True
            assert result.data.uploaded_count == 5

            # Phase 1 format should not create training images in Convex
            mock_convex_client.create_training_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_images_dimensions_too_small(self, mock_convex_client):
        """Test that images with too small dimensions are rejected."""
        with patch('src.commands.lora.get_convex_client', return_value=mock_convex_client):
            input_data = UploadImagesInput(
                lora_id="test_lora_id",
                images=[
                    {
                        "storage_id": "storage_123",
                        "filename": "small.jpg",
                        "width": 256,  # Too small
                        "height": 256,  # Too small
                        "size_bytes": 100000,
                    },
                ],
            )

            result = await upload_images(input_data)

            assert result.success is False
            assert "too small" in result.error.message
            assert "minimum 512x512" in result.error.message

    @pytest.mark.asyncio
    async def test_upload_images_mixed_formats_rejected(self, mock_convex_client):
        """Test that mixing Phase 1 and Phase 2 formats is rejected."""
        with patch('src.commands.lora.get_convex_client', return_value=mock_convex_client):
            input_data = UploadImagesInput(
                lora_id="test_lora_id",
                images=[
                    {"url": "https://example.com/img1.jpg"},  # Phase 1
                    {"storage_id": "storage_123", "filename": "img2.jpg"},  # Phase 2
                ],
            )

            result = await upload_images(input_data)

            assert result.success is False
            assert "Mixed input formats not supported" in result.error.message