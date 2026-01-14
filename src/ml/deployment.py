"""LoRA deployment integration with Fireworks API.

This module handles:
- Deploying trained LoRA weights to Fireworks
- Managing deployment timeouts and retries
- Validating deployment status
"""

import asyncio
import os
import time
from typing import Optional

import httpx


DEPLOYMENT_TIMEOUT = 600  # 10 minutes


async def deploy_to_fireworks(lora_url: str, lora_name: str) -> str:
    """Upload trained LoRA to Fireworks AI with timeout handling.

    Args:
        lora_url: URL of the trained LoRA weights (.safetensors)
        lora_name: Human-readable name for the LoRA model

    Returns:
        Fireworks model ID

    Raises:
        ValueError: If required environment variables missing or API fails
        TimeoutError: If deployment takes too long
    """
    api_key = os.getenv("FIREWORKS_API_KEY")
    account_id = os.getenv("FIREWORKS_ACCOUNT_ID")

    if not api_key:
        raise ValueError("FIREWORKS_API_KEY environment variable is required")
    if not account_id:
        raise ValueError("FIREWORKS_ACCOUNT_ID environment variable is required")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Download weights
        weights_response = await client.get(lora_url)
        if weights_response.status_code != 200:
            raise ValueError(f"Failed to download LoRA weights: {weights_response.status_code}")

        weights_data = weights_response.content

        # Create model
        create_url = f"https://api.fireworks.ai/inference/v1/accounts/{account_id}/models"
        create_headers = {"Authorization": f"Bearer {api_key}"}

        create_response = await client.post(
            create_url,
            headers=create_headers,
            json={
                "name": lora_name.replace(" ", "-").lower(),  # Sanitize name
                "settings": {
                    "baseModel": "accounts/fireworks/models/flux-1-dev-fp8"
                }
            }
        )

        if create_response.status_code not in [200, 201]:
            raise ValueError(f"Failed to create Fireworks model: {create_response.status_code} {create_response.text}")

        model_id = create_response.json()["name"]

        # Get upload endpoint
        upload_url = f"https://api.fireworks.ai/inference/v1/accounts/{account_id}/models/{model_id}/versions"
        upload_response = await client.post(
            upload_url,
            headers=create_headers,
            json={
                "baseModel": "accounts/fireworks/models/flux-1-dev-fp8",
                "files": {
                    "adapter_model.safetensors": len(weights_data)
                }
            }
        )

        if upload_response.status_code not in [200, 201]:
            raise ValueError(f"Failed to get upload endpoint: {upload_response.status_code} {upload_response.text}")

        upload_data = upload_response.json()
        version_id = upload_data["name"]
        signed_url = upload_data["uploadUrls"]["adapter_model.safetensors"]

        # Upload weights to signed URL
        upload_weights_response = await client.put(signed_url, content=weights_data)
        if upload_weights_response.status_code not in [200, 201]:
            raise ValueError(f"Failed to upload weights: {upload_weights_response.status_code}")

        # Validate upload
        validate_url = f"https://api.fireworks.ai/inference/v1/accounts/{account_id}/models/{model_id}/versions/{version_id}:validateUpload"
        validate_response = await client.post(validate_url, headers=create_headers)

        if validate_response.status_code not in [200, 201]:
            raise ValueError(f"Failed to validate upload: {validate_response.status_code}")

        # Wait for deployment to complete with timeout
        start_time = time.time()
        status_url = f"https://api.fireworks.ai/inference/v1/accounts/{account_id}/models/{model_id}/versions/{version_id}"

        while True:
            if time.time() - start_time > DEPLOYMENT_TIMEOUT:
                raise TimeoutError(f"Fireworks deployment timed out after {DEPLOYMENT_TIMEOUT} seconds")

            status_response = await client.get(status_url, headers=create_headers)
            if status_response.status_code != 200:
                raise ValueError(f"Failed to check deployment status: {status_response.status_code}")

            status_data = status_response.json()
            state = status_data.get("state", "UNKNOWN")

            if state == "READY":
                # Return the full model version ID for inference
                return f"accounts/{account_id}/models/{model_id}/versions/{version_id}"
            elif state == "FAILED":
                error_msg = status_data.get("error", "Unknown deployment error")
                raise ValueError(f"Fireworks deployment failed: {error_msg}")

            # Wait before checking again
            await asyncio.sleep(10)


async def check_fireworks_model_status(model_id: str) -> str:
    """Check the status of a Fireworks model.

    Args:
        model_id: Full Fireworks model ID

    Returns:
        Model state (READY, FAILED, DEPLOYING, etc.)

    Raises:
        ValueError: If API call fails
    """
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY environment variable is required")

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {api_key}"}

        response = await client.get(
            f"https://api.fireworks.ai/inference/v1/{model_id}",
            headers=headers
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to check model status: {response.status_code} {response.text}")

        return response.json().get("state", "UNKNOWN")