"""ML Pipeline - Image generation backends.

Supports multiple backends:
- mock: Returns placeholder images (for testing)
- replicate: Uses Replicate API (has HiDream, FLUX)
- local: Local diffusers pipeline (requires GPU)
"""

import os
from abc import ABC, abstractmethod
from typing import List

from src.core.types import AssetType, GeneratedImage, ModelId, QualityPreset


class ImageGenerator(ABC):
    """Abstract base class for image generators."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: ModelId,
        quality: QualityPreset,
        count: int,
    ) -> List[GeneratedImage]:
        """Generate images from a prompt."""
        pass


class MockGenerator(ImageGenerator):
    """Mock generator that returns placeholder images for testing."""

    # Placeholder image URLs (1024x1024 colored squares)
    PLACEHOLDER_URLS = [
        "https://placehold.co/1024x1024/107C10/white?text=Generated+1",
        "https://placehold.co/1024x1024/0078D4/white?text=Generated+2",
        "https://placehold.co/1024x1024/5C2D91/white?text=Generated+3",
        "https://placehold.co/1024x1024/D83B01/white?text=Generated+4",
    ]

    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: ModelId,
        quality: QualityPreset,
        count: int,
    ) -> List[GeneratedImage]:
        """Return placeholder images instantly."""
        import random

        images = []
        for i in range(count):
            seed = random.randint(1, 999999)
            images.append(
                GeneratedImage(
                    index=i,
                    url=self.PLACEHOLDER_URLS[i % len(self.PLACEHOLDER_URLS)],
                    width=1024,
                    height=1024,
                    seed=seed,
                )
            )
        return images


class HuggingFaceGenerator(ImageGenerator):
    """Generator using Hugging Face Inference API (free tier available)."""

    # Model mappings to HF model IDs
    MODEL_IDS = {
        ModelId.FLUX: "black-forest-labs/FLUX.1-schnell",  # Fast, 4-step
        ModelId.SD35: "stabilityai/stable-diffusion-3.5-large",
    }

    def __init__(self):
        self.api_token = os.environ.get("HF_TOKEN")
        if not self.api_token:
            raise ValueError(
                "HF_TOKEN environment variable not set.\n"
                "Get your FREE token at: https://huggingface.co/settings/tokens\n"
                "Then run: $env:HF_TOKEN='your_token_here'"
            )
        
    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: ModelId,
        quality: QualityPreset,
        count: int,
    ) -> List[GeneratedImage]:
        """Generate images using Hugging Face Inference API."""
        import httpx
        import base64
        import tempfile
        from pathlib import Path
        
        # Get model ID
        model_id = self.MODEL_IDS.get(model, self.MODEL_IDS[ModelId.FLUX])
        
        # Build enhanced prompt based on asset type
        from src.core.types import ASSET_TYPE_CONFIGS
        asset_config = ASSET_TYPE_CONFIGS[asset_type]
        enhanced_prompt = asset_config.prompt_template.replace("{subject}", prompt)
        
        # API endpoint (updated Dec 2025)
        api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        images = []
        output_dir = Path(tempfile.gettempdir()) / "noisett"
        output_dir.mkdir(exist_ok=True)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            for i in range(count):
                print(f"  Generating image {i + 1}/{count}...")
                
                response = await client.post(
                    api_url,
                    headers=headers,
                    json={"inputs": enhanced_prompt},
                )
                
                if response.status_code == 503:
                    # Model is loading, wait and retry
                    import asyncio
                    print("  Model is loading, waiting 20s...")
                    await asyncio.sleep(20)
                    response = await client.post(
                        api_url,
                        headers=headers,
                        json={"inputs": enhanced_prompt},
                    )
                
                if response.status_code != 200:
                    raise ValueError(f"HF API error: {response.status_code} - {response.text}")
                
                # Save image to temp file
                image_path = output_dir / f"generated_{i}.png"
                image_path.write_bytes(response.content)
                
                images.append(
                    GeneratedImage(
                        index=i,
                        url=f"file://{image_path}",
                        width=1024,
                        height=1024,
                    )
                )
        
        return images


class ReplicateGenerator(ImageGenerator):
    """Generator using Replicate API (supports HiDream, FLUX, SD3.5)."""

    # Model mappings to Replicate model versions
    MODEL_VERSIONS = {
        ModelId.HIDREAM: "mcai/hidream-i1-full:50c0e2241017e6713ab94a5f984e6b1e9646dc95ef0d60e7a3045017e7d1e33c",
        ModelId.FLUX: "black-forest-labs/flux-1.1-pro",
        ModelId.SD35: "stability-ai/stable-diffusion-3.5-large",
    }

    def __init__(self):
        self.api_token = os.environ.get("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "REPLICATE_API_TOKEN environment variable not set. "
                "Get your token at https://replicate.com/account/api-tokens"
            )

    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: ModelId,
        quality: QualityPreset,
        count: int,
    ) -> List[GeneratedImage]:
        """Generate images using Replicate API."""
        import replicate

        # Get model version
        model_version = self.MODEL_VERSIONS.get(model)
        if not model_version:
            raise ValueError(f"Model {model} not supported on Replicate")

        # Build enhanced prompt based on asset type
        from src.core.types import ASSET_TYPE_CONFIGS

        asset_config = ASSET_TYPE_CONFIGS[asset_type]
        enhanced_prompt = asset_config.prompt_template.replace("{subject}", prompt)

        # Quality to steps mapping
        steps_map = {"draft": 20, "standard": 28, "high": 50}
        num_steps = steps_map.get(quality.value, 28)

        images = []
        for i in range(count):
            # Run prediction
            output = await replicate.async_run(
                model_version,
                input={
                    "prompt": enhanced_prompt,
                    "negative_prompt": asset_config.negative_prompt,
                    "num_inference_steps": num_steps,
                    "width": 1024,
                    "height": 1024,
                },
            )

            # Handle different output formats
            if isinstance(output, list):
                url = output[0] if output else None
            else:
                url = str(output)

            if url:
                images.append(
                    GeneratedImage(
                        index=i,
                        url=url,
                        width=1024,
                        height=1024,
                    )
                )

        return images


def get_generator(backend: str = "mock") -> ImageGenerator:
    """Get an image generator by backend name.
    
    Args:
        backend: "mock", "huggingface", "replicate", or "local"
        
    Returns:
        ImageGenerator instance
    """
    if backend == "mock":
        return MockGenerator()
    elif backend == "huggingface" or backend == "hf":
        return HuggingFaceGenerator()
    elif backend == "replicate":
        return ReplicateGenerator()
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'mock', 'huggingface', or 'replicate'")
