"""Favorites commands for Noisett.

Phase 8: Commands for managing user favorite images.

Commands:
    favorites.add - Add an image to favorites
    favorites.list - List user's favorited images
    favorites.remove - Remove an image from favorites
"""

import sqlite3

from pydantic import BaseModel, Field

from src.core.errors import ErrorCode, get_error_template
from src.core.result import CommandResult
from src.core.storage import (
    add_favorite,
    get_favorite,
    list_favorites,
    remove_favorite,
)
from src.core.types import (
    Favorite,
    FavoriteInput,
    FavoritesListOutput,
)


# ============================================================================
# Input/Output Schemas
# ============================================================================

class FavoritesAddInput(BaseModel):
    """Input for favorites.add command."""
    
    job_id: str = Field(
        ...,
        description="Job ID of the generation containing the image",
        examples=["job_abc123"],
    )
    image_index: int = Field(
        ...,
        ge=0,
        description="Index of the image in the job results (0-based)",
        examples=[0, 1, 2, 3],
    )
    image_url: str = Field(
        ...,
        description="URL of the image to favorite",
    )
    prompt: str | None = Field(
        None,
        description="Optional prompt that generated the image",
    )


class FavoritesRemoveInput(BaseModel):
    """Input for favorites.remove command."""
    
    job_id: str = Field(
        ...,
        description="Job ID of the favorited image",
        examples=["job_abc123"],
    )
    image_index: int = Field(
        ...,
        ge=0,
        description="Index of the image to remove from favorites",
        examples=[0, 1, 2, 3],
    )


class FavoritesRemoveOutput(BaseModel):
    """Output for favorites.remove command."""
    
    removed: bool = Field(
        ...,
        description="Whether the favorite was removed",
    )
    job_id: str = Field(
        ...,
        description="Job ID of the removed favorite",
    )
    image_index: int = Field(
        ...,
        description="Image index of the removed favorite",
    )


class FavoritesListInput(BaseModel):
    """Input for favorites.list command."""
    
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of favorites to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of favorites to skip (for pagination)",
    )


# ============================================================================
# Command Implementations
# ============================================================================

def favorites_add(
    user_id: str,
    input_data: FavoritesAddInput,
) -> CommandResult[Favorite]:
    """Add an image to favorites.
    
    Args:
        user_id: Authenticated user's ID
        input_data: Favorite details (job_id, image_index, image_url)
        
    Returns:
        CommandResult with created favorite
        
    CLI Example:
        noisett favorites.add '{"job_id": "job_abc", "image_index": 0, "image_url": "https://..."}'
    """
    try:
        favorite = add_favorite(
            user_id=user_id,
            job_id=input_data.job_id,
            image_index=input_data.image_index,
            image_url=input_data.image_url,
            prompt=input_data.prompt,
        )
        
        return CommandResult(
            success=True,
            data=favorite,
            reasoning=f"Added image {input_data.image_index} from job {input_data.job_id} to favorites",
        )
        
    except sqlite3.IntegrityError:
        template = get_error_template(ErrorCode.FAVORITE_ALREADY_EXISTS)
        return CommandResult(
            success=False,
            error={
                "code": ErrorCode.FAVORITE_ALREADY_EXISTS.value,
                "message": template["message"],
                "suggestion": template["suggestion"],
            },
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


def favorites_list(
    user_id: str,
    input_data: FavoritesListInput | None = None,
) -> CommandResult[FavoritesListOutput]:
    """List user's favorited images.
    
    Args:
        user_id: Authenticated user's ID
        input_data: Pagination options (limit, offset)
        
    Returns:
        CommandResult with list of favorites
        
    CLI Example:
        noisett favorites.list '{}'
        noisett favorites.list '{"limit": 10}'
    """
    if input_data is None:
        input_data = FavoritesListInput()
    
    try:
        favorites, total = list_favorites(
            user_id=user_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )
        
        return CommandResult(
            success=True,
            data=FavoritesListOutput(
                favorites=favorites,
                total_count=total,
            ),
            reasoning=f"Retrieved {len(favorites)} of {total} favorites",
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


def favorites_remove(
    user_id: str,
    input_data: FavoritesRemoveInput,
) -> CommandResult[FavoritesRemoveOutput]:
    """Remove an image from favorites.
    
    Args:
        user_id: Authenticated user's ID
        input_data: Favorite to remove (job_id, image_index)
        
    Returns:
        CommandResult confirming removal
        
    CLI Example:
        noisett favorites.remove '{"job_id": "job_abc", "image_index": 0}'
    """
    try:
        removed = remove_favorite(
            user_id=user_id,
            job_id=input_data.job_id,
            image_index=input_data.image_index,
        )
        
        if not removed:
            template = get_error_template(ErrorCode.FAVORITE_NOT_FOUND)
            return CommandResult(
                success=False,
                error={
                    "code": ErrorCode.FAVORITE_NOT_FOUND.value,
                    "message": template["message"],
                    "suggestion": template["suggestion"],
                },
            )
        
        return CommandResult(
            success=True,
            data=FavoritesRemoveOutput(
                removed=True,
                job_id=input_data.job_id,
                image_index=input_data.image_index,
            ),
            reasoning=f"Removed image {input_data.image_index} from job {input_data.job_id} from favorites",
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
    "FavoritesAddInput",
    "FavoritesListInput",
    "FavoritesRemoveInput",
    "FavoritesRemoveOutput",
    # Commands
    "favorites_add",
    "favorites_list",
    "favorites_remove",
]
