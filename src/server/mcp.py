"""Noisett MCP Server - FastMCP integration for AI agent workflows.

This server exposes all Noisett commands as MCP tools, enabling
AI agents in VS Code, Cursor, and other MCP-compatible clients
to generate brand assets directly.

Usage:
    # Run as MCP server (stdio)
    python -m src.server.mcp
    
    # Configure in .cursor/mcp.json:
    {
        "mcpServers": {
            "noisett": {
                "command": "python",
                "args": ["-m", "src.server.mcp"],
                "cwd": "/path/to/noisett"
            }
        }
    }
"""

from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP(
    name="noisett",
    version="0.1.0",
    instructions="Generate on-brand illustrations and icons using AI",
)


# --- Asset Commands ---


@mcp.tool()
async def asset_generate(
    prompt: str,
    asset_type: str = "product",
    model: str = "hidream",
    quality: str = "standard",
    count: int = 4,
) -> dict:
    """Generate brand-aligned images from a text prompt.
    
    Creates a generation job and returns immediately with job ID.
    Use job_status to poll for completion.
    
    Args:
        prompt: Description of the image to generate (1-500 chars)
        asset_type: Type of asset - icons, product, logo, or premium
        model: Model to use - hidream (commercial OK) or flux (reference only)
        quality: Quality preset - draft, standard, or high
        count: Number of variations to generate (1-4)
    
    Returns:
        Job information with ID for status tracking
    """
    from src.commands.asset import AssetGenerateInput, generate
    from src.core.types import AssetType, ModelId, QualityPreset

    input_data = AssetGenerateInput(
        prompt=prompt,
        asset_type=AssetType(asset_type),
        model=ModelId(model),
        quality=QualityPreset(quality),
        count=count,
    )
    result = await generate(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def asset_types() -> dict:
    """List available asset types and their configurations.
    
    Returns information about each asset type including name,
    description, prompt template, and recommended use cases.
    
    Returns:
        Available asset types with configurations
    """
    from src.commands.asset import types

    result = await types()
    return result.model_dump(exclude_none=True)


# --- Job Commands ---


@mcp.tool()
async def job_status(job_id: str) -> dict:
    """Get the current status of a generation job.
    
    Returns job details including status, progress percentage,
    and generated images when complete.
    
    Args:
        job_id: The job ID returned from asset_generate
    
    Returns:
        Job status, progress, and images if complete
    """
    from src.commands.job import JobStatusInput, status

    input_data = JobStatusInput(job_id=job_id)
    result = await status(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def job_cancel(job_id: str) -> dict:
    """Cancel a queued or in-progress generation job.
    
    Jobs that are already complete or cancelled cannot be cancelled.
    
    Args:
        job_id: The job ID to cancel
    
    Returns:
        Updated job status (cancelled)
    """
    from src.commands.job import JobCancelInput, cancel

    input_data = JobCancelInput(job_id=job_id)
    result = await cancel(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def job_list(limit: int = 20, status_filter: str | None = None) -> dict:
    """List recent generation jobs.
    
    Returns jobs sorted by creation time (newest first).
    
    Args:
        limit: Maximum number of jobs to return (1-100)
        status_filter: Optional filter by status (queued, processing, complete, failed)
    
    Returns:
        List of jobs with total count
    """
    from src.commands.job import JobListInput, list_jobs
    from src.core.types import JobStatus

    input_data = JobListInput(
        limit=limit,
        status_filter=JobStatus(status_filter) if status_filter else None,
    )
    result = await list_jobs(input_data)
    return result.model_dump(exclude_none=True)


# --- Model Commands ---


@mcp.tool()
async def model_list() -> dict:
    """List available image generation models.
    
    Returns information about all models including availability
    and licensing information.
    
    Returns:
        List of models with details
    """
    from src.commands.model import list_models

    result = await list_models()
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def model_info(model_id: str) -> dict:
    """Get detailed information about a specific model.
    
    Returns complete model details including license information
    and recommended settings.
    
    Args:
        model_id: Model ID (hidream, flux, or sd35)
    
    Returns:
        Model details including license and availability
    """
    from src.commands.model import ModelInfoInput, info
    from src.core.types import ModelId

    input_data = ModelInfoInput(model_id=ModelId(model_id))
    result = await info(input_data)
    return result.model_dump(exclude_none=True)


# --- History Commands ---


@mcp.tool()
async def history_list(
    limit: int = 50,
    offset: int = 0,
    asset_type: str | None = None,
) -> dict:
    """List generation history for the current user.
    
    Returns past generations sorted by creation time (newest first).
    
    Args:
        limit: Maximum number of records to return (1-200)
        offset: Number of records to skip for pagination
        asset_type: Optional filter by asset type
    
    Returns:
        List of generation records with total count
    """
    from src.commands.history import HistoryListInput, history_list as history_list_cmd
    from src.core.types import AssetType
    from src.core.auth import get_anonymous_user_id

    input_data = HistoryListInput(
        user_id=get_anonymous_user_id(),
        limit=limit,
        offset=offset,
        asset_type=AssetType(asset_type) if asset_type else None,
    )
    result = await history_list_cmd(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def history_get(generation_id: str) -> dict:
    """Get details of a specific generation from history.
    
    Args:
        generation_id: The generation ID to retrieve
    
    Returns:
        Generation details including prompt, images, and metadata
    """
    from src.commands.history import HistoryGetInput, history_get as history_get_cmd
    from src.core.auth import get_anonymous_user_id

    input_data = HistoryGetInput(
        user_id=get_anonymous_user_id(),
        generation_id=generation_id,
    )
    result = await history_get_cmd(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def history_delete(generation_id: str) -> dict:
    """Delete a generation from history.
    
    This permanently removes the generation record. The images
    may still exist in storage but will be orphaned.
    
    Args:
        generation_id: The generation ID to delete
    
    Returns:
        Confirmation of deletion
    """
    from src.commands.history import HistoryDeleteInput, history_delete as history_delete_cmd
    from src.core.auth import get_anonymous_user_id

    input_data = HistoryDeleteInput(
        user_id=get_anonymous_user_id(),
        generation_id=generation_id,
    )
    result = await history_delete_cmd(input_data)
    return result.model_dump(exclude_none=True)


# --- Favorites Commands ---


@mcp.tool()
async def favorites_add(
    generation_id: str,
    prompt: str | None = None,
    notes: str | None = None,
) -> dict:
    """Add a generation to favorites.
    
    Saves a generation for quick access later. Optionally add
    notes to remember why it was favorited.
    
    Args:
        generation_id: The generation ID to favorite
        prompt: Original prompt (for display)
        notes: Optional notes about why this was favorited
    
    Returns:
        Favorite record with timestamp
    """
    from src.commands.favorites import FavoriteAddInput, favorites_add as favorites_add_cmd
    from src.core.auth import get_anonymous_user_id

    input_data = FavoriteAddInput(
        user_id=get_anonymous_user_id(),
        generation_id=generation_id,
        prompt=prompt,
        notes=notes,
    )
    result = await favorites_add_cmd(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def favorites_list(limit: int = 50) -> dict:
    """List favorited generations.
    
    Returns favorites sorted by when they were added (newest first).
    
    Args:
        limit: Maximum number of favorites to return (1-100)
    
    Returns:
        List of favorites with total count
    """
    from src.commands.favorites import FavoritesListInput, favorites_list as favorites_list_cmd
    from src.core.auth import get_anonymous_user_id

    input_data = FavoritesListInput(
        user_id=get_anonymous_user_id(),
        limit=limit,
    )
    result = await favorites_list_cmd(input_data)
    return result.model_dump(exclude_none=True)


@mcp.tool()
async def favorites_remove(generation_id: str) -> dict:
    """Remove a generation from favorites.
    
    This only removes the favorite record, not the generation itself.
    
    Args:
        generation_id: The generation ID to unfavorite
    
    Returns:
        Confirmation of removal
    """
    from src.commands.favorites import FavoriteRemoveInput, favorites_remove as favorites_remove_cmd
    from src.core.auth import get_anonymous_user_id

    input_data = FavoriteRemoveInput(
        user_id=get_anonymous_user_id(),
        generation_id=generation_id,
    )
    result = await favorites_remove_cmd(input_data)
    return result.model_dump(exclude_none=True)


# --- Entry Point ---


if __name__ == "__main__":
    mcp.run()
