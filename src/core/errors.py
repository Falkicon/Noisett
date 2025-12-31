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
