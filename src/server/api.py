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
import hashlib
import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # Load .env file

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.core.types import AssetType, ModelId, QualityPreset, JobStatus
from src.core.convex_client import get_convex_client

# Configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# --- Request/Response Models ---


class GenerateRequest(BaseModel):
    """Request body for image generation."""

    prompt: str = Field(..., min_length=1, max_length=500, description="Image description")
    asset_type: str = Field(default="product", description="Type of asset to generate")
    model: str = Field(default="hidream", description="Model to use")
    quality: str = Field(default="standard", description="Quality preset")
    count: int = Field(default=1, ge=1, le=4, description="Number of variations")
    lora: str | None = Field(default=None, description="LoRA ID to use for styled generation")


class CancelRequest(BaseModel):
    """Request body for job cancellation."""
    
    reason: str | None = Field(default=None, description="Cancellation reason")


# --- Background Task for Job Processing ---


async def process_job(job_id: str):
    """Process a job in the background using the configured ML backend."""
    from src.commands.asset import get_job, update_job
    from src.core.types import JobStatus
    
    # File-based debug logging (stdout may not work in background tasks)
    def debug_log(msg):
        import datetime
        with open("debug_process_job.log", "a") as f:
            f.write(f"[{datetime.datetime.now()}] {msg}\n")
        print(msg)  # Also try stdout
    
    debug_log(f"[PROCESS_JOB] Starting job {job_id}")
    debug_log(f"[PROCESS_JOB] ML_BACKEND: {os.environ.get('ML_BACKEND', 'mock')}")
    debug_log(f"[PROCESS_JOB] REPLICATE_API_TOKEN set: {bool(os.environ.get('REPLICATE_API_TOKEN'))}")
    
    # Get the job
    job = get_job(job_id)
    if not job or job.status != JobStatus.QUEUED:
        debug_log(f"[PROCESS_JOB] Job not found or not queued, exiting")
        return
    
    debug_log(f"[PROCESS_JOB] Job found: {job.prompt}")
    
    # Update to processing
    job.status = JobStatus.PROCESSING
    job.progress = 0.1
    update_job(job)
    
    try:
        # Handle LoRA generation with Fireworks/Replicate fallback
        if job.lora_id:
            # Get LoRA information from Convex
            from src.core.convex_client import get_convex_client

            convex = get_convex_client()
            convex_lora = await convex.get_lora(job.lora_id)

            if not convex_lora:
                raise ValueError(f"LoRA '{job.lora_id}' not found")

            fireworks_model_id = convex_lora.get("fireworksModelId")
            lora_url = convex_lora.get("loraUrl")

            # Try Fireworks first if deployed
            if fireworks_model_id and convex_lora.get("status") == "deployed":
                try:
                    from src.ml import FireworksGenerator
                    generator = FireworksGenerator()

                    # Update progress
                    job.progress = 0.3
                    update_job(job)

                    # Generate with Fireworks LoRA
                    images = await generator.generate_with_lora(
                        prompt=job.prompt,
                        asset_type=job.asset_type,
                        model=job.model,
                        quality=job.quality,
                        count=job.count,
                        lora_model_id=fireworks_model_id,
                    )

                except Exception as fireworks_error:
                    # Fallback to Replicate if Fireworks fails and lora_url is available
                    if lora_url:
                        from src.ml import ReplicateGenerator
                        generator = ReplicateGenerator()

                        # Update progress
                        job.progress = 0.3
                        update_job(job)

                        # Generate with Replicate LoRA inference
                        images = await generator.generate_with_lora(
                            prompt=job.prompt,
                            asset_type=job.asset_type,
                            model=job.model,
                            quality=job.quality,
                            count=job.count,
                            lora_url=lora_url,
                        )
                    else:
                        raise ValueError(f"Fireworks LoRA inference failed and no Replicate fallback available: {fireworks_error}")

            elif lora_url:
                # Use Replicate directly if no Fireworks deployment
                from src.ml import ReplicateGenerator
                generator = ReplicateGenerator()

                # Update progress
                job.progress = 0.3
                update_job(job)

                # Generate with Replicate LoRA inference
                images = await generator.generate_with_lora(
                    prompt=job.prompt,
                    asset_type=job.asset_type,
                    model=job.model,
                    quality=job.quality,
                    count=job.count,
                    lora_url=lora_url,
                )
            else:
                raise ValueError("LoRA is not ready for inference - no Fireworks deployment or Replicate URL available")

        else:
            # Regular generation without LoRA
            # Get the appropriate generator based on ML_BACKEND env var
            backend = os.environ.get("ML_BACKEND", "mock")
            print(f"[DEBUG] ML_BACKEND selected: '{backend}'")

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


# --- Debug: Direct Replicate Test ---


@app.get("/api/test-replicate")
async def test_replicate():
    """Direct Replicate API test to debug the 422 error.
    
    This bypasses all job processing to isolate the Replicate call.
    Only available when DEBUG=true environment variable is set.
    """
    # SECURITY: Only allow in debug mode to prevent production abuse
    if not DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    import replicate
    
    try:
        # Log what we're doing
        token = os.environ.get("REPLICATE_API_TOKEN", "NOT SET")
        print(f"[TEST] Token: {token[:10]}... (hidden)")
        print(f"[TEST] Calling black-forest-labs/flux-dev-lora...")
        
        output = await replicate.async_run(
            "black-forest-labs/flux-dev-lora",
            input={
                "prompt": "a simple laptop illustration",
                "go_fast": True,
                "guidance": 3,
                "megapixels": "1",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "webp",
                "output_quality": 80,
                "num_inference_steps": 20,
            },
        )
        
        # Parse output
        if isinstance(output, list) and len(output) > 0:
            item = output[0]
            url = item.url if hasattr(item, 'url') else str(item)
        else:
            url = str(output)
            
        return {
            "success": True,
            "data": {"url": url},
            "reasoning": "Direct Replicate test succeeded!",
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[TEST] Error: {error_details}")
        return {
            "success": False,
            "error": {
                "message": str(e),
                "details": error_details,
            },
            "reasoning": "Direct Replicate test failed",
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
            lora=request.lora,
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


# --- LoRA Management Endpoints ---


class LoraCreateRequest(BaseModel):
    """Request body for LoRA creation."""
    name: str = Field(..., min_length=1, max_length=100)
    trigger_word: str = Field(..., min_length=1, max_length=50)
    base_model: str = Field(default="flux")
    steps: int = Field(default=1000, ge=100, le=5000)


@app.get("/api/loras")
async def list_loras():
    """List all LoRAs from Convex."""
    try:
        convex = get_convex_client()
        loras = await convex.list_loras()
        return {"success": True, "data": loras}
    except Exception as e:
        logging.error(f"Failed to list LoRAs: {e}")
        return {"success": True, "data": []}  # Return empty on error


@app.post("/api/loras")
async def create_lora(request: LoraCreateRequest):
    """Create a new LoRA in Convex."""
    try:
        convex = get_convex_client()
        lora_data = {
            "name": request.name,
            "triggerWord": request.trigger_word,
            "baseModel": request.base_model,
            "steps": request.steps,
            "status": "created",
            "isActive": False,
            "createdAt": int(time.time() * 1000),  # JS timestamp
        }
        result = await convex.create_lora(lora_data)
        return {"success": True, "data": {"id": result}}
    except Exception as e:
        logging.error(f"Failed to create LoRA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/loras/{lora_id}")
async def get_lora(lora_id: str):
    """Get a specific LoRA by ID."""
    try:
        convex = get_convex_client()
        lora = await convex.get_lora(lora_id)
        if not lora:
            raise HTTPException(status_code=404, detail="LoRA not found")
        return {"success": True, "data": lora}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to get LoRA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/loras/{lora_id}")
async def delete_lora_endpoint(lora_id: str):
    """Delete a LoRA from Convex."""
    try:
        convex = get_convex_client()
        await convex.delete_lora(lora_id)
        return {"success": True}
    except Exception as e:
        logging.error(f"Failed to delete LoRA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Upload Endpoints ---


@app.post("/api/lora/{lora_id}/upload-url")
async def get_upload_url(lora_id: str):
    """Generate a Convex storage upload URL for training images."""
    try:
        convex = get_convex_client()
        
        # Verify LoRA exists
        lora = await convex.get_lora(lora_id)
        if not lora:
            raise HTTPException(status_code=404, detail=f"LoRA '{lora_id}' not found")
        
        # Generate upload URL
        upload_url = await convex.generate_upload_url()
        return {
            "success": True,
            "data": {
                "uploadUrl": upload_url,
                "loraId": lora_id,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TrainingImageRequest(BaseModel):
    lora_id: str = Field(..., description="LoRA ID")
    storage_id: str = Field(..., description="Convex storage ID from upload")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(default="image/png", description="MIME type")
    file_size: int = Field(default=0, description="File size in bytes")


@app.post("/api/training-images")
async def create_training_image(request: TrainingImageRequest):
    """Register a training image after upload to Convex storage."""
    try:
        convex = get_convex_client()
        
        # Create training image record - match Convex schema field names
        import time
        image_id = await convex.create_training_image({
            "loraId": request.lora_id,
            "storageId": request.storage_id,
            "filename": request.filename,
            "sizeBytes": float(request.file_size),  # Convex expects sizeBytes, not fileSize
            "uploadedAt": float(time.time() * 1000),  # Convex expects uploadedAt timestamp
        })
        
        # Get current image count (don't try to update LoRA - no imageCount field)
        count = await convex.count_training_images_by_lora(request.lora_id)
        
        return {
            "success": True,
            "data": {
                "id": image_id,
                "loraId": request.lora_id,
                "imageCount": count,
            }
        }
    except Exception as e:
        logging.error(f"Failed to create training image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lora/{lora_id}/training-images")
async def list_training_images(lora_id: str):
    """List training images for a LoRA with resolved storage URLs."""
    try:
        convex = get_convex_client()
        images = await convex.list_training_images_by_lora(lora_id)
        
        # Resolve storage URLs for each image
        for img in images:
            if img.get("storageId"):
                try:
                    url_data = await convex.get_storage_url(img["storageId"])
                    img["url"] = url_data
                except Exception as e:
                    logging.warning(f"Failed to get URL for {img.get('filename')}: {e}")
                    img["url"] = None
        
        return {"success": True, "data": images}
    except Exception as e:
        logging.error(f"Failed to list training images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        content_type = "image/jpeg"
    elif filename.endswith(".svg"):
        content_type = "image/svg+xml"
    else:
        content_type = "image/png"
    
    return FileResponse(image_path, media_type=content_type)


# --- Training SSE Endpoints (AFD Handoff Pattern) ---


from sse_starlette.sse import EventSourceResponse


async def training_event_generator(lora_id: str, last_event_id: int = 0):
    """Generate SSE events for LoRA training progress reading from Convex.

    Yields events in format:
        event: progress
        data: {"step": 100, "total": 1000, "percent": 10, "message": "..."}

        event: complete
        data: {"lora_id": "...", "lora_url": "..."}

        event: error
        data: {"code": "...", "message": "..."}
    """
    from src.core.types import LoraStatus
    import json

    convex = get_convex_client()
    event_counter = last_event_id
    last_status = None
    last_progress = None

    try:
        # Get initial LoRA state
        convex_lora = await convex.get_lora(lora_id)
        if not convex_lora:
            yield {
                "id": str(event_counter + 1),
                "event": "error",
                "data": json.dumps({"code": "LORA_NOT_FOUND", "message": f"LoRA '{lora_id}' not found"}),
            }
            return

        # Send initial status
        event_counter += 1
        yield {
            "id": str(event_counter),
            "event": "status",
            "data": json.dumps({
                "lora_id": lora_id,
                "status": convex_lora["status"],
                "progress": convex_lora.get("progress", 0),
                "current_step": convex_lora.get("currentStep", 0),
                "steps": convex_lora["steps"],
                "message": f"Current status: {convex_lora['status']}"
            }),
        }

        # Poll for updates
        while True:
            try:
                # Get current LoRA state
                current_lora = await convex.get_lora(lora_id)
                if not current_lora:
                    break

                current_status = current_lora["status"]
                current_progress = current_lora.get("progress", 0)
                current_step = current_lora.get("currentStep", 0)
                total_steps = current_lora["steps"]

                # Check if status changed
                if current_status != last_status:
                    event_counter += 1
                    if current_status == "training":
                        yield {
                            "id": str(event_counter),
                            "event": "training_started",
                            "data": json.dumps({
                                "lora_id": lora_id,
                                "status": current_status,
                                "message": "Training started on Replicate",
                            }),
                        }
                    elif current_status == "failed":
                        yield {
                            "id": str(event_counter),
                            "event": "error",
                            "data": json.dumps({
                                "code": current_lora.get("errorCode", "TRAINING_FAILED"),
                                "message": current_lora.get("errorMessage", "Training failed"),
                            }),
                        }
                        break
                    elif current_status in ["completed", "deployment_pending"]:
                        yield {
                            "id": str(event_counter),
                            "event": "training_complete",
                            "data": json.dumps({
                                "lora_id": lora_id,
                                "status": current_status,
                                "lora_url": current_lora.get("loraUrl"),
                                "message": "Training completed! Deploying to Fireworks...",
                            }),
                        }
                    elif current_status == "deployed":
                        yield {
                            "id": str(event_counter),
                            "event": "complete",
                            "data": json.dumps({
                                "lora_id": lora_id,
                                "status": current_status,
                                "lora_url": current_lora.get("loraUrl"),
                                "fireworks_model_id": current_lora.get("fireworksModelId"),
                                "trigger_word": current_lora["triggerWord"],
                                "message": f"LoRA ready! Use trigger word '{current_lora['triggerWord']}' in generation",
                            }),
                        }
                        break
                    elif current_status == "deployment_failed":
                        yield {
                            "id": str(event_counter),
                            "event": "deployment_error",
                            "data": json.dumps({
                                "code": current_lora.get("errorCode", "DEPLOYMENT_FAILED"),
                                "message": current_lora.get("errorMessage", "Deployment failed"),
                                "lora_url": current_lora.get("loraUrl"),
                                "suggestion": "Try lora.deploy to retry deployment",
                            }),
                        }
                        break

                # Check if progress changed
                elif current_progress != last_progress and current_status == "training":
                    event_counter += 1
                    yield {
                        "id": str(event_counter),
                        "event": "progress",
                        "data": json.dumps({
                            "step": current_step,
                            "total": total_steps,
                            "percent": current_progress,
                            "message": f"Training step {current_step}/{total_steps}",
                        }),
                    }

                last_status = current_status
                last_progress = current_progress

                # Exit if training is complete or failed
                if current_status in ["completed", "failed", "deployed", "deployment_failed"]:
                    break

                # Poll every 5 seconds
                await asyncio.sleep(5)

            except Exception as e:
                logging.error(f"Error in SSE generator for LoRA {lora_id}: {e}")
                event_counter += 1
                yield {
                    "id": str(event_counter),
                    "event": "error",
                    "data": json.dumps({
                        "code": "SSE_ERROR",
                        "message": f"Connection error: {str(e)}",
                    }),
                }
                break

    except Exception as e:
        event_counter += 1
        yield {
            "id": str(event_counter),
            "event": "error",
            "data": json.dumps({
                "code": "LORA_ERROR",
                "message": f"Failed to get LoRA status: {str(e)}",
            }),
        }


@app.get("/api/training/{lora_id}/events")
async def training_events(lora_id: str, lastEventId: int = Query(default=0, description="Last event ID for reconnection")):
    """SSE endpoint for real-time LoRA training progress with reconnection support.

    Connect with EventSource to receive progress updates:
    - event: status - Initial/current status
    - event: training_started - Training began
    - event: progress - Training step updates
    - event: training_complete - Training finished, deployment starting
    - event: complete - Training and deployment finished successfully
    - event: error - Training failed
    - event: deployment_error - Deployment failed

    Supports reconnection via ?lastEventId=X parameter.
    Part of the AFD Handoff Pattern for long-running operations.
    """
    return EventSourceResponse(training_event_generator(lora_id, last_event_id=lastEventId))


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


# --- Webhook Endpoints ---


async def deploy_with_error_handling(lora_id: str, url: str, name: str):
    """Deploy LoRA to Fireworks with retry and error tracking."""
    from src.ml.deployment import deploy_to_fireworks

    convex = get_convex_client()
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            model_id = await deploy_to_fireworks(url, name)
            await convex.update_lora(lora_id, {
                "status": "deployed",
                "fireworksModelId": model_id,
            })
            logging.info(f"LoRA {lora_id} deployed successfully to Fireworks: {model_id}")
            return
        except Exception as e:
            logging.error(f"Deployment attempt {attempt+1} failed for LoRA {lora_id}: {e}")
            if attempt == max_attempts - 1:
                await convex.update_lora(lora_id, {
                    "status": "deployment_failed",
                    "errorMessage": str(e),
                    "errorCode": "FIREWORKS_DEPLOYMENT_FAILED",
                })
            else:
                await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff


@app.post("/api/webhooks/replicate/training")
async def replicate_training_webhook(request: Request):
    """Handle Replicate training webhooks with signature verification."""

    # Get webhook secret
    webhook_secret = os.getenv("REPLICATE_WEBHOOK_SECRET")
    if not webhook_secret:
        logging.error("REPLICATE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # Verify webhook signature
    signature = request.headers.get("Webhook-Signature", "")
    body = await request.body()

    expected = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(f"sha256={expected}", signature):
        logging.warning(f"Invalid webhook signature from {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    training_id = payload.get("id")
    if not training_id:
        raise HTTPException(status_code=400, detail="Missing training ID in payload")

    convex = get_convex_client()

    # Idempotency check
    existing_event = await convex.get_webhook_event_by_id(training_id)
    if existing_event:
        return {"ok": True, "skipped": True, "reason": "already_processed"}

    # Record event before processing
    await convex.create_webhook_event({
        "eventId": training_id,
        "processedAt": int(time.time() * 1000),
        "eventType": payload.get("status", "unknown"),
    })

    # Find LoRA
    lora = await convex.get_lora_by_replicate_id(training_id)
    if not lora:
        logging.error(f"LoRA not found for training {training_id}")
        return {"ok": False, "error": "lora_not_found"}

    lora_id = lora["_id"]
    status = payload.get("status")

    if status == "succeeded":
        output_url = payload.get("output", {}).get("weights") if payload.get("output") else None
        if not output_url:
            logging.error(f"No weights URL in successful training {training_id}")
            await convex.update_lora(lora_id, {
                "status": "failed",
                "errorMessage": "Training completed but no weights URL provided",
                "errorCode": "MISSING_WEIGHTS_URL",
            })
        else:
            # Set intermediate status
            await convex.update_lora(lora_id, {
                "status": "deployment_pending",
                "loraUrl": output_url,
                "completedAt": int(time.time() * 1000),
                "progress": 100,
                "currentStep": lora.get("steps", 1000),
            })

            # Trigger async deployment
            asyncio.create_task(
                deploy_with_error_handling(lora_id, output_url, lora["name"])
            )

    elif status == "failed":
        error_message = payload.get("error", "Training failed")
        await convex.update_lora(lora_id, {
            "status": "failed",
            "errorMessage": error_message,
            "errorCode": "REPLICATE_TRAINING_FAILED",
        })

    elif status == "processing":
        # Update progress if provided
        logs = payload.get("logs", "")
        progress_info = extract_progress_from_logs(logs)
        if progress_info:
            await convex.update_lora(lora_id, progress_info)

    return {"ok": True}


def extract_progress_from_logs(logs: str) -> dict:
    """Extract progress information from Replicate training logs."""
    if not logs:
        return {}

    # Try to extract step information from logs
    # Replicate LoRA training typically outputs: "Step 123/1000"
    import re
    step_match = re.search(r"Step (\d+)/(\d+)", logs)
    if step_match:
        current_step = int(step_match.group(1))
        total_steps = int(step_match.group(2))
        progress = int((current_step / total_steps) * 100)

        return {
            "currentStep": current_step,
            "progress": progress,
        }

    return {}


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
