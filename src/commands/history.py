"""History commands for Noisett.

Phase 8: Commands for managing user generation history.

Commands:
    history.list - List user's generation history
    history.get - Get details of a specific generation
    history.delete - Delete a generation from history
"""

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode, get_error_template
from src.core.result import CommandResult
from src.core.storage import (
    delete_generation,
    get_generation,
    list_generations,
)
from src.core.types import (
    GenerationRecord,
    HistoryListInput,
    HistoryListOutput,
)


# ============================================================================
# Input/Output Schemas
# ============================================================================

class HistoryGetInput(BaseModel):
    """Input for history.get command."""
    
    job_id: str = Field(
        ...,
        description="Job ID to retrieve",
        examples=["job_abc123"],
    )


class HistoryDeleteInput(BaseModel):
    """Input for history.delete command."""
    
    job_id: str = Field(
        ...,
        description="Job ID to delete from history",
        examples=["job_abc123"],
    )


class HistoryDeleteOutput(BaseModel):
    """Output for history.delete command."""
    
    deleted: bool = Field(
        ...,
        description="Whether the record was deleted",
    )
    job_id: str = Field(
        ...,
        description="Job ID that was deleted",
    )


# ============================================================================
# Command Implementations
# ============================================================================

def history_list(
    user_id: str,
    input_data: HistoryListInput | None = None,
) -> CommandResult[HistoryListOutput]:
    """List user's generation history.
    
    Args:
        user_id: Authenticated user's ID
        input_data: Pagination options (limit, offset)
        
    Returns:
        CommandResult with list of generations
        
    CLI Example:
        noisett history.list '{}'
        noisett history.list '{"limit": 10, "offset": 20}'
    """
    if input_data is None:
        input_data = HistoryListInput()
    
    try:
        records, total = list_generations(
            user_id=user_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )
        
        has_more = input_data.offset + len(records) < total
        
        return CommandResult(
            success=True,
            data=HistoryListOutput(
                generations=records,
                total_count=total,
                has_more=has_more,
            ),
            reasoning=f"Retrieved {len(records)} of {total} generations",
        )
        
    except Exception as e:
        template = get_error_template(ErrorCode.INTERNAL_ERROR)
        return CommandResult(
            success=False,
            error={
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": template["message"],
                "suggestion": template["suggestion"],
                "details": str(e),
            },
        )


def history_get(
    user_id: str,
    input_data: HistoryGetInput,
) -> CommandResult[GenerationRecord]:
    """Get details of a specific generation.
    
    Args:
        user_id: Authenticated user's ID
        input_data: Job ID to retrieve
        
    Returns:
        CommandResult with generation details
        
    CLI Example:
        noisett history.get '{"job_id": "job_abc123"}'
    """
    try:
        record = get_generation(
            job_id=input_data.job_id,
            user_id=user_id,
        )
        
        if not record:
            template = get_error_template(ErrorCode.HISTORY_NOT_FOUND)
            return CommandResult(
                success=False,
                error={
                    "code": ErrorCode.HISTORY_NOT_FOUND.value,
                    "message": template["message"],
                    "suggestion": template["suggestion"],
                },
            )
        
        return CommandResult(
            success=True,
            data=record,
            reasoning=f"Retrieved generation with {len(record.images)} images",
        )
        
    except Exception as e:
        template = get_error_template(ErrorCode.INTERNAL_ERROR)
        return CommandResult(
            success=False,
            error={
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": template["message"],
                "suggestion": template["suggestion"],
                "details": str(e),
            },
        )


def history_delete(
    user_id: str,
    input_data: HistoryDeleteInput,
) -> CommandResult[HistoryDeleteOutput]:
    """Delete a generation from history.
    
    Args:
        user_id: Authenticated user's ID
        input_data: Job ID to delete
        
    Returns:
        CommandResult confirming deletion
        
    CLI Example:
        noisett history.delete '{"job_id": "job_abc123"}'
    """
    try:
        deleted = delete_generation(
            job_id=input_data.job_id,
            user_id=user_id,
        )
        
        if not deleted:
            template = get_error_template(ErrorCode.HISTORY_NOT_FOUND)
            return CommandResult(
                success=False,
                error={
                    "code": ErrorCode.HISTORY_NOT_FOUND.value,
                    "message": template["message"],
                    "suggestion": template["suggestion"],
                },
            )
        
        return CommandResult(
            success=True,
            data=HistoryDeleteOutput(
                deleted=True,
                job_id=input_data.job_id,
            ),
            reasoning=f"Deleted generation {input_data.job_id} from history",
        )
        
    except Exception as e:
        template = get_error_template(ErrorCode.INTERNAL_ERROR)
        return CommandResult(
            success=False,
            error={
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": template["message"],
                "suggestion": template["suggestion"],
                "details": str(e),
            },
        )


# Export for easy imports
__all__ = [
    # Input/Output types
    "HistoryListInput",
    "HistoryListOutput",
    "HistoryGetInput",
    "HistoryDeleteInput",
    "HistoryDeleteOutput",
    # Commands
    "history_list",
    "history_get",
    "history_delete",
]
