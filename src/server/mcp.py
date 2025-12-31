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


# --- Entry Point ---


if __name__ == "__main__":
    mcp.run()
