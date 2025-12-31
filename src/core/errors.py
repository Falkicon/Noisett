"""Standard error codes for Noisett commands.

Error codes follow a consistent naming convention and are used across
all command responses for structured error handling.
"""

from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for command responses."""

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROMPT_TOO_LONG = "PROMPT_TOO_LONG"
    PROMPT_EMPTY = "PROMPT_EMPTY"
    INVALID_COUNT = "INVALID_COUNT"

    # State errors
    JOB_ALREADY_COMPLETE = "JOB_ALREADY_COMPLETE"
    JOB_ALREADY_CANCELLED = "JOB_ALREADY_CANCELLED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"

    # Permission errors
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"

    # Generation errors
    GENERATION_FAILED = "GENERATION_FAILED"
    GENERATION_TIMEOUT = "GENERATION_TIMEOUT"

    # LoRA training errors (Phase 5)
    LORA_NOT_FOUND = "LORA_NOT_FOUND"
    LORA_ALREADY_EXISTS = "LORA_ALREADY_EXISTS"
    TRAINING_FAILED = "TRAINING_FAILED"
    TRAINING_IN_PROGRESS = "TRAINING_IN_PROGRESS"
    TRAINING_NOT_STARTED = "TRAINING_NOT_STARTED"
    INVALID_TRAINING_DATA = "INVALID_TRAINING_DATA"
    INSUFFICIENT_IMAGES = "INSUFFICIENT_IMAGES"
    TOO_MANY_IMAGES = "TOO_MANY_IMAGES"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    LORA_NOT_READY = "LORA_NOT_READY"
    CANNOT_DELETE_ACTIVE = "CANNOT_DELETE_ACTIVE"

    # Quality pipeline errors (Phase 6)
    IMAGE_URL_INVALID = "IMAGE_URL_INVALID"
    IMAGE_FETCH_FAILED = "IMAGE_FETCH_FAILED"
    REFINE_FAILED = "REFINE_FAILED"
    UPSCALE_FAILED = "UPSCALE_FAILED"
    VARIATIONS_FAILED = "VARIATIONS_FAILED"
    POST_PROCESS_FAILED = "POST_PROCESS_FAILED"

    # Auth & Storage errors (Phase 8)
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    HISTORY_NOT_FOUND = "HISTORY_NOT_FOUND"
    FAVORITE_NOT_FOUND = "FAVORITE_NOT_FOUND"
    FAVORITE_ALREADY_EXISTS = "FAVORITE_ALREADY_EXISTS"
    STORAGE_ERROR = "STORAGE_ERROR"

    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# Error message templates with recovery suggestions
ERROR_TEMPLATES = {
    ErrorCode.NOT_FOUND: {
        "message": "Resource not found",
        "suggestion": "Verify the resource ID and try again",
    },
    ErrorCode.JOB_NOT_FOUND: {
        "message": "Generation job not found",
        "suggestion": "Check the job ID or list recent jobs with job.list",
    },
    ErrorCode.MODEL_NOT_FOUND: {
        "message": "Model not found",
        "suggestion": "Use model.list to see available models",
    },
    ErrorCode.VALIDATION_ERROR: {
        "message": "Input validation failed",
        "suggestion": "Check the command schema and provide valid input",
    },
    ErrorCode.PROMPT_TOO_LONG: {
        "message": "Prompt exceeds maximum length (500 characters)",
        "suggestion": "Shorten your prompt or split into multiple requests",
    },
    ErrorCode.PROMPT_EMPTY: {
        "message": "Prompt cannot be empty",
        "suggestion": "Provide a description of the image you want to generate",
    },
    ErrorCode.INVALID_COUNT: {
        "message": "Count must be between 1 and 4",
        "suggestion": "Specify a count between 1 and 4",
    },
    ErrorCode.JOB_ALREADY_COMPLETE: {
        "message": "Cannot modify a completed job",
        "suggestion": "Start a new generation instead",
    },
    ErrorCode.JOB_ALREADY_CANCELLED: {
        "message": "Job was already cancelled",
        "suggestion": "Start a new generation instead",
    },
    ErrorCode.MODEL_UNAVAILABLE: {
        "message": "Selected model is not currently available",
        "suggestion": "Try a different model or wait and retry",
    },
    ErrorCode.FORBIDDEN: {
        "message": "You don't have permission to perform this action",
        "suggestion": "Contact your administrator for access",
    },
    ErrorCode.RATE_LIMITED: {
        "message": "Too many requests",
        "suggestion": "Wait a moment and try again",
    },
    ErrorCode.GENERATION_FAILED: {
        "message": "Image generation failed",
        "suggestion": "Try with a different prompt or model",
    },
    ErrorCode.GENERATION_TIMEOUT: {
        "message": "Generation timed out",
        "suggestion": "Try with 'draft' quality for faster results",
    },
    ErrorCode.INTERNAL_ERROR: {
        "message": "An internal error occurred",
        "suggestion": "Please try again or report this issue",
    },
    ErrorCode.SERVICE_UNAVAILABLE: {
        "message": "Service is temporarily unavailable",
        "suggestion": "Please try again in a few moments",
    },
    # LoRA training error templates (Phase 5)
    ErrorCode.LORA_NOT_FOUND: {
        "message": "LoRA not found",
        "suggestion": "Check the LoRA ID or use lora.list to see available LoRAs",
    },
    ErrorCode.LORA_ALREADY_EXISTS: {
        "message": "A LoRA with this name already exists",
        "suggestion": "Use a different name or delete the existing LoRA first",
    },
    ErrorCode.TRAINING_FAILED: {
        "message": "LoRA training failed",
        "suggestion": "Check training images quality and try again with different parameters",
    },
    ErrorCode.TRAINING_IN_PROGRESS: {
        "message": "Training is already in progress",
        "suggestion": "Wait for current training to complete or cancel it first",
    },
    ErrorCode.TRAINING_NOT_STARTED: {
        "message": "Training has not been started",
        "suggestion": "Use lora.train to start training after uploading images",
    },
    ErrorCode.INVALID_TRAINING_DATA: {
        "message": "Invalid training data format",
        "suggestion": "Ensure images are JPEG or PNG, min 512x512, max 4096x4096",
    },
    ErrorCode.INSUFFICIENT_IMAGES: {
        "message": "Not enough training images",
        "suggestion": "Upload at least 10 images (20-30 recommended for best results)",
    },
    ErrorCode.TOO_MANY_IMAGES: {
        "message": "Too many training images",
        "suggestion": "Maximum 100 images allowed. Remove some and try again",
    },
    ErrorCode.UPLOAD_FAILED: {
        "message": "Image upload failed",
        "suggestion": "Check file format and size, then retry the upload",
    },
    ErrorCode.LORA_NOT_READY: {
        "message": "LoRA is not ready for use",
        "suggestion": "Wait for training to complete (status: completed)",
    },
    ErrorCode.CANNOT_DELETE_ACTIVE: {
        "message": "Cannot delete an active LoRA",
        "suggestion": "Deactivate the LoRA first with lora.activate --active false",
    },
    # Quality pipeline error templates (Phase 6)
    ErrorCode.IMAGE_URL_INVALID: {
        "message": "Invalid image URL",
        "suggestion": "Provide a valid HTTP/HTTPS URL to an image",
    },
    ErrorCode.IMAGE_FETCH_FAILED: {
        "message": "Failed to fetch image from URL",
        "suggestion": "Check that the URL is accessible and returns a valid image",
    },
    ErrorCode.REFINE_FAILED: {
        "message": "Image refinement failed",
        "suggestion": "Try a lower denoise strength or different image",
    },
    ErrorCode.UPSCALE_FAILED: {
        "message": "Image upscaling failed",
        "suggestion": "Try a different upscaling model or smaller image",
    },
    ErrorCode.VARIATIONS_FAILED: {
        "message": "Failed to generate variations",
        "suggestion": "Try a different source image or variation strength",
    },
    ErrorCode.POST_PROCESS_FAILED: {
        "message": "Post-processing failed",
        "suggestion": "Try different processing options or a different image",
    },
    # Auth & Storage error templates (Phase 8)
    ErrorCode.UNAUTHORIZED: {
        "message": "Authentication required",
        "suggestion": "Sign in with your Microsoft account to access this feature",
    },
    ErrorCode.TOKEN_EXPIRED: {
        "message": "Your session has expired",
        "suggestion": "Sign in again to refresh your session",
    },
    ErrorCode.TOKEN_INVALID: {
        "message": "Invalid authentication token",
        "suggestion": "Sign out and sign in again",
    },
    ErrorCode.HISTORY_NOT_FOUND: {
        "message": "History record not found",
        "suggestion": "Check the job ID or use history.list to see your history",
    },
    ErrorCode.FAVORITE_NOT_FOUND: {
        "message": "Favorite not found",
        "suggestion": "Check the job ID and image index, or use favorites.list",
    },
    ErrorCode.FAVORITE_ALREADY_EXISTS: {
        "message": "Image is already in favorites",
        "suggestion": "Use favorites.list to see your current favorites",
    },
    ErrorCode.STORAGE_ERROR: {
        "message": "Storage operation failed",
        "suggestion": "Please try again or contact support",
    },
}


def get_error_template(code: ErrorCode) -> dict:
    """Get the error message template for an error code.
    
    Args:
        code: The error code
        
    Returns:
        Dict with 'message' and 'suggestion' keys
    """
    return ERROR_TEMPLATES.get(
        code,
        {"message": "Unknown error", "suggestion": "Please try again"},
    )
