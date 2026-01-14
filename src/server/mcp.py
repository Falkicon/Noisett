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
    version="0.9.2",
    instructions="Generate on-brand illustrations and icons using AI",
)


# --- Bootstrap Commands (AFD Standard) ---


# Registry of all commands with their metadata
COMMANDS = {
    "asset_generate": {"tags": ["asset", "create", "write"], "mutation": True, "description": "Generate brand-aligned images from a text prompt"},
    "asset_types": {"tags": ["asset", "list", "read", "bootstrap"], "mutation": False, "description": "List available asset types"},
    "job_status": {"tags": ["job", "read", "single"], "mutation": False, "description": "Get job status"},
    "job_cancel": {"tags": ["job", "delete", "write", "destructive"], "mutation": True, "description": "Cancel a job"},
    "job_list": {"tags": ["job", "list", "read"], "mutation": False, "description": "List recent jobs"},
    "model_list": {"tags": ["model", "list", "read", "bootstrap"], "mutation": False, "description": "List available models"},
    "model_info": {"tags": ["model", "read", "single"], "mutation": False, "description": "Get model details"},
    "history_list": {"tags": ["history", "list", "read"], "mutation": False, "description": "List generation history"},
    "history_get": {"tags": ["history", "read", "single"], "mutation": False, "description": "Get generation details"},
    "history_delete": {"tags": ["history", "delete", "write", "destructive"], "mutation": True, "description": "Delete from history"},
    "favorites_add": {"tags": ["favorites", "create", "write"], "mutation": True, "description": "Add to favorites"},
    "favorites_list": {"tags": ["favorites", "list", "read"], "mutation": False, "description": "List favorites"},
    "favorites_remove": {"tags": ["favorites", "delete", "write"], "mutation": True, "description": "Remove from favorites"},
}


@mcp.tool(meta={"tags": ["bootstrap", "help"], "mutation": False})
async def noisett_help(
    tag: str | None = None,
    category: str | None = None,
) -> dict:
    """List available Noisett commands with optional filtering.
    
    Use this to discover what commands are available and their purpose.
    Filter by tag or category to find relevant commands.
    
    Args:
        tag: Filter by tag (e.g., 'read', 'write', 'destructive')
        category: Filter by category (e.g., 'asset', 'job', 'model')
    
    Returns:
        List of commands with descriptions and tags
    """
    result = []
    for name, meta in COMMANDS.items():
        # Filter by tag
        if tag and tag not in meta["tags"]:
            continue
        # Filter by category (first tag is typically the category)
        if category and meta["tags"][0] != category:
            continue
        result.append({
            "name": name,
            "description": meta["description"],
            "tags": meta["tags"],
            "mutation": meta["mutation"],
        })
    
    return {
        "success": True,
        "data": {"commands": result, "total": len(result)},
        "reasoning": f"Found {len(result)} commands" + (f" matching filters" if tag or category else ""),
    }


@mcp.tool(meta={"tags": ["bootstrap", "docs"], "mutation": False})
async def noisett_docs() -> dict:
    """Generate markdown documentation for all Noisett commands.
    
    Returns complete documentation suitable for agent context or
    human reference.
    
    Returns:
        Markdown documentation string
    """
    lines = ["# Noisett Commands", "", "AI-powered brand asset generation.", ""]
    
    # Group by category
    categories: dict[str, list] = {}
    for name, meta in COMMANDS.items():
        cat = meta["tags"][0]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((name, meta))
    
    for cat, cmds in sorted(categories.items()):
        lines.append(f"## {cat.title()}")
        lines.append("")
        for name, meta in cmds:
            mutation = "⚠️ " if meta["mutation"] else ""
            lines.append(f"- **{name}**: {mutation}{meta['description']}")
        lines.append("")
    
    return {
        "success": True,
        "data": {"markdown": "\n".join(lines)},
        "reasoning": f"Generated docs for {len(COMMANDS)} commands",
    }


@mcp.tool(meta={"tags": ["bootstrap", "schema"], "mutation": False})
async def noisett_schema(command: str | None = None) -> dict:
    """Export JSON schemas for command inputs.
    
    Returns Pydantic-generated JSON schemas for command validation.
    
    Args:
        command: Specific command to get schema for (optional, all if omitted)
    
    Returns:
        JSON schemas for command inputs
    """
    from src.commands.asset import AssetGenerateInput
    from src.commands.job import JobStatusInput, JobCancelInput, JobListInput
    from src.commands.model import ModelInfoInput
    
    schemas = {
        "asset_generate": AssetGenerateInput.model_json_schema(),
        "job_status": JobStatusInput.model_json_schema(),
        "job_cancel": JobCancelInput.model_json_schema(),
        "job_list": JobListInput.model_json_schema(),
        "model_info": ModelInfoInput.model_json_schema(),
    }
    
    if command:
        if command not in schemas:
            return {
                "success": False,
                "error": {"code": "NOT_FOUND", "message": f"Unknown command: {command}"},
            }
        return {
            "success": True,
            "data": {"command": command, "schema": schemas[command]},
            "reasoning": f"Schema for {command}",
        }
    
    return {
        "success": True,
        "data": {"schemas": schemas},
        "reasoning": f"Schemas for {len(schemas)} commands",
    }


# --- Asset Commands ---


@mcp.tool(meta={"tags": ["asset", "create", "write"], "mutation": True})
async def asset_generate(
    prompt: str,
    asset_type: str = "product",
    model: str = "hidream",
    quality: str = "standard",
    count: int = 1,
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


@mcp.tool(meta={"tags": ["asset", "list", "read", "bootstrap"], "mutation": False})
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


@mcp.tool(meta={"tags": ["job", "read", "single"], "mutation": False})
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


@mcp.tool(meta={"tags": ["job", "delete", "write", "destructive"], "mutation": True})
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


@mcp.tool(meta={"tags": ["job", "list", "read"], "mutation": False})
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


@mcp.tool(meta={"tags": ["model", "list", "read", "bootstrap"], "mutation": False})
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


@mcp.tool(meta={"tags": ["model", "read", "single"], "mutation": False})
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


@mcp.tool(meta={"tags": ["history", "list", "read"], "mutation": False})
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


@mcp.tool(meta={"tags": ["history", "read", "single"], "mutation": False})
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


@mcp.tool(meta={"tags": ["history", "delete", "write", "destructive"], "mutation": True})
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


@mcp.tool(meta={"tags": ["favorites", "create", "write"], "mutation": True})
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


@mcp.tool(meta={"tags": ["favorites", "list", "read"], "mutation": False})
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


@mcp.tool(meta={"tags": ["favorites", "delete", "write"], "mutation": True})
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
