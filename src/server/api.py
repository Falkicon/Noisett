"""Noisett REST API - FastAPI server for web UI.

This server exposes all Noisett commands as REST endpoints.
Following AFD principles, this is a thin wrapper over commands.

Usage:
    # Development
    uvicorn src.server.api:app --reload --port 8000
    
    # Production
    uvicorn src.server.api:app --host 0.0.0.0 --port 8000
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.core.types import AssetType, ModelId, QualityPreset, JobStatus
from src.core.convex_client import get_convex_client


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
    
    reason: str | None = Field(default=None, description="Cancellation reason")


# --- Background Task for Job Processing ---


async def process_job(job_id: str):
    """Process a job in the background using the configured ML backend."""
    from src.commands.asset import get_job, update_job
    from src.core.types import JobStatus
    
    # Get the job
    job = get_job(job_id)
    if not job or job.status != JobStatus.QUEUED:
        return
    
    # Update to processing
    job.status = JobStatus.PROCESSING
    job.progress = 0.1
    update_job(job)
    
    try:
        # Get the appropriate generator based on ML_BACKEND env var
        backend = os.environ.get("ML_BACKEND", "mock")
        
        if backend == "mock":
            from src.ml import MockGenerator
            generator = MockGenerator()
        elif backend == "huggingface":
            from src.ml import HuggingFaceGenerator
            generator = HuggingFaceGenerator()
        elif backend == "fireworks":
            from src.ml import FireworksGenerator
            generator = FireworksGenerator()
        elif backend == "replicate":
            from src.ml import ReplicateGenerator
            generator = ReplicateGenerator()
        else:
            from src.ml import MockGenerator
            generator = MockGenerator()
        
        # Update progress
        job.progress = 0.3
        update_job(job)
        
        # Generate images
        images = await generator.generate(
            prompt=job.prompt,
            asset_type=job.asset_type,
            model=job.model,
            quality=job.quality,
            count=job.count,
        )
        
        # Update job with results
        job.status = JobStatus.COMPLETE
        job.progress = 1.0
        job.images = images
        update_job(job)
        
    except Exception as e:
        # Mark job as failed
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        update_job(job)


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

# CORS configuration
# Read allowed origins from environment or use defaults
CORS_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
).split(",")

# In development, allow all origins if explicitly set
if os.getenv("CORS_ALLOW_ALL", "false").lower() == "true":
    CORS_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
async def generate_asset(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate brand-aligned images from a text prompt.
    
    Creates a generation job and starts processing in background.
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
        
        # Start processing the job in background
        if result.success and result.data:
            background_tasks.add_task(process_job, result.data.job.id)
        
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
async def cancel_job(job_id: str, request: CancelRequest | None = None):
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
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=10, ge=1, le=100, description="Max results"),
):
    """List recent generation jobs for the current user."""
    from src.commands.job import JobListInput, list_jobs as list_jobs_cmd

    try:
        input_data = JobListInput(
            status_filter=JobStatus(status) if status else None,
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


# --- Generated Images Endpoint ---


@app.get("/api/images/{filename}")
async def get_generated_image(filename: str):
    """Serve generated images from temp directory."""
    import tempfile
    from pathlib import Path
    
    # Validate filename (prevent path traversal)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    image_path = Path(tempfile.gettempdir()) / "noisett" / filename
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    content_type = "image/jpeg" if filename.endswith(".jpg") else "image/png"
    
    return FileResponse(image_path, media_type=content_type)


# --- Training SSE Endpoints (AFD Handoff Pattern) ---


from sse_starlette.sse import EventSourceResponse


async def training_event_generator(lora_id: str):
    """Generate SSE events for LoRA training progress.
    
    Yields events in format:
        event: progress
        data: {"step": 100, "total": 1000, "percent": 10, "message": "..."}
        
        event: complete
        data: {"lora_id": "...", "lora_url": "..."}
        
        event: error
        data: {"code": "...", "message": "..."}
    """
    from src.commands.lora import _loras
    from src.core.types import LoraStatus
    import json
    
    # Get the LoRA
    lora = _loras.get(lora_id)
    if not lora:
        yield {
            "event": "error",
            "data": json.dumps({"code": "LORA_NOT_FOUND", "message": f"LoRA '{lora_id}' not found"}),
        }
        return
    
    # Simulate training progress (in production, poll Replicate API)
    for step in range(0, lora.steps + 1, lora.steps // 10 or 1):
        # Check if still training
        if lora.status != LoraStatus.TRAINING:
            break
            
        progress = int((step / lora.steps) * 100)
        lora.current_step = step
        lora.progress = progress
        
        yield {
            "event": "progress",
            "data": json.dumps({
                "step": step,
                "total": lora.steps,
                "percent": progress,
                "message": f"Training step {step}/{lora.steps}",
            }),
        }
        
        # Simulate training time
        await asyncio.sleep(0.5)
    
    # Mark training complete
    from datetime import datetime, timezone
    lora.status = LoraStatus.COMPLETED
    lora.completed_at = datetime.now(timezone.utc)
    lora.progress = 100
    lora.current_step = lora.steps
    lora.lora_url = f"https://storage.noisett.ai/loras/{lora.id}/weights.safetensors"
    
    yield {
        "event": "complete",
        "data": json.dumps({
            "lora_id": lora.id,
            "lora_url": lora.lora_url,
            "trigger_word": lora.trigger_word,
            "message": f"Training complete! Use trigger word '{lora.trigger_word}'",
        }),
    }


@app.get("/api/training/{lora_id}/events")
async def training_events(lora_id: str):
    """SSE endpoint for real-time LoRA training progress.

    Connect with EventSource to receive progress updates:
    - event: progress - Training step updates
    - event: complete - Training finished successfully
    - event: error - Training failed

    Part of the AFD Handoff Pattern for long-running operations.
    """
    return EventSourceResponse(training_event_generator(lora_id))


@app.post("/api/lora/{lora_id}/upload-url")
async def generate_upload_url(lora_id: str):
    """Generate Convex upload URL for LoRA training images.

    Returns a secure upload URL that clients can use to upload training images
    directly to Convex file storage. The URL is valid for a limited time.

    Args:
        lora_id: The LoRA ID to associate images with

    Returns:
        Upload URL and metadata for client upload
    """
    from src.commands.lora import LoraStatusInput, status

    try:
        # Verify LoRA exists and get its status
        input_data = LoraStatusInput(lora_id=lora_id)
        result = await status(input_data)

        if not result.success or not result.data:
            if result.error and result.error.code == "LORA_NOT_FOUND":
                raise HTTPException(status_code=404, detail=f"LoRA '{lora_id}' not found")
            else:
                raise HTTPException(status_code=400, detail=result.error.message if result.error else "Failed to get LoRA status")

        lora = result.data

        # Check if LoRA is in a valid state for image uploads
        valid_statuses = ["created", "uploading", "ready_to_train"]
        if lora.status.value not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot upload images to LoRA in status '{lora.status.value}'. Expected one of: {', '.join(valid_statuses)}"
            )

        # Check storage quota before generating upload URL
        convex = get_convex_client()

        try:
            storage_usage = await convex.get_storage_usage()
            usage_percent = storage_usage.get("usage_percent", 0)

            # Check if storage is nearly full (>90%)
            if usage_percent > 90:
                raise HTTPException(
                    status_code=507,  # Insufficient Storage
                    detail="Storage quota nearly full. Please delete old LoRAs to free up space."
                )

            # Warn if approaching quota (>75%)
            warning_message = None
            if usage_percent > 75:
                warning_message = f"Storage is {usage_percent}% full. Consider cleaning up old LoRAs soon."

        except Exception as e:
            # If quota check fails, log but continue (don't block uploads)
            print(f"Warning: Could not check storage quota: {e}")
            warning_message = "Could not check storage quota"

        # Generate upload URL from Convex
        upload_url = await convex.generate_upload_url()

        response_data = {
            "upload_url": upload_url,
            "lora_id": lora_id,
            "max_file_size_mb": 10,
            "allowed_formats": ["jpeg", "jpg", "png"],
            "min_dimensions": "512x512",
            "instructions": "Upload files directly to the provided URL using POST with the file as the request body"
        }

        if warning_message:
            response_data["warning"] = warning_message

        return {
            "success": True,
            "data": response_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


# --- History Endpoints (Phase 8) ---


@app.get("/api/history")
async def get_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """List generation history for the current user.
    
    Returns paginated list of past generations with images and metadata.
    """
    from src.commands.history import history_list, HistoryListInput
    from src.core.auth import get_anonymous_user_id
    
    # TODO: Get real user from auth when enabled
    user_id = get_anonymous_user_id()
    
    try:
        input_data = HistoryListInput(limit=limit, offset=offset)
        result = history_list(user_id=user_id, input_data=input_data)
        return result.model_dump(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{job_id}")
async def get_history_item(job_id: str):
    """Get details of a specific generation from history."""
    from src.commands.history import history_get, HistoryGetInput
    from src.core.auth import get_anonymous_user_id
    
    user_id = get_anonymous_user_id()
    
    try:
        input_data = HistoryGetInput(job_id=job_id)
        result = history_get(user_id=user_id, input_data=input_data)
        
        if not result.success and result.error:
            if result.error.get("code") == "HISTORY_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result.error.get("message"))
        
        return result.model_dump(exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history/{job_id}")
async def delete_history_item(job_id: str):
    """Delete a generation from history."""
    from src.commands.history import history_delete, HistoryDeleteInput
    from src.core.auth import get_anonymous_user_id
    
    user_id = get_anonymous_user_id()
    
    try:
        input_data = HistoryDeleteInput(job_id=job_id)
        result = history_delete(user_id=user_id, input_data=input_data)
        
        if not result.success and result.error:
            if result.error.get("code") == "HISTORY_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result.error.get("message"))
        
        return result.model_dump(exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Favorites Endpoints (Phase 8) ---


class FavoriteAddRequest(BaseModel):
    """Request body for adding a favorite."""
    
    job_id: str = Field(..., description="Job ID containing the image")
    image_index: int = Field(..., ge=0, description="Index of image in job results")
    image_url: str = Field(..., description="URL of the image")
    prompt: str | None = Field(default=None, description="Prompt that generated the image")


@app.get("/api/favorites")
async def get_favorites(
    limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """List favorite images for the current user."""
    from src.commands.favorites import favorites_list, FavoritesListInput
    from src.core.auth import get_anonymous_user_id
    
    user_id = get_anonymous_user_id()
    
    try:
        input_data = FavoritesListInput(limit=limit, offset=offset)
        result = favorites_list(user_id=user_id, input_data=input_data)
        return result.model_dump(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/favorites")
async def add_favorite(request: FavoriteAddRequest):
    """Add an image to favorites."""
    from src.commands.favorites import favorites_add, FavoritesAddInput
    from src.core.auth import get_anonymous_user_id
    
    user_id = get_anonymous_user_id()
    
    try:
        input_data = FavoritesAddInput(
            job_id=request.job_id,
            image_index=request.image_index,
            image_url=request.image_url,
            prompt=request.prompt,
        )
        result = favorites_add(user_id=user_id, input_data=input_data)
        
        if not result.success and result.error:
            if result.error.get("code") == "FAVORITE_ALREADY_EXISTS":
                raise HTTPException(status_code=409, detail=result.error.get("message"))
        
        return result.model_dump(exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/favorites/{job_id}/{image_index}")
async def remove_favorite(job_id: str, image_index: int):
    """Remove an image from favorites."""
    from src.commands.favorites import favorites_remove, FavoritesRemoveInput
    from src.core.auth import get_anonymous_user_id
    
    user_id = get_anonymous_user_id()
    
    try:
        input_data = FavoritesRemoveInput(job_id=job_id, image_index=image_index)
        result = favorites_remove(user_id=user_id, input_data=input_data)
        
        if not result.success and result.error:
            if result.error.get("code") == "FAVORITE_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result.error.get("message"))
        
        return result.model_dump(exclude_none=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
