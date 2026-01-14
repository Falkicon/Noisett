"""ML Pipeline - Image generation backends.

Supports multiple backends:
- mock: Returns placeholder images (for testing)
- replicate: Uses Replicate API (has HiDream, FLUX)
- local: Local diffusers pipeline (requires GPU)
"""

import os
from abc import ABC, abstractmethod

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
    ) -> list[GeneratedImage]:
        """Generate images from a prompt."""
        pass


class MockGenerator(ImageGenerator):
    """Mock generator that creates simple placeholder images for testing."""

    # Colors for placeholder images
    COLORS = ["#107C10", "#0078D4", "#5C2D91", "#D83B01"]

    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: ModelId,
        quality: QualityPreset,
        count: int,
    ) -> list[GeneratedImage]:
        """Generate placeholder images with colored backgrounds."""
        import random
        import tempfile
        from pathlib import Path
        import asyncio
        
        # Simulate processing time (1-2 seconds)
        await asyncio.sleep(1.5)
        
        output_dir = Path(tempfile.gettempdir()) / "noisett"
        output_dir.mkdir(exist_ok=True)

        images = []
        for i in range(count):
            seed = random.randint(1, 999999)
            color = self.COLORS[i % len(self.COLORS)]
            short_prompt = prompt[:30].replace('"', "'").replace('<', '').replace('>', '')
            
            # Create simple SVG placeholder using concatenation to avoid encoding issues
            svg_lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">',
                f'  <rect width="100%" height="100%" fill="{color}"/>',
                f'  <text x="512" y="480" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" fill="white">Generated #{i+1}</text>',
                f'  <text x="512" y="550" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="white" opacity="0.7">{short_prompt}</text>',
                f'  <text x="512" y="600" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="white" opacity="0.5">Mock - Seed: {seed}</text>',
                '</svg>',
            ]
            svg_content = '\n'.join(svg_lines)
            
            filename = f"mock_{i}_{seed}.svg"
            filepath = output_dir / filename
            filepath.write_text(svg_content, encoding='utf-8')
            
            images.append(
                GeneratedImage(
                    index=i,
                    url=f"/api/images/{filename}",
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
    ) -> list[GeneratedImage]:
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


class FireworksGenerator(ImageGenerator):
    """Generator using Fireworks.ai API (cheapest FLUX option, ~$0.003/image)."""

    # Model mappings to Fireworks model IDs (workflows endpoint)
    MODEL_IDS = {
        ModelId.FLUX: "accounts/fireworks/models/flux-1-schnell-fp8",  # Fast, cheap
        ModelId.SD35: "accounts/fireworks/models/flux-1-dev-fp8",  # Higher quality
    }
    
    BASE_URL = "https://api.fireworks.ai/inference/v1/workflows"

    def __init__(self):
        self.api_key = os.environ.get("FIREWORKS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FIREWORKS_API_KEY environment variable not set. "
                "Get your key at https://fireworks.ai/account/api-keys"
            )

    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: ModelId,
        quality: QualityPreset,
        count: int,
    ) -> list[GeneratedImage]:
        """Generate images using Fireworks.ai REST API."""
        import httpx
        import random
        import tempfile
        from pathlib import Path
        
        # Get model ID
        model_id = self.MODEL_IDS.get(model, self.MODEL_IDS[ModelId.FLUX])
        
        # Build enhanced prompt based on asset type
        from src.core.types import ASSET_TYPE_CONFIGS
        asset_config = ASSET_TYPE_CONFIGS[asset_type]
        enhanced_prompt = asset_config.prompt_template.replace("{subject}", prompt)
        
        # Quality to size mapping
        size_map = {"draft": 512, "standard": 1024, "high": 1024}
        size = size_map.get(quality.value, 1024)
        
        # Build API URL
        api_url = f"{self.BASE_URL}/{model_id}/text_to_image"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "image/jpeg",
        }
        
        images = []
        output_dir = Path(tempfile.gettempdir()) / "noisett"
        output_dir.mkdir(exist_ok=True)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(count):
                seed = random.randint(1, 999999)
                
                payload = {
                    "prompt": enhanced_prompt,
                    "width": size,
                    "height": size,
                    "seed": seed,
                }
                
                response = await client.post(api_url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    raise ValueError(
                        f"Fireworks API error: {response.status_code} - {response.text}"
                    )
                
                # Save image to temp file
                filename = f"fireworks_{i}_{seed}.jpg"
                image_path = output_dir / filename
                image_path.write_bytes(response.content)
                
                # Return API URL for serving (not file:// URL)
                images.append(
                    GeneratedImage(
                        index=i,
                        url=f"/api/images/{filename}",
                        width=size,
                        height=size,
                        seed=seed,
                    )
                )
        
        return images


class ReplicateGenerator(ImageGenerator):
    """Generator using Replicate API (FLUX dev-lora for high quality generation)."""

    # Using FLUX dev-lora - works without version hash
    MODEL_ID = "black-forest-labs/flux-dev-lora"

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
    ) -> list[GeneratedImage]:
        """Generate images using Replicate FLUX dev-lora API."""
        import replicate
        import random

        # Build enhanced prompt based on asset type
        from src.core.types import ASSET_TYPE_CONFIGS

        asset_config = ASSET_TYPE_CONFIGS[asset_type]
        enhanced_prompt = asset_config.prompt_template.replace("{subject}", prompt)

        # Quality to inference steps mapping
        steps_map = {"draft": 20, "standard": 28, "high": 40}
        num_steps = steps_map.get(quality.value, 28)
        
        # Quality to output_quality mapping
        quality_map = {"draft": 70, "standard": 85, "high": 95}
        output_quality = quality_map.get(quality.value, 85)

        images = []
        for i in range(count):
            seed = random.randint(1, 999999)
            
            # Debug: print what we're doing
            print(f"[REPLICATE] Using model: {self.MODEL_ID}")
            print(f"[REPLICATE] Prompt: {enhanced_prompt[:50]}...")
            
            # Run prediction with FLUX dev-lora params
            output = await replicate.async_run(
                self.MODEL_ID,
                input={
                    "prompt": enhanced_prompt,
                    "go_fast": True,
                    "guidance": 3,
                    "megapixels": "1",
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "webp",
                    "output_quality": output_quality,
                    "num_inference_steps": num_steps,
                    "seed": seed,
                },
            )

            # Handle output - FLUX returns a list of FileOutput objects
            if isinstance(output, list) and len(output) > 0:
                item = output[0]
                url = item.url if hasattr(item, 'url') else str(item)
            elif hasattr(output, 'url'):
                url = output.url
            else:
                url = str(output)

            if url:
                images.append(
                    GeneratedImage(
                        index=i,
                        url=url,
                        width=1024,
                        height=1024,
                        seed=seed,
                    )
                )

        return images


def get_generator(backend: str = "mock") -> ImageGenerator:
    """Get an image generator by backend name.
    
    Args:
        backend: "mock", "huggingface", "replicate", "fireworks", or "local"
        
    Returns:
        ImageGenerator instance
    """
    if backend == "mock":
        return MockGenerator()
    elif backend == "huggingface" or backend == "hf":
        return HuggingFaceGenerator()
    elif backend == "replicate":
        return ReplicateGenerator()
    elif backend == "fireworks":
        return FireworksGenerator()
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'mock', 'huggingface', 'replicate', or 'fireworks'")
