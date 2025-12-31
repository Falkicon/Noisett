# MCP Server Integration

Noisett exposes all commands as MCP tools, enabling AI agents in VS Code, Cursor, and other MCP-compatible clients to generate brand assets directly.

---

## Overview

The MCP server is built with **FastMCP** (official Python SDK), which automatically generates tool definitions from Python type hints and docstrings. This aligns perfectly with AFD: the same Pydantic schemas used for CLI validation become MCP tool schemas.

```
┌─────────────────────────────────────────────────────────────────┐
│  VS Code / Cursor with Claude                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  User: "Generate an icon of a cloud with an upload arrow"  ││
│  │                                                             ││
│  │  Claude: I'll use the asset.generate tool...               ││
│  │  [Calls noisett MCP server]                                 ││
│  │                                                             ││
│  │  Result: Generated 4 icon variations, job ID: abc-123      ││
│  │  Images available at: [blob URLs]                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
         │
         │ MCP (stdio)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Noisett MCP Server (FastMCP)                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  @mcp.tool()                                                ││
│  │  async def asset_generate(prompt: str, ...) -> dict         ││
│  │      return await commands.asset.generate(input)            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## FastMCP Implementation

### Server Setup

```python
# src/server/mcp.py
from fastmcp import FastMCP
from src.commands import asset, job, model
from src.core.result import CommandResult

# Create MCP server (FastMCP 2.x uses 'instructions' instead of 'description')
mcp = FastMCP(
    name="noisett",
    version="0.1.0",
    instructions="Generate on-brand illustrations and icons using AI"
)

# --- Asset Commands ---

@mcp.tool()
async def asset_generate(
    prompt: str,
    asset_type: str = "product",
    model: str = "hidream",
    quality: str = "standard",
    count: int = 4
) -> dict:
    """
    Generate brand-aligned images from a text prompt.

    Args:
        prompt: Description of the image to generate (1-500 chars)
        asset_type: Type of asset - icons, product, logo, or premium
        model: Model to use - hidream (commercial OK) or flux (reference only)
        quality: Quality preset - draft, standard, or high
        count: Number of variations to generate (1-4)

    Returns:
        Job information with ID for status tracking
    """
    from src.commands.asset import GenerateInput, generate

    input_data = GenerateInput(
        prompt=prompt,
        asset_type=asset_type,
        model=model,
        quality=quality,
        count=count
    )
    result = await generate(input_data)
    return result.model_dump()


@mcp.tool()
async def asset_types() -> dict:
    """
    List available asset types and their configurations.

    Returns:
        Available asset types with prompt templates and recommendations
    """
    from src.commands.asset import types
    result = await types()
    return result.model_dump()


# --- Job Commands ---

@mcp.tool()
async def job_status(job_id: str) -> dict:
    """
    Get the current status of a generation job.

    Args:
        job_id: The job ID returned from asset_generate

    Returns:
        Job status, progress percentage, and images if complete
    """
    from src.commands.job import StatusInput, status

    input_data = StatusInput(job_id=job_id)
    result = await status(input_data)
    return result.model_dump()


@mcp.tool()
async def job_cancel(job_id: str) -> dict:
    """
    Cancel a queued or in-progress generation job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Updated job status (cancelled)
    """
    from src.commands.job import CancelInput, cancel

    input_data = CancelInput(job_id=job_id)
    result = await cancel(input_data)
    return result.model_dump()


@mcp.tool()
async def job_list(limit: int = 20, status: str | None = None) -> dict:
    """
    List recent generation jobs.

    Args:
        limit: Maximum number of jobs to return (1-100)
        status: Optional filter by status (queued, processing, complete, failed)

    Returns:
        List of recent jobs with their status and results
    """
    from src.commands.job import ListInput, list_jobs

    input_data = ListInput(limit=limit, status=status)
    result = await list_jobs(input_data)
    return result.model_dump()


# --- Model Commands ---

@mcp.tool()
async def model_list() -> dict:
    """
    List available image generation models.

    Returns:
        Available models with licensing info (commercial_ok flag)
    """
    from src.commands.model import list_models
    result = await list_models()
    return result.model_dump()


@mcp.tool()
async def model_info(model_id: str) -> dict:
    """
    Get detailed information about a specific model.

    Args:
        model_id: Model ID (hidream, flux, sd35)

    Returns:
        Model details including VRAM requirements and licensing
    """
    from src.commands.model import InfoInput, info

    input_data = InfoInput(model_id=model_id)
    result = await info(input_data)
    return result.model_dump()


# Entry point
if __name__ == "__main__":
    mcp.run()
```

### Running the Server

```bash
# Development (stdio mode for local testing)
python -m src.server.mcp

# Or via the CLI
noisett serve --mcp
```

---

## Client Configuration

### VS Code / Cursor

Add to your MCP settings (`.cursor/mcp.json` or VS Code equivalent):

```json
{
  "mcpServers": {
    "noisett": {
      "command": "python",
      "args": ["-m", "src.server.mcp"],
      "cwd": "D:/Github/Falkicon/Noisett",
      "env": {
        "AZURE_STORAGE_CONNECTION_STRING": "${env:AZURE_STORAGE_CONNECTION_STRING}"
      }
    }
  }
}
```

### Alternative: uvx (if published to PyPI)

```json
{
  "mcpServers": {
    "noisett": {
      "command": "uvx",
      "args": ["noisett-mcp"]
    }
  }
}
```

---

## Tool Discovery

Once configured, the MCP client will discover these tools:

| Tool             | Description                                         |
| ---------------- | --------------------------------------------------- |
| `asset_generate` | Generate brand-aligned images from a text prompt    |
| `asset_types`    | List available asset types and their configurations |
| `job_status`     | Get the current status of a generation job          |
| `job_cancel`     | Cancel a queued or in-progress generation job       |
| `job_list`       | List recent generation jobs                         |
| `model_list`     | List available image generation models              |
| `model_info`     | Get detailed information about a specific model     |

---

## Agent Workflow Example

A typical workflow for an AI agent using Noisett:

```
User: "I need an icon of a cloud with an upload arrow for our file sharing feature"

Agent thinking:
1. User needs an icon → use asset_generate with asset_type="icons"
2. Should check available models first → use model_list
3. HiDream is commercial OK → proceed with hidream model

Agent actions:
1. Call model_list() → sees hidream is available and commercial_ok
2. Call asset_generate(
     prompt="cloud with upload arrow, file sharing concept",
     asset_type="icons",
     model="hidream",
     count=4
   )
3. Receive job_id: "abc-123"
4. Call job_status(job_id="abc-123") → processing, 50%
5. Wait, call again → complete, 4 images available
6. Return image URLs to user

Agent response:
"I've generated 4 icon variations for your file sharing feature. Here are the results:
- [Image 1 URL] - Clean minimal style
- [Image 2 URL] - Slightly more detailed
- [Image 3 URL] - Alternative composition
- [Image 4 URL] - Variant with different arrow style

All images are commercial-use ready (generated with HiDream model).
Would you like me to generate more variations or try a different style?"
```

---

## Error Handling

MCP tools return structured errors that agents can understand:

```python
# Error response example
{
  "success": false,
  "error": {
    "code": "PROMPT_TOO_LONG",
    "message": "Prompt exceeds 500 character limit",
    "suggestion": "Shorten your prompt or split into multiple requests"
  }
}
```

The `suggestion` field helps agents self-correct:

```
Agent: The prompt was too long. Let me shorten it...
[Retries with shorter prompt]
```

---

## UX-Enabling Fields

Commands return metadata that helps agents provide better UX:

### `reasoning`

Explains what happened in human-readable terms:

```python
{
  "success": true,
  "data": {...},
  "reasoning": "Started generation of 4 product illustrations using HiDream"
}
```

Agent can relay this directly to user.

### `confidence`

For AI-generated content quality assessment:

```python
{
  "success": true,
  "data": {...},
  "confidence": 0.85,
  "reasoning": "High confidence - prompt is clear and model is well-suited"
}
```

Agent can adjust messaging based on confidence.

### `suggestions`

Guide next steps:

```python
{
  "success": true,
  "data": {...},
  "suggestions": [
    "Try 'premium' asset type for marketing-grade quality",
    "Use 'high' quality preset for final assets"
  ]
}
```

Agent can proactively offer these options.

---

## Testing MCP Integration

### 1. Verify Server Starts

```bash
python -m src.server.mcp
# Should output: "Noisett MCP server running on stdio"
```

### 2. Test Tool Discovery

In VS Code/Cursor with MCP configured:

- Open Claude chat
- Type: "What tools do you have access to?"
- Should list all Noisett tools

### 3. Test Generation Flow

```
User: "Generate a test icon"
Agent: [Should call asset_generate, then job_status]
```

### 4. Verify Error Handling

```
User: "Generate an image with this very long prompt that exceeds 500 characters..."
Agent: [Should receive error with suggestion, may auto-retry]
```

---

## Security Considerations

### Authentication

For internal use, the MCP server trusts the stdio connection from the host IDE. The IDE handles user authentication via Entra ID.

For production, consider:

- Passing user context from IDE to MCP server
- Rate limiting per user
- Audit logging

### Resource Access

The MCP server has access to:

- Azure Blob Storage (for image storage)
- GPU compute (for generation)
- User's job history

Ensure proper Azure RBAC for the service principal.

---

## Deployment Options

### Local Development

```bash
# Run MCP server directly
python -m src.server.mcp
```

### Remote Server (Future)

For team-wide access without local GPU:

```json
{
  "mcpServers": {
    "noisett": {
      "transport": "sse",
      "url": "https://noisett-api.internal.company.com/mcp"
    }
  }
}
```

This requires the FastAPI server to expose an SSE endpoint for MCP.
