"""LoRA training integration with Replicate API.

This module handles:
- Exporting training images to zip format for Replicate
- Starting Replicate training jobs
- Progress tracking and deployment
"""

import asyncio
import json
import os
import tempfile
import time
import zipfile
from typing import Optional, Dict, Any

import httpx
import replicate

from src.core.convex_client import get_convex_client, ConvexError
from src.core.errors import ErrorCode
from afd.core import CommandResult, error


async def export_training_images_to_zip(lora_id: str) -> str:
    """Export Convex images to zip for Replicate training.

    Args:
        lora_id: The LoRA ID to export images for

    Returns:
        Public URL of the zip file stored in Convex

    Raises:
        ValueError: If no images found or validation fails
        ConvexError: If Convex operations fail
    """
    convex = get_convex_client()

    # Get training images
    images = await convex.list_training_images_by_lora(lora_id)

    # Validate image count
    if len(images) == 0:
        raise ValueError("Cannot train with 0 images. Upload at least 5 images.")

    if len(images) < 5:
        raise ValueError(f"Need at least 5 images for training, have {len(images)}.")

    # Use temp file to avoid OOM
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        try:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for i, img in enumerate(images):
                        # Get download URL from Convex storage
                        url = f"{convex.base_url}/api/storage/get-url?storageId={img['storageId']}"
                        response = await client.get(url)

                        if response.status_code != 200:
                            raise ValueError(f"Failed to download image {img['filename']}: {response.status_code}")

                        download_url = response.json().get("url")
                        if not download_url:
                            raise ValueError(f"No download URL for image {img['filename']}")

                        # Download image content
                        img_response = await client.get(download_url)
                        if img_response.status_code != 200:
                            raise ValueError(f"Failed to download image content for {img['filename']}")

                        # Extract file extension
                        ext = img["filename"].split(".")[-1].lower()
                        if ext not in ["jpg", "jpeg", "png"]:
                            ext = "jpg"  # Default extension

                        # Add image to zip
                        zf.writestr(f"image_{i:03d}.{ext}", img_response.content)

                        # Add caption if present
                        if img.get("caption"):
                            zf.writestr(f"image_{i:03d}.txt", img["caption"])

            # Upload zip to Convex storage
            upload_url = await convex.generate_upload_url()

            async with httpx.AsyncClient() as client:
                with open(tmp.name, 'rb') as f:
                    upload_response = await client.post(upload_url, content=f.read())

                if upload_response.status_code not in [200, 201]:
                    raise ValueError(f"Failed to upload zip to Convex: {upload_response.status_code}")

                storage_id = upload_response.json().get("storageId")
                if not storage_id:
                    raise ValueError("No storage ID returned from upload")

            # Get public URL
            public_url_response = await convex._make_request(
                "GET",
                "/api/storage/get-url",
                params={"storageId": storage_id}
            )
            return public_url_response.get("url")

        finally:
            # Cleanup temp file
            try:
                os.unlink(tmp.name)
            except OSError:
                pass  # Ignore cleanup errors


async def start_replicate_training(
    lora_id: str,
    zip_url: str,
    trigger_word: str,
    steps: int = 1000
) -> str:
    """Start a Replicate LoRA training job.

    Args:
        lora_id: The LoRA ID for tracking
        zip_url: URL of the training images zip file
        trigger_word: The trigger word for the LoRA
        steps: Number of training steps

    Returns:
        Replicate training ID

    Raises:
        ValueError: If required environment variables missing or API fails
    """
    # Support both REPLICATE_API_KEY and REPLICATE_API_TOKEN for flexibility
    api_token = os.getenv("REPLICATE_API_KEY") or os.getenv("REPLICATE_API_TOKEN")
    webhook_secret = os.getenv("REPLICATE_WEBHOOK_SECRET")
    webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io")

    if not api_token:
        raise ValueError("REPLICATE_API_KEY environment variable is required")

    # Use the fast-flux-trainer (faster than ostris/flux-dev-lora-trainer)
    # See: https://replicate.com/replicate/fast-flux-trainer/train
    training_model = "replicate/fast-flux-trainer"
    training_version = "8b10794665aed907bb98a1a5324cd1d3a8bea0e9b31e65210967fb9c9e2e08ed"
    
    # Get Replicate username for destination (required)
    replicate_owner = os.getenv("REPLICATE_OWNER")
    if not replicate_owner:
        raise ValueError("REPLICATE_OWNER environment variable is required")
    
    model_name = f"lora-{lora_id[:8]}"
    destination = f"{replicate_owner}/{model_name}"

    # Auto-create destination model if it doesn't exist
    try:
        await replicate.models.async_get(destination)
    except Exception:
        # Model doesn't exist, create it
        await replicate.models.async_create(
            owner=replicate_owner,
            name=model_name,
            visibility="private",
            hardware="gpu-t4",
            description=f"LoRA fine-tune with trigger word: {trigger_word}"
        )

    # Fast-flux-trainer uses simpler inputs
    input_data = {
        "input_images": zip_url,
        "trigger_word": trigger_word,
        "lora_type": "style",  # "subject" for faces/objects, "style" for art styles
        "steps": steps,
    }

    try:
        # Start training job - requires model, version, destination, and input
        if webhook_secret:
            webhook_url = f"{webhook_base_url}/api/webhooks/replicate/training"
            training = await replicate.trainings.async_create(
                model=training_model,
                version=training_version,
                destination=destination,
                input=input_data,
                webhook=webhook_url,
                webhook_events_filter=["start", "output", "logs", "completed"]
            )
        else:
            # No webhook - training will run but progress updates won't be pushed
            training = await replicate.trainings.async_create(
                model=training_model,
                version=training_version,
                destination=destination,
                input=input_data
            )

        return training.id

    except Exception as e:
        raise ValueError(f"Failed to start Replicate training: {e}")


async def estimate_training_cost(steps: int = 1000) -> Dict[str, Any]:
    """Estimate the cost and time for LoRA training.

    Args:
        steps: Number of training steps

    Returns:
        Dict with estimated_cost_usd, estimated_time_minutes, steps
    """
    # Replicate LoRA training costs approximately $0.002 per step
    cost_per_step = 0.002
    estimated_cost = steps * cost_per_step

    # Training time is approximately 20 minutes for 1000 steps
    time_per_step = 20 / 1000  # minutes per step
    estimated_time = int(steps * time_per_step)

    return {
        "estimated_cost_usd": round(estimated_cost, 2),
        "estimated_time_minutes": max(estimated_time, 10),  # Minimum 10 minutes
        "steps": steps
    }


async def cancel_replicate_training(replicate_training_id: str) -> bool:
    """Cancel a running Replicate training job.

    Args:
        replicate_training_id: The Replicate training ID

    Returns:
        True if cancelled successfully, False otherwise
    """
    try:
        training = await replicate.trainings.async_get(replicate_training_id)
        if training.status in ["starting", "processing"]:
            await replicate.trainings.async_cancel(replicate_training_id)
            return True
        return False
    except Exception:
        return False


async def cleanup_orphaned_trainings(max_age_hours: int = 24) -> int:
    """Clean up LoRAs stuck in uploading state for too long.

    Args:
        max_age_hours: Maximum age in hours before cleanup

    Returns:
        Number of LoRAs cleaned up
    """
    convex = get_convex_client()
    cutoff_time = int((time.time() - max_age_hours * 3600) * 1000)

    try:
        # Get LoRAs stuck in uploading state
        uploading_loras = await convex.list_loras(status="uploading")

        cleanup_count = 0
        for lora in uploading_loras:
            if lora.get("createdAt", 0) < cutoff_time:
                # Mark as failed due to timeout
                await convex.update_lora(lora["_id"], {
                    "status": "failed",
                    "errorMessage": f"Upload timed out after {max_age_hours} hours",
                    "errorCode": "UPLOAD_TIMEOUT"
                })
                cleanup_count += 1

        return cleanup_count

    except ConvexError:
        return 0