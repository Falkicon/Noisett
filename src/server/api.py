"""Noisett REST API - FastAPI server for web UI.

This server exposes all Noisett commands as REST endpoints.
Following AFD principles, this is a thin wrapper over commands.

Usage:
    # Development
    uvicorn src.server.api:app --reload --port 8000
    
    # Production
    uvicorn src.server.api:app --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.core.types import AssetType, ModelId, QualityPreset, JobStatus


# --- Request/Response Models ---


class GenerateRequest(BaseModel):
    """Request body for image generation."""
    
    prompt: str = Field(..., min_length=1, max_length=500, description="Image description")
    asset_type: str = Field(default="product", description="Type of asset to generate")
    model: str = Field(default="hidream", description="Model to use")
    quality: str = Field(default="standard", description="Quality preset")
    count: int = Field(default=4, ge=1, le=4, description="Number of variations")


class CancelRequest(BaseModel):
    """Request body for job cancellation."""
    
    reason: Optional[str] = Field(default=None, description="Cancellation reason")


# --- App Setup ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan handler for startup/shutdown."""
    # Startup
    print("🎨 Noisett API starting...")
    yield
    # Shutdown
    print("🎨 Noisett API shutting down...")


app = FastAPI(
    title="Noisett API",
    description="Generate on-brand illustrations and icons using AI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check ---


@app.get("/health")
async def health_check():
    """Health check endpoint for Container Apps monitoring.
    
    Returns system status including GPU availability.
    Used by Azure Container Apps for liveness/readiness probes.
    """
    import os
    
    # Check GPU availability (only if torch is installed)
    gpu_available = False
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except ImportError:
        pass
    
    return {
        "status": "healthy" if gpu_available else "degraded",
        "service": "noisett-api",
        "version": "0.6.0",
        "gpu_available": gpu_available,
        "environment": os.getenv("NOISETT_ENV", "development"),
    }


# --- Asset Endpoints ---


@app.post("/api/generate")
async def generate_asset(request: GenerateRequest):
    """Generate brand-aligned images from a text prompt.
    
    Creates a generation job and returns immediately with job ID.
    Poll /api/jobs/{id} for completion.
    """
    from src.commands.asset import AssetGenerateInput, generate

    try:
        input_data = AssetGenerateInput(
            prompt=request.prompt,
            asset_type=AssetType(request.asset_type),
            model=ModelId(request.model),
            quality=QualityPreset(request.quality),
            count=request.count,
        )
        result = await generate(input_data)
        return result.model_dump(exclude_none=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/asset-types")
async def get_asset_types():
    """List available asset types and their configurations."""
    from src.commands.asset import types

    result = await types()
    return result.model_dump(exclude_none=True)


# --- Job Endpoints ---


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the current status of a generation job.
    
    Returns job details including status, progress percentage,
    and generated images when complete.
    """
    from src.commands.job import JobStatusInput, status

    try:
        input_data = JobStatusInput(job_id=job_id)
        result = await status(input_data)
        
        # Return 404 if job not found
        if not result.success and result.error and result.error.code == "JOB_NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error.message)
        
        return result.model_dump(exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str, request: Optional[CancelRequest] = None):
    """Cancel a running generation job."""
    from src.commands.job import JobCancelInput, cancel

    try:
        input_data = JobCancelInput(
            job_id=job_id,
            reason=request.reason if request else None,
        )
        result = await cancel(input_data)
        
        if not result.success and result.error:
            if result.error.code == "JOB_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result.error.message)
            raise HTTPException(status_code=400, detail=result.error.message)
        
        return result.model_dump(exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=10, ge=1, le=100, description="Max results"),
):
    """List recent generation jobs for the current user."""
    from src.commands.job import JobListInput, list_jobs as list_jobs_cmd

    try:
        input_data = JobListInput(
            status=JobStatus(status) if status else None,
            limit=limit,
        )
        result = await list_jobs_cmd(input_data)
        return result.model_dump(exclude_none=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Model Endpoints ---


@app.get("/api/models")
async def get_models():
    """List available AI models and their capabilities."""
    from src.commands.model import list_models

    result = await list_models()
    return result.model_dump(exclude_none=True)


@app.get("/api/models/{model_id}")
async def get_model_info(model_id: str):
    """Get detailed information about a specific model."""
    from src.commands.model import ModelInfoInput, info

    try:
        input_data = ModelInfoInput(model_id=ModelId(model_id))
        result = await info(input_data)
        
        if not result.success and result.error:
            raise HTTPException(status_code=404, detail=result.error.message)
        
        return result.model_dump(exclude_none=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid model ID: {model_id}")


# --- Static Files (Web UI) ---
# Mount after API routes so /api/* takes precedence


def setup_static_files():
    """Mount static files for web UI if directory exists."""
    import os
    
    web_dir = os.path.join(os.path.dirname(__file__), "..", "..", "web")
    if os.path.exists(web_dir):
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")
        return True
    return False


# Mount static files on import
_static_mounted = setup_static_files()


# --- CLI Entry Point ---


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.server.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
