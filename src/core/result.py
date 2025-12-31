"""CommandResult and helper functions for structured command responses.

All commands return a CommandResult with UX-enabling metadata following
Agent-First Development (AFD) principles.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class CommandError(BaseModel):
    """Structured error with recovery guidance."""

    code: str
    message: str
    suggestion: str | None = None


class Warning(BaseModel):
    """Non-fatal warning about side effects or considerations."""

    code: str
    message: str


class CommandResult(BaseModel, Generic[T]):
    """Standard response for all commands.
    
    All Noisett commands return this structure, enabling consistent
    handling across CLI, MCP, and REST API surfaces.
    
    Attributes:
        success: Whether the command completed successfully
        data: The command output (generic type T)
        error: Structured error if success=False
        reasoning: Human-readable explanation of what happened
        confidence: 0-1 score for AI-generated content quality
        warnings: Non-fatal warnings to surface to user
        suggestions: Helpful tips for the user
    """

    success: bool
    data: T | None = None
    error: CommandError | None = None

    # UX-enabling fields (AFD standard)
    reasoning: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[Warning] | None = None
    suggestions: list[str] | None = None


def success(
    data: T,
    reasoning: str | None = None,
    confidence: float | None = None,
    warnings: list[Warning] | None = None,
    suggestions: list[str] | None = None,
) -> CommandResult[T]:
    """Create a successful command result.
    
    Args:
        data: The command output
        reasoning: Human-readable explanation
        confidence: Quality confidence score (0-1)
        warnings: Non-fatal warnings
        suggestions: Helpful tips for the user
        
    Returns:
        CommandResult with success=True
    """
    return CommandResult(
        success=True,
        data=data,
        reasoning=reasoning,
        confidence=confidence,
        warnings=warnings,
        suggestions=suggestions,
    )


def error(
    code: str,
    message: str,
    suggestion: str | None = None,
) -> CommandResult[None]:
    """Create an error command result.
    
    Args:
        code: Error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
        message: Human-readable error description
        suggestion: Recovery guidance for the user
        
    Returns:
        CommandResult with success=False and data=None
    """
    return CommandResult(
        success=False,
        error=CommandError(code=code, message=message, suggestion=suggestion),
    )
