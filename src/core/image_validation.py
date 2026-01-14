"""Image validation utilities for LoRA training images.

Validates individual images and collections according to training requirements:
- Individual: 512x512 min, 10MB max, JPEG/PNG only
- Collection: 5-100 images required, warns if < 15 images
"""

import io
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image


class ImageValidationError(Exception):
    """Raised when image validation fails."""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class CollectionValidationError(Exception):
    """Raised when collection validation fails."""

    def __init__(self, message: str, code: str, warnings: Optional[List[str]] = None):
        self.message = message
        self.code = code
        self.warnings = warnings or []
        super().__init__(message)


def validate_image_data(
    file_data: bytes,
    filename: str,
    max_size_bytes: int = 10 * 1024 * 1024  # 10MB
) -> Tuple[Dict[str, Any], List[str]]:
    """Validate a single training image.

    Args:
        file_data: Raw image file bytes
        filename: Original filename for format detection
        max_size_bytes: Maximum allowed file size (default 10MB)

    Returns:
        Tuple of (image_metadata, warnings)

    Raises:
        ImageValidationError: If validation fails
    """
    warnings = []

    # Check file size
    if len(file_data) > max_size_bytes:
        raise ImageValidationError(
            f"File '{filename}' is {len(file_data) / 1024 / 1024:.1f}MB, maximum allowed is {max_size_bytes / 1024 / 1024}MB",
            "FILE_TOO_LARGE"
        )

    if len(file_data) == 0:
        raise ImageValidationError(
            f"File '{filename}' is empty",
            "EMPTY_FILE"
        )

    # Detect format using PIL and filename extension
    try:
        # Use PIL to detect the actual format
        with io.BytesIO(file_data) as image_buffer:
            temp_image = Image.open(image_buffer)
            detected_format = temp_image.format

        # Map PIL formats to MIME types
        if detected_format == 'JPEG':
            mime_type = 'image/jpeg'
        elif detected_format == 'PNG':
            mime_type = 'image/png'
        else:
            raise ImageValidationError(
                f"File '{filename}' has unsupported format '{detected_format}'. Only JPEG and PNG are supported",
                "UNSUPPORTED_FORMAT"
            )
    except Exception as e:
        # If PIL can't read it, check extension as fallback
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext in ['jpg', 'jpeg']:
            mime_type = 'image/jpeg'
        elif ext == 'png':
            mime_type = 'image/png'
        else:
            raise ImageValidationError(
                f"Cannot determine image format for '{filename}': {str(e)}",
                "UNKNOWN_FORMAT"
            )

    # Check format
    allowed_types = ['image/jpeg', 'image/png']
    if mime_type not in allowed_types:
        raise ImageValidationError(
            f"File '{filename}' has unsupported format '{mime_type}'. Only JPEG and PNG are supported",
            "UNSUPPORTED_FORMAT"
        )

    # Load and validate image
    try:
        image = Image.open(io.BytesIO(file_data))
        width, height = image.size
    except Exception as e:
        raise ImageValidationError(
            f"Cannot read image data from '{filename}': {str(e)}",
            "CORRUPT_IMAGE"
        )

    # Check dimensions
    min_dimension = 512
    if width < min_dimension or height < min_dimension:
        raise ImageValidationError(
            f"Image '{filename}' dimensions are {width}x{height}, minimum required is {min_dimension}x{min_dimension}",
            "DIMENSIONS_TOO_SMALL"
        )

    # Generate warnings for non-square images
    if width != height:
        warnings.append(f"Image '{filename}' is not square ({width}x{height}). Square images work best for training")

    # Generate warnings for very large images
    if width > 2048 or height > 2048:
        warnings.append(f"Image '{filename}' is very large ({width}x{height}). Consider resizing to 1024x1024 for faster training")

    # Return metadata
    metadata = {
        "filename": filename,
        "width": width,
        "height": height,
        "sizeBytes": len(file_data),
        "format": mime_type,
    }

    return metadata, warnings


def validate_image_collection(
    image_count: int,
    min_images: int = 5,
    max_images: int = 100,
    recommended_min: int = 15
) -> List[str]:
    """Validate training image collection constraints.

    Args:
        image_count: Number of images in collection
        min_images: Minimum required images (default 5)
        max_images: Maximum allowed images (default 100)
        recommended_min: Recommended minimum for good results (default 15)

    Returns:
        List of warning messages

    Raises:
        CollectionValidationError: If validation fails
    """
    warnings = []

    # Check minimum required
    if image_count < min_images:
        raise CollectionValidationError(
            f"Not enough training images. Found {image_count}, minimum required is {min_images}",
            "TOO_FEW_IMAGES"
        )

    # Check maximum allowed
    if image_count > max_images:
        raise CollectionValidationError(
            f"Too many training images. Found {image_count}, maximum allowed is {max_images}",
            "TOO_MANY_IMAGES"
        )

    # Generate warnings
    if image_count < recommended_min:
        warnings.append(
            f"You have {image_count} images. For best results, use at least {recommended_min} high-quality, diverse images"
        )

    if image_count > 50:
        warnings.append(
            f"You have {image_count} images. Training may take longer with many images. Consider using 20-40 high-quality images instead"
        )

    return warnings


def estimate_storage_usage(image_sizes: List[int]) -> Dict[str, Any]:
    """Estimate storage usage for image collection.

    Args:
        image_sizes: List of image file sizes in bytes

    Returns:
        Storage usage statistics
    """
    total_bytes = sum(image_sizes)
    total_mb = total_bytes / 1024 / 1024
    avg_mb = total_mb / len(image_sizes) if image_sizes else 0

    return {
        "total_bytes": total_bytes,
        "total_mb": round(total_mb, 2),
        "average_mb_per_image": round(avg_mb, 2),
        "image_count": len(image_sizes),
    }