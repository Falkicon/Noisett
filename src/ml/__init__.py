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
        model: str,  # Changed from ModelId to str to support dynamic models
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
        model: str,
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
        model: str,
        quality: QualityPreset,
        count: int,
    ) -> list[GeneratedImage]:
        """Generate images using Hugging Face Inference API."""
        import httpx
        import base64
        import tempfile
        from pathlib import Path

        # Get model ID - try to convert string to ModelId enum, fallback to FLUX
        try:
            model_enum = ModelId(model) if isinstance(model, str) else model
            model_id = self.MODEL_IDS.get(model_enum, self.MODEL_IDS[ModelId.FLUX])
        except ValueError:
            model_id = self.MODEL_IDS[ModelId.FLUX]
        
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
        model: str,
        quality: QualityPreset,
        count: int,
    ) -> list[GeneratedImage]:
        """Generate images using Fireworks.ai REST API."""
        import httpx
        import random
        import tempfile
        from pathlib import Path

        # Get model ID - try to convert string to ModelId enum, fallback to FLUX
        try:
            model_enum = ModelId(model) if isinstance(model, str) else model
            model_id = self.MODEL_IDS.get(model_enum, self.MODEL_IDS[ModelId.FLUX])
        except ValueError:
            model_id = self.MODEL_IDS[ModelId.FLUX]
        
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
    """Generator using Replicate API for dynamic models from models.json."""

    # Default fallback model if not found in models.json
    DEFAULT_MODEL_ID = "black-forest-labs/flux-dev-lora"

    def __init__(self):
        # Support both REPLICATE_API_KEY and REPLICATE_API_TOKEN for flexibility
        self.api_token = os.environ.get("REPLICATE_API_KEY") or os.environ.get("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "REPLICATE_API_KEY environment variable not set. "
                "Get your token at https://replicate.com/account/api-tokens"
            )

    def _get_replicate_model_id(self, model: str) -> tuple[str, dict | None]:
        """Get the actual Replicate model ID from models.json.

        Args:
            model: Model ID string (e.g., 'replicate:nano-banana-pro')

        Returns:
            Tuple of (replicate_model_id, model_config)
        """
        from src.ml.registry import list_models

        models = list_models()
        model_config = models.get(model)

        if model_config and model_config.get("replicateModel"):
            return model_config["replicateModel"], model_config

        # Fallback to default
        return self.DEFAULT_MODEL_ID, None

    async def generate(
        self,
        prompt: str,
        asset_type: AssetType,
        model: str,  # Changed from ModelId to str to support dynamic models
        quality: QualityPreset,
        count: int,
    ) -> list[GeneratedImage]:
        """Generate images using the specified model from models.json."""
        import replicate
        import random

        # Get actual Replicate model ID from models.json
        replicate_model_id, model_config = self._get_replicate_model_id(model)

        # Build enhanced prompt based on asset type
        from src.core.types import ASSET_TYPE_CONFIGS

        asset_config = ASSET_TYPE_CONFIGS[asset_type]
        enhanced_prompt = asset_config.prompt_template.replace("{subject}", prompt)

        # Debug: print what we're doing
        print(f"[REPLICATE] Model requested: {model}")
        print(f"[REPLICATE] Using Replicate model: {replicate_model_id}")
        print(f"[REPLICATE] Prompt: {enhanced_prompt[:50]}...")

        images = []
        for i in range(count):
            seed = random.randint(1, 999999)

            # Build model-specific input parameters
            input_params = self._build_input_params(
                replicate_model_id,
                enhanced_prompt,
                quality,
                seed,
                model_config,
            )

            print(f"[REPLICATE] Input params: {input_params}")

            # Run prediction
            output = await replicate.async_run(
                replicate_model_id,
                input=input_params,
            )

            # Handle output - models return a list of FileOutput objects
            print(f"[REPLICATE] Raw output type: {type(output)}")
            print(f"[REPLICATE] Raw output: {output}")

            if isinstance(output, list) and len(output) > 0:
                item = output[0]
                print(f"[REPLICATE] Item type: {type(item)}")
                url = item.url if hasattr(item, 'url') else str(item)
            elif hasattr(output, 'url'):
                url = output.url
            else:
                url = str(output)

            print(f"[REPLICATE] Final URL: {url}")

            # Calculate dimensions from input params
            resolution = input_params.get("resolution", "1K")
            aspect_ratio = input_params.get("aspect_ratio", "1:1")
            # Handle size param for models that use it instead of resolution
            if "size" in input_params and input_params["size"] in ["2K", "4K"]:
                resolution = input_params["size"]
            width, height = self._get_dimensions_for_resolution(resolution, aspect_ratio)

            if url:
                images.append(
                    GeneratedImage(
                        index=i,
                        url=url,
                        width=width,
                        height=height,
                        seed=seed,
                    )
                )

        return images

    def _get_dimensions_for_resolution(
        self, resolution: str, aspect_ratio: str = "1:1"
    ) -> tuple[int, int]:
        """Calculate width and height from resolution string and aspect ratio.

        Args:
            resolution: Resolution string like "1K", "2K", "4K", "1 MP", "2 MP", etc.
            aspect_ratio: Aspect ratio like "1:1", "16:9", "4:3", etc.

        Returns:
            Tuple of (width, height)
        """
        # Parse aspect ratio
        if ":" in aspect_ratio:
            w_ratio, h_ratio = map(int, aspect_ratio.split(":"))
        else:
            w_ratio, h_ratio = 1, 1

        # Base pixel counts for different resolutions
        # K-based (Nano Banana, Seedream)
        k_pixels = {
            "1K": 1024 * 1024,      # ~1 megapixel
            "2K": 2048 * 2048,      # ~4 megapixels
            "4K": 4096 * 4096,      # ~16 megapixels
        }

        # MP-based (FLUX 2)
        mp_pixels = {
            "0.5 MP": 512 * 1024,
            "1 MP": 1024 * 1024,
            "2 MP": 1448 * 1448,    # sqrt(2M) ≈ 1414, rounded
            "4 MP": 2048 * 2048,
        }

        # Get total pixels
        total_pixels = k_pixels.get(resolution) or mp_pixels.get(resolution) or (1024 * 1024)

        # Calculate dimensions maintaining aspect ratio
        # width * height = total_pixels
        # width / height = w_ratio / h_ratio
        # So: width = sqrt(total_pixels * w_ratio / h_ratio)
        import math
        width = int(math.sqrt(total_pixels * w_ratio / h_ratio))
        height = int(total_pixels / width)

        return width, height

    def _build_input_params(
        self,
        replicate_model_id: str,
        prompt: str,
        quality: QualityPreset,
        seed: int,
        model_config: dict | None = None,
    ) -> dict:
        """Build model-specific input parameters.

        Different models have different API parameters. This method
        builds the correct parameters based on the model.
        """
        # Quality mappings
        quality_map = {"draft": 70, "standard": 85, "high": 95}
        output_quality = quality_map.get(quality.value, 85)
        steps_map = {"draft": 20, "standard": 28, "high": 40}
        num_steps = steps_map.get(quality.value, 28)

        # Detect model type and build appropriate params
        model_lower = replicate_model_id.lower()

        # Google Nano Banana Pro
        # Params: prompt, image_input[], aspect_ratio, resolution (1K/2K/4K), output_format
        if "nano-banana" in model_lower:
            resolution_map = {"draft": "1K", "standard": "2K", "high": "4K"}
            return {
                "prompt": prompt,
                "aspect_ratio": "1:1",
                "resolution": resolution_map.get(quality.value, "2K"),
                "output_format": "png",
            }

        # FLUX.2 [max] - different from FLUX.1 dev-lora
        # Params: prompt, input_images[], aspect_ratio, resolution (0.5 MP/1 MP/2 MP/4 MP), seed, output_format
        if "flux-2" in model_lower or "flux.2" in model_lower:
            resolution_map = {"draft": "1 MP", "standard": "2 MP", "high": "4 MP"}
            return {
                "prompt": prompt,
                "aspect_ratio": "1:1",
                "resolution": resolution_map.get(quality.value, "2 MP"),
                "output_format": "png",
                "output_quality": output_quality,
                "seed": seed,
            }

        # Recraft V3 SVG - specialized for vector graphics
        # Params: prompt, aspect_ratio, size, style (any/engraving/line_art/line_circuit/linocut)
        if "recraft" in model_lower:
            return {
                "prompt": prompt,
                "style": "any",  # Let the model decide best style
                "aspect_ratio": "1:1",
                "size": "1024x1024",
            }

        # ByteDance Seedream 4.5
        # Params: prompt, image_input[], size (2K/4K/custom), aspect_ratio
        if "seedream" in model_lower or "bytedance" in model_lower:
            size_map = {"draft": "2K", "standard": "2K", "high": "4K"}
            return {
                "prompt": prompt,
                "aspect_ratio": "1:1",
                "size": size_map.get(quality.value, "2K"),
            }

        # Qwen Image
        # Params: prompt, seed, go_fast, guidance, image_size, aspect_ratio, output_format, num_inference_steps
        if "qwen" in model_lower:
            image_size = "optimize_for_speed" if quality.value == "draft" else "optimize_for_quality"
            return {
                "prompt": prompt,
                "aspect_ratio": "1:1",
                "image_size": image_size,
                "guidance": 3.0,
                "num_inference_steps": num_steps,
                "output_format": "png",
                "output_quality": output_quality,
                "seed": seed,
                "go_fast": quality.value == "draft",
            }

        # HiDream models (prunaai)
        # Params: prompt, model_type, speed_mode, resolution, seed, output_format, output_quality
        if "hidream" in model_lower or "prunaai" in model_lower:
            # Speed mode affects quality vs speed tradeoff
            speed_map = {
                "draft": "Extra Juiced 🍹",
                "standard": "Lightly Juiced 🍊",
                "high": "Unsqueezed 🍋",
            }
            return {
                "prompt": prompt,
                "resolution": "1024 × 1024 (Square)",
                "speed_mode": speed_map.get(quality.value, "Lightly Juiced 🍊"),
                "output_format": "png",
                "output_quality": 100,
                "seed": seed,
            }

        # Default: FLUX.1 [dev] LoRA style parameters
        # Params: prompt, aspect_ratio, num_outputs, num_inference_steps, guidance, seed, output_format, go_fast, megapixels
        return {
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "num_outputs": 1,
            "num_inference_steps": num_steps,
            "guidance": 3.0,
            "megapixels": "1",
            "output_format": "png",
            "output_quality": output_quality,
            "go_fast": False,
            "seed": seed,
        }

    async def generate_with_lora(
        self,
        prompt: str,
        asset_type: AssetType,
        model: str,  # Model ID string (ignored for LoRA, always uses flux-dev-lora)
        quality: QualityPreset,
        count: int,
        lora_url: str,
        lora_scale: float = 1.0,
    ) -> list[GeneratedImage]:
        """Generate images using FLUX dev-lora with custom LoRA weights.

        Args:
            prompt: Text description of the image
            asset_type: Type of asset to generate
            model: Model ID (ignored, always uses FLUX dev-lora for LoRA inference)
            quality: Quality preset affecting inference steps
            count: Number of images to generate
            lora_url: URL to LoRA weights (safetensors format)
            lora_scale: Strength of LoRA effect (0.0 to 2.0)
        """
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
            print(f"[REPLICATE+LORA] Using model: {self.DEFAULT_MODEL_ID}")
            print(f"[REPLICATE+LORA] LoRA URL: {lora_url[:50]}...")
            print(f"[REPLICATE+LORA] Prompt: {enhanced_prompt[:50]}...")

            # Run prediction with FLUX dev-lora + custom LoRA
            output = await replicate.async_run(
                self.DEFAULT_MODEL_ID,
                input={
                    "prompt": enhanced_prompt,
                    "hf_lora": lora_url,  # Custom LoRA weights URL
                    "lora_scale": lora_scale,
                    "go_fast": False,  # Disable for better quality
                    "guidance": 3.5,  # Slightly higher for LoRA
                    "megapixels": "1",
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "png",  # PNG for better quality (no compression artifacts)
                    "num_inference_steps": num_steps,
                    "seed": seed,
                },
            )

            # Handle output - FLUX returns a list of FileOutput objects
            print(f"[REPLICATE+LORA] Raw output type: {type(output)}")
            print(f"[REPLICATE+LORA] Raw output: {output}")

            if isinstance(output, list) and len(output) > 0:
                item = output[0]
                print(f"[REPLICATE+LORA] Item type: {type(item)}")
                url = item.url if hasattr(item, 'url') else str(item)
            elif hasattr(output, 'url'):
                url = output.url
            else:
                url = str(output)

            print(f"[REPLICATE+LORA] Final URL: {url}")

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

    async def generate_with_references(
        self,
        prompt: str,
        asset_type: AssetType,
        model: str,  # Model ID string
        quality: QualityPreset,
        count: int,
        reference_urls: list[str],
        model_config: dict | None = None,
    ) -> list[GeneratedImage]:
        """Generate images using a model with reference images.

        Args:
            prompt: Text description of the image
            asset_type: Type of asset to generate
            model: Model ID to use
            quality: Quality preset affecting inference steps
            count: Number of images to generate
            reference_urls: List of URLs to reference images
            model_config: Model configuration from models.json
        """
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

        # Get model ID from config or use default
        replicate_model = model_config.get("replicateModel", self.DEFAULT_MODEL_ID) if model_config else self.DEFAULT_MODEL_ID

        images = []
        for i in range(count):
            seed = random.randint(1, 999999)

            # Debug: print what we're doing
            print(f"[REPLICATE+REF] Using model: {replicate_model}")
            print(f"[REPLICATE+REF] Reference images: {len(reference_urls)}")
            print(f"[REPLICATE+REF] Prompt: {enhanced_prompt[:50]}...")

            # Build model-specific input params
            model_lower = replicate_model.lower()

            # Nano Banana Pro - uses image_input for reference images
            if "nano-banana" in model_lower:
                resolution_map = {"draft": "1K", "standard": "2K", "high": "4K"}
                input_params = {
                    "prompt": enhanced_prompt,
                    "image_input": reference_urls,  # Nano Banana Pro uses image_input
                    "aspect_ratio": "1:1",
                    "resolution": resolution_map.get(quality.value, "2K"),
                    "output_format": "png",  # Only jpg or png supported
                }
            # FLUX.2 [max] - uses input_images
            elif "flux-2" in model_lower or "flux.2" in model_lower:
                resolution_map = {"draft": "1 MP", "standard": "2 MP", "high": "4 MP"}
                input_params = {
                    "prompt": enhanced_prompt,
                    "input_images": reference_urls,
                    "aspect_ratio": "1:1",
                    "resolution": resolution_map.get(quality.value, "2 MP"),
                    "output_format": "png",
                    "output_quality": output_quality,
                    "seed": seed,
                }
            # Seedream - uses image_input
            elif "seedream" in model_lower or "bytedance" in model_lower:
                size_map = {"draft": "2K", "standard": "2K", "high": "4K"}
                input_params = {
                    "prompt": enhanced_prompt,
                    "image_input": reference_urls,
                    "aspect_ratio": "1:1",
                    "size": size_map.get(quality.value, "2K"),
                }
            # Default: FLUX-style parameters
            else:
                input_params = {
                    "prompt": enhanced_prompt,
                    "input_images": reference_urls,
                    "go_fast": True,
                    "guidance": 3.5,
                    "megapixels": "1",
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "png",
                    "output_quality": output_quality,
                    "num_inference_steps": num_steps,
                    "seed": seed,
                }

            print(f"[REPLICATE+REF] Input params: {input_params}")

            # Run prediction
            output = await replicate.async_run(
                replicate_model,
                input=input_params,
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
