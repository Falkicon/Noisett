"""Convex HTTP client for Noisett.

Provides async HTTP client for interacting with Convex HTTP Actions.
Includes rate limiting and exponential backoff for reliability.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel


class ConvexError(Exception):
    """Base exception for Convex client errors."""
    pass


class ConvexRateLimitError(ConvexError):
    """Raised when Convex rate limits are exceeded."""
    pass


class ConvexClient:
    """HTTP client for Convex backend operations.

    Handles LoRA CRUD operations, webhook events, and storage operations
    through Convex HTTP Actions with built-in retry and rate limiting.
    """

    def __init__(self, deployment_url: Optional[str] = None):
        """Initialize Convex client.

        Args:
            deployment_url: Convex deployment URL. If None, reads from CONVEX_URL env var.
        """
        self.deployment_url = deployment_url or os.getenv("CONVEX_URL")
        if not self.deployment_url:
            raise ValueError("CONVEX_URL environment variable is required")

        # HTTP actions use .convex.site, not .convex.cloud
        self.base_url = self.deployment_url.rstrip("/").replace(".convex.cloud", ".convex.site")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Any:
        """Make HTTP request with rate limiting and retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: JSON data for POST requests
            params: URL parameters for GET requests
            max_retries: Maximum number of retry attempts

        Returns:
            Response data as dict

        Raises:
            ConvexError: On non-retryable errors
            ConvexRateLimitError: On persistent rate limiting
        """
        # Rate limiting
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)

        self._last_request_time = time.time()

        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries + 1):
            try:
                if method == "GET":
                    response = await self._client.get(url, params=params or {})
                elif method == "POST":
                    response = await self._client.post(url, json=data or {})
                elif method == "DELETE":
                    response = await self._client.delete(url, params=params or {})
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle rate limiting
                if response.status_code == 429:
                    if attempt == max_retries:
                        raise ConvexRateLimitError("Persistent rate limiting from Convex")

                    # Exponential backoff
                    wait_time = (2 ** attempt) * 1.0  # 1s, 2s, 4s
                    await asyncio.sleep(wait_time)
                    continue

                # Handle other errors
                if not response.is_success:
                    error_text = response.text
                    raise ConvexError(
                        f"Convex request failed: {response.status_code} {error_text}"
                    )

                return response.json()

            except httpx.RequestError as e:
                if attempt == max_retries:
                    raise ConvexError(f"HTTP request failed: {e}")

                # Exponential backoff for network errors
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                await asyncio.sleep(wait_time)

        raise ConvexError("Max retries exceeded")

    # LoRA operations

    async def create_lora(self, lora_data: Dict[str, Any]) -> str:
        """Create a new LoRA.

        Args:
            lora_data: LoRA fields matching Convex schema

        Returns:
            Created LoRA ID
        """
        result = await self._make_request("POST", "/api/loras/create", data=lora_data)
        return result["id"]

    async def get_lora(self, lora_id: str) -> Optional[Dict[str, Any]]:
        """Get LoRA by ID.

        Args:
            lora_id: LoRA ID

        Returns:
            LoRA data or None if not found
        """
        result = await self._make_request("GET", "/api/loras/get", params={"id": lora_id})
        return result

    async def get_asset_type(self, asset_type_id: str) -> Optional[Dict[str, Any]]:
        """Get Asset Type by ID.

        Args:
            asset_type_id: Asset Type ID

        Returns:
            Asset Type data or None if not found
        """
        result = await self._make_request("GET", "/api/asset-types/get", params={"id": asset_type_id})
        return result

    async def list_loras(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        base_model: Optional[str] = None,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List LoRAs with optional filters.

        Args:
            user_id: Filter by user ID
            status: Filter by status
            base_model: Filter by base model
            active_only: Only show active LoRAs

        Returns:
            List of LoRA data
        """
        params = {"activeOnly": str(active_only).lower()}
        if user_id:
            params["userId"] = user_id
        if status:
            params["status"] = status
        if base_model:
            params["baseModel"] = base_model

        result = await self._make_request("GET", "/api/loras/list", params=params)
        return result

    async def update_lora(self, lora_id: str, updates: Dict[str, Any]) -> None:
        """Update LoRA fields.

        Args:
            lora_id: LoRA ID
            updates: Fields to update
        """
        data = {"id": lora_id, **updates}
        await self._make_request("POST", "/api/loras/update", data=data)

    async def delete_lora(self, lora_id: str) -> None:
        """Delete LoRA by ID.

        Args:
            lora_id: LoRA ID to delete
        """
        await self._make_request("DELETE", "/api/loras/delete", params={"id": lora_id})

    async def get_lora_by_replicate_id(self, replicate_training_id: str) -> Optional[Dict[str, Any]]:
        """Get LoRA by Replicate training ID.

        Args:
            replicate_training_id: Replicate training ID

        Returns:
            LoRA data or None if not found
        """
        result = await self._make_request(
            "GET",
            "/api/loras/by-replicate-id",
            params={"replicateTrainingId": replicate_training_id}
        )
        return result

    async def get_lora_by_trigger_word(self, trigger_word: str) -> Optional[Dict[str, Any]]:
        """Get LoRA by trigger word.

        Args:
            trigger_word: Trigger word to search for

        Returns:
            LoRA data or None if not found
        """
        result = await self._make_request(
            "GET",
            "/api/loras/by-trigger-word",
            params={"triggerWord": trigger_word}
        )
        return result

    # Training images operations

    async def create_training_image(self, image_data: Dict[str, Any]) -> str:
        """Create a training image record.

        Args:
            image_data: Image fields (loraId, storageId, filename, etc.)

        Returns:
            Created training image ID
        """
        result = await self._make_request("POST", "/api/training-images/create", data=image_data)
        return result["id"]

    async def list_training_images_by_lora(self, lora_id: str) -> List[Dict[str, Any]]:
        """List training images for a LoRA.

        Args:
            lora_id: LoRA ID

        Returns:
            List of training image data
        """
        result = await self._make_request(
            "GET",
            "/api/training-images/list-by-lora",
            params={"loraId": lora_id}
        )
        return result

    async def count_training_images_by_lora(self, lora_id: str) -> int:
        """Count training images for a LoRA.

        Args:
            lora_id: LoRA ID

        Returns:
            Count of training images
        """
        result = await self._make_request(
            "GET",
            "/api/training-images/count-by-lora",
            params={"loraId": lora_id}
        )
        return result["count"]

    async def delete_training_image(self, image_id: str) -> None:
        """Delete a training image by ID.

        Args:
            image_id: Training image ID to delete
        """
        await self._make_request(
            "DELETE",
            "/api/training-images/delete",
            params={"id": image_id}
        )

    async def delete_training_images_by_lora(self, lora_id: str) -> None:
        """Delete all training images for a LoRA.

        Args:
            lora_id: LoRA ID
        """
        await self._make_request(
            "DELETE",
            "/api/training-images/delete-by-lora",
            params={"loraId": lora_id}
        )

    # Storage operations

    async def generate_upload_url(self) -> str:
        """Generate a Convex storage upload URL.

        Returns:
            Upload URL for file storage
        """
        result = await self._make_request("POST", "/api/storage/generate-upload-url")
        return result["uploadUrl"]

    async def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage information.

        Returns:
            Storage usage data with used_bytes, quota_bytes, usage_percent
        """
        result = await self._make_request("GET", "/api/storage/usage")
        return result

    async def get_storage_url(self, storage_id: str) -> Optional[str]:
        """Get download URL for a storage ID.

        Args:
            storage_id: Convex storage ID

        Returns:
            Signed download URL or None if not found
        """
        result = await self._make_request(
            "GET",
            "/api/storage/get-url",
            params={"storageId": storage_id}
        )
        return result.get("url")

    # Webhook event operations

    async def create_webhook_event(self, event_data: Dict[str, Any]) -> str:
        """Create webhook event record for idempotency.

        Args:
            event_data: Event fields (eventId, processedAt, eventType)

        Returns:
            Created event ID
        """
        result = await self._make_request("POST", "/api/webhook-events/create", data=event_data)
        return result["id"]

    async def get_webhook_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook event by event ID.

        Args:
            event_id: Event ID to search for

        Returns:
            Event data or None if not found
        """
        result = await self._make_request(
            "GET",
            "/api/webhook-events/by-event-id",
            params={"eventId": event_id}
        )
        return result


# Global client instance
_convex_client: Optional[ConvexClient] = None


def get_convex_client() -> ConvexClient:
    """Get global Convex client instance.

    Returns:
        ConvexClient instance
    """
    global _convex_client
    if _convex_client is None:
        _convex_client = ConvexClient()
    return _convex_client


async def close_convex_client():
    """Close global Convex client."""
    global _convex_client
    if _convex_client:
        await _convex_client.close()
        _convex_client = None