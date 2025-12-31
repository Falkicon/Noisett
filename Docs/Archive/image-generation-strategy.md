# Image generation strategy

> **Goal:** Build a code-driven, self-hosted image generation engine trained on brand guidelines, replacing the current ComfyUI + Stable Diffusion + LoRA workflow with something more controllable and modern.

---

## Current State of the Art Models (Dec 2025)

The image generation landscape has evolved significantly beyond the older Stable Diffusion models. Here are the leading open-source options for enterprise/internal use:

### Tier 1: Latest Generation

| Model                          | Release | Architecture                             | Native Resolution | Key Strengths                                            | License                      |
| ------------------------------ | ------- | ---------------------------------------- | ----------------- | -------------------------------------------------------- | ---------------------------- |
| **FLUX.1** (Black Forest Labs) | 2024    | Transformer + Rectified Flow             | 1024×1024         | Excellent prompt adherence, text rendering, photorealism | Dev (open), Pro (commercial) |
| **FLUX.2**                     | 2025    | Transformer + Rectified Flow             | 1024×1024+        | Improved quality, better fine-tuning support             | Check latest terms           |
| **HiDream-I1**                 | 2025    | Diffusion Transformer                    | 1024×1024         | Claimed to outperform FLUX dev; fast inference           | Apache 2.0                   |
| **Janus Pro 7B** (DeepSeek)    | 2025    | Multimodal (unified vision-language)     | 1024×1024         | Outperforms DALL-E 3 on benchmarks; WebGPU support       | Open source                  |
| **SD 3.5** (Stability AI)      | 2024    | MMDiT (Multimodal Diffusion Transformer) | 1024×1024         | Good text rendering, strong ecosystem                    | Community license            |

### Tier 2: Mature & Well-Supported

| Model              | Key Strengths                                            | Best For                                        |
| ------------------ | -------------------------------------------------------- | ----------------------------------------------- |
| **SDXL**           | Largest ecosystem, most LoRAs available, well-documented | Teams needing extensive customization resources |
| **SDXL Turbo**     | Fast inference (1-4 steps)                               | Real-time or high-volume generation             |
| **Playground 2.5** | Aesthetic quality                                        | Artistic/creative outputs                       |

<aside>
💡

**Recommendation:** FLUX.1 or FLUX.2 are currently the best balance of quality, fine-tuning support, and code-driven workflows. HiDream-I1 is worth evaluating if you need Apache 2.0 licensing.

</aside>

---

## Code-Driven Libraries & Frameworks

Moving away from ComfyUI to programmatic control, these are your primary options:

### 🐍 Hugging Face Diffusers (Recommended)

The de facto standard Python library for working with diffusion models programmatically.

```python
from diffusers import FluxPipeline
import torch

# Load base model
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    torch_dtype=torch.bfloat16
)
[pipe.to](http://pipe.to)("cuda")

# Load your custom LoRA
pipe.load_lora_weights("path/to/your-brand-lora")

# Generate
image = pipe(
    prompt="A modern icon of a clipboard with checkmarks, brand style",
    num_inference_steps=28,
    guidance_scale=3.5
).images[0]
```

**Why Diffusers:**

- Native support for FLUX, SDXL, SD3.5, and most major models
- Built-in LoRA loading and training utilities
- Excellent documentation
- Easy integration with training pipelines
- Active development and community

### Other Options

| Library                             | Use Case                                                       |
| ----------------------------------- | -------------------------------------------------------------- |
| **ComfyUI (API mode)**              | If you want to keep existing workflows but drive them via code |
| **Invoke AI**                       | Higher-level abstraction, good for creative teams              |
| [\*\*Fal.ai](http://Fal.ai) SDK\*\* | Serverless inference, fast iteration                           |

---

## Fine-Tuning Approaches for Brand Training

### LoRA (Low-Rank Adaptation) — Recommended

**What it is:** Lightweight fine-tuning that trains small adapter weights instead of the full model.

**Pros:**

- Small file sizes (typically 10-200 MB vs 6+ GB for full model)
- Can combine multiple LoRAs (style + subject + composition)
- Fast training (hours, not days)
- Easy to version and swap

**Training Tools:**

- `diffusers` training scripts
- `kohya-ss/sd-scripts` (popular, well-tested)
- `ai-toolkit` by Ostris

### DreamBooth

**What it is:** Fine-tunes the model to learn a specific subject/concept with a unique token.

**Best for:** Teaching the model specific brand characters, mascots, or product shots.

### Full Fine-Tuning

**When to consider:** Only if you have massive compute budget and need to fundamentally alter the model's style. Usually overkill for brand guidelines.

<aside>
⚡

**For your use case:** Start with LoRA training on FLUX.1-dev. Train separate LoRAs for:

- **Style LoRA:** Your brand's visual language (colors, rendering style)
- **Subject LoRAs:** Specific brand elements (logo treatments, icon styles)
</aside>

---

## Azure Deployment Options

### Option 1: Azure Container Apps with Serverless GPU

Microsoft offers serverless GPU support in Azure Container Apps, allowing you to deploy without manual infrastructure configuration.

**Pros:** Auto-scaling, no driver management, pay-per-use

**Cons:** May have cold start latency

### Option 2: Azure Kubernetes Service (AKS) + AI Toolchain Operator

Deploy models on AKS with the AI toolchain operator add-on for more control.

**Pros:** Full control, can optimize for your workload

**Cons:** More operational overhead

### Option 3: Azure ML + Custom Container

Package your Diffusers pipeline in a container and deploy as a managed endpoint.

**Pros:** Integrates with Azure ML ecosystem, model versioning

**Cons:** Azure ML learning curve

### Option 4: Self-Managed VMs with GPU

Spin up NC or ND series VMs with NVIDIA GPUs.

**Pros:** Maximum control, predictable costs for steady workloads

**Cons:** You manage everything

<aside>
🎯

**Suggested starting point:** Azure Container Apps with serverless GPU for inference, Azure ML for training jobs.

</aside>

---

## Model-Agnostic Architecture (Swappable Models)

To enable easy testing and future-proofing, we'll build an abstraction layer that lets you swap between models via configuration.

### Design Principles

1. **Model Registry** — Register available models with their configs, LoRAs, and default parameters
2. **Unified Interface** — All models expose the same `generate()` method
3. **Config-Driven Selection** — Switch models via API parameter or environment variable
4. **Separate LoRA Management** — Store LoRAs per-model, automatically load the right ones

### Target Models for Initial Support

| Model        | Pipeline Class             | LoRA Format  | Notes                     |
| ------------ | -------------------------- | ------------ | ------------------------- |
| FLUX.1-dev   | `FluxPipeline`             | FLUX LoRA    | Primary recommendation    |
| HiDream-I1   | `HiDreamPipeline`          | HiDream LoRA | Apache 2.0, good fallback |
| SD 3.5 Large | `StableDiffusion3Pipeline` | SD3 LoRA     | Strong ecosystem          |

### Example: Model Abstraction Layer

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import torch

@dataclass
class GenerationRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 1024
    height: int = 1024
    num_inference_steps: int = 28
    guidance_scale: float = 3.5
    seed: Optional[int] = None

class BaseImageModel(ABC):
    """Abstract base class for all image models."""

    @abstractmethod
    def load(self) -> None:
        """Load model weights and LoRAs."""
        pass

    @abstractmethod
    def generate(self, request: GenerationRequest) -> "PIL.Image":
        """Generate an image from the request."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Free GPU memory."""
        pass

class FluxModel(BaseImageModel):
    def __init__(self, model_id: str, lora_paths: list[str]):
        self.model_id = model_id
        self.lora_paths = lora_paths
        self.pipe = None

    def load(self):
        from diffusers import FluxPipeline
        self.pipe = FluxPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.bfloat16
        ).to("cuda")
        for lora_path in self.lora_paths:
            self.pipe.load_lora_weights(lora_path)

    def generate(self, request: GenerationRequest):
        generator = torch.Generator("cuda").manual_seed(request.seed) if request.seed else None
        return self.pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            generator=generator
        ).images[0]

    def unload(self):
        del self.pipe
        torch.cuda.empty_cache()

# Similar implementations for HiDreamModel, SD3Model...
```

### Model Registry & Factory

```python
from enum import Enum

class ModelType(str, Enum):
    FLUX = "flux"
    HIDREAM = "hidream"
    SD3 = "sd3"

MODEL_REGISTRY = {
    ModelType.FLUX: {
        "class": FluxModel,
        "model_id": "black-forest-labs/FLUX.1-dev",
        "lora_paths": ["./loras/flux/brand-style.safetensors"],
        "default_steps": 28,
        "default_guidance": 3.5,
    },
    ModelType.HIDREAM: {
        "class": HiDreamModel,
        "model_id": "HiDream-ai/HiDream-I1-Full",
        "lora_paths": ["./loras/hidream/brand-style.safetensors"],
        "default_steps": 50,
        "default_guidance": 5.0,
    },
    [ModelType.SD](http://ModelType.SD)3: {
        "class": SD3Model,
        "model_id": "stabilityai/stable-diffusion-3.5-large",
        "lora_paths": ["./loras/sd3/brand-style.safetensors"],
        "default_steps": 40,
        "default_guidance": 4.5,
    },
}

def get_model(model_type: ModelType) -> BaseImageModel:
    config = MODEL_REGISTRY[model_type]
    return config["class"](
        model_id=config["model_id"],
        lora_paths=config["lora_paths"]
    )
```

### API Endpoint with Model Selection

```python
from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()

# Pre-load default model, lazy-load others
loaded_models: dict[ModelType, BaseImageModel] = {}

class GenerateRequest(BaseModel):
    prompt: str
    model: ModelType = ModelType.FLUX  # Default to FLUX
    width: int = 1024
    height: int = 1024
    seed: int | None = None

@[app.post](http://app.post)("/generate")
async def generate_image(request: GenerateRequest):
    # Lazy load model if not already loaded
    if request.model not in loaded_models:
        loaded_models[request.model] = get_model(request.model)
        loaded_models[request.model].load()

    model = loaded_models[request.model]
    image = model.generate(GenerationRequest(
        prompt=request.prompt,
        width=request.width,
        height=request.height,
        seed=request.seed
    ))

    # Return image as base64 or save to blob storage
    return {"image": image_to_base64(image)}
```

<aside>
🔄

**Swap models easily:**

- **Testing:** Hit the same endpoint with `model: "flux"` vs `model: "hidream"` to compare
- **A/B testing:** Route percentage of traffic to different models
- **New models:** Add to registry, train LoRA, deploy — no API changes needed
</aside>

### Updated Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Brand Asset Generation API                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐    ┌──────────────────┐    ┌────────────────────┐    │
│   │   FastAPI    │───▶│  Model Registry  │───▶│   Model Adapters   │    │
│   │   Service    │    │    & Factory     │    │                    │    │
│   └──────────────┘    └──────────────────┘    │  ┌──────────────┐  │    │
│          │                    │               │  │  FLUX.1-dev  │  │    │
│          │                    │               │  │  + LoRAs     │  │    │
│          │                    │               │  └──────────────┘  │    │
│          │                    │               │  ┌──────────────┐  │    │
│          │                    │               │  │  HiDream-I1  │  │    │
│          │                    │               │  │  + LoRAs     │  │    │
│          │                    │               │  └──────────────┘  │    │
│          │                    │               │  ┌──────────────┐  │    │
│          │                    │               │  │    SD 3.5    │  │    │
│          │                    │               │  │  + LoRAs     │  │    │
│          ▼                    ▼               │  └──────────────┘  │    │
│   ┌──────────────┐    ┌──────────────┐       └────────────────────┘    │
│   │    Azure     │    │    LoRA      │                                  │
│   │    Blob      │    │   Storage    │        Azure Container Apps      │
│   │   Storage    │    │  (per model) │              (GPU)               │
│   └──────────────┘    └──────────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### LoRA Management Strategy

Since each model family uses different LoRA formats, organize them separately:

```
/loras
  /flux
    brand-style-v1.safetensors
    brand-style-v2.safetensors
    icon-style.safetensors
  /hidream
    brand-style-v1.safetensors
  /sd3
    brand-style-v1.safetensors
```

<aside>
⚠️

**Important:** You'll need to train separate LoRAs for each model architecture. The same training images can be used, but the training process and output format differ. Budget time for training 3 LoRAs instead of 1.

</aside>

---

## Next Steps

- [ ] **Evaluate models:** Run test generations with FLUX.1-dev and HiDream-I1 using your brand prompts
- [ ] **Collect training data:** Gather 20-50 high-quality examples of your brand style for LoRA training
- [ ] **Set up training pipeline:** Use Diffusers or kohya-ss scripts for LoRA training
- [ ] **Prototype API:** Build a simple FastAPI wrapper around Diffusers
- [ ] **Azure POC:** Deploy to Azure Container Apps for initial testing
- [ ] **Iterate:** Refine LoRAs based on generation quality

---

## Resources

- [Hugging Face Diffusers Documentation](https://huggingface.co/docs/diffusers)
- [FLUX.1 on Hugging Face](https://huggingface.co/black-forest-labs/FLUX.1-dev)
- [HiDream-I1 GitHub](https://github.com/HiDream-ai/HiDream-I1)
- [Azure Container Apps GPU Tutorial](https://learn.microsoft.com/en-us/azure/container-apps/)
- [LoRA Training Guide (Diffusers)](https://huggingface.co/docs/diffusers/training/lora)

---

## Quality Optimization Strategies

For impressive, production-ready outputs, consider these techniques beyond the base model + LoRA setup:

### 1. Multi-Stage Generation Pipeline

Don't just generate once — use a refinement pipeline:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Base      │────▶│   Refiner   │────▶│  Upscaler   │────▶│   Post-     │
│   Generate  │     │   Pass      │     │  (4x)       │     │  Processing │
│   1024×1024 │     │   (optional)│     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

- **Base generation:** FLUX at 1024×1024 with your brand LoRA
- **Refiner pass:** Img2img at lower denoise (0.2-0.4) to add detail
- **Upscaler:** Real-ESRGAN or SUPIR for crisp 4K outputs
- **Post-processing:** Auto color correction, format optimization

### 2. Style Consistency with IP-Adapter

**IP-Adapter** lets you use reference images to guide style, not just text prompts.

```python
from diffusers import FluxPipeline
from diffusers.utils import load_image

pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models")

# Use a brand reference image to guide style
style_reference = load_image("brand_style_reference.png")

image = pipe(
    prompt="A clipboard icon with checkmarks",
    ip_adapter_image=style_reference,
    ip_adapter_scale=0.6,  # Blend strength
).images[0]
```

<aside>
✨

**Why this matters:** LoRAs teach the model your style, but IP-Adapter ensures _every_ output matches a specific reference. Great for icon sets that need to feel cohesive.

</aside>

### 3. ControlNet for Precise Composition

When you need exact layouts (e.g., icon must be centered, specific pose):

| ControlNet Type | Use Case                           |
| --------------- | ---------------------------------- |
| **Canny edge**  | Match the outline of a sketch      |
| **Depth**       | Maintain spatial layout            |
| **Pose**        | Character positioning              |
| **Tile**        | Upscaling with detail preservation |

### 4. Intelligent Prompt Engineering

Build prompt templates that consistently produce great results:

```python
PROMPT_TEMPLATES = {
    "icon": """
        {subject}, flat design icon,
        minimal vector style, solid background,
        clean edges, professional UI icon,
        brand style, high contrast
    """,
    "illustration": """
        {subject}, editorial illustration style,
        brand color palette, clean composition,
        professional quality, detailed but not cluttered
    """,
    "hero_image": """
        {subject}, cinematic composition,
        dramatic lighting, brand aesthetic,
        4k quality, sharp details
    """
}

NEGATIVE_PROMPT = """
    blurry, low quality, distorted,
    watermark, text artifacts,
    oversaturated, amateur
"""
```

### 5. Generate Variations, Pick the Best

For important assets, don't settle for one output:

```python
def generate_with_selection(prompt: str, num_variations: int = 4):
    """Generate multiple variations for human selection."""
    images = []
    for i in range(num_variations):
        image = pipe(
            prompt=prompt,
            seed=random.randint(0, 2**32),
        ).images[0]
        images.append(image)

    # Return grid or save all for user to pick
    return create_comparison_grid(images)
```

### 6. Quality Presets

Offer different quality tiers based on need:

| Preset       | Steps | Resolution | Upscale      | Use Case           |
| ------------ | ----- | ---------- | ------------ | ------------------ |
| **Draft**    | 15    | 512×512    | No           | Quick ideation     |
| **Standard** | 28    | 1024×1024  | No           | Most use cases     |
| **High**     | 40    | 1024×1024  | 2x           | Final assets       |
| **Ultra**    | 50    | 1024×1024  | 4x + refiner | Hero images, print |

### 7. Training Data Quality & Volume

The single biggest factor in output quality is your training data. Here's what you need:

### Training Data Volume Guidelines

| Level         | Image Count    | When to Use                         | Expected Results                               |
| ------------- | -------------- | ----------------------------------- | ---------------------------------------------- |
| **Minimum**   | 10-15 images   | Proof of concept only               | Basic style transfer, inconsistent results     |
| **Good**      | 20-35 images   | Most projects                       | Solid style adherence, good for single concept |
| **Great**     | 50-100 images  | Production quality                  | Strong generalization, handles edge cases well |
| **Excellent** | 100-200 images | Complex styles or multiple concepts | Near-perfect style matching, very flexible     |

### What Counts as "One Image"?

Each training image should be:

- **Unique** — Don't include crops or minor variations of the same image
- **Representative** — Shows your brand style clearly
- **High quality** — Your best work, not filler

### Detailed Recommendations by Use Case

**For a single style LoRA (e.g., "brand illustration style"):**

- Minimum: 15-20 images
- Recommended: 30-50 images
- Include variety: different subjects, compositions, color treatments all in your style

**For a subject LoRA (e.g., "our mascot character"):**

- Minimum: 10-15 images
- Recommended: 20-30 images
- Include variety: different poses, angles, expressions, contexts

**For icons specifically:**

- Minimum: 20-25 icons
- Recommended: 40-60 icons
- Include: different icon types (objects, actions, concepts), different complexity levels

### Quality Checklist

- [ ] All images are 1024×1024 or higher resolution
- [ ] Consistent style across all images (don't mix old and new brand styles)
- [ ] Each image has a detailed, accurate caption
- [ ] Captions use consistent terminology (e.g., always "flat icon" not sometimes "flat" sometimes "minimal")
- [ ] No watermarks, compression artifacts, or low-quality images
- [ ] Variety in subject matter while maintaining style consistency
- [ ] Hand-picked by your best designer, not bulk-selected

### Caption Quality Matters

Good captions dramatically improve results. Compare:

**Bad caption:**

> icon

**Good caption:**

> A flat design clipboard icon with three checkmarks, orange and white color scheme, minimal vector style, solid light gray background, clean edges, professional UI icon

<aside>
🎯

**Pro tip:** Have your best designer hand-pick the training set. The model will learn to produce the "average" quality of what it sees — make sure that average is high. 30 carefully curated images will outperform 150 hastily gathered ones.

</aside>

### Diminishing Returns

```
Quality
  ▲
  │                        ╭───────────────
  │                   ╭────╯
  │              ╭────╯
  │         ╭────╯
  │    ╭────╯
  │ ───╯
  └────────────────────────────────────────▶ Training Images
     10   25   50   75   100  150  200+
         ↑              ↑
    Sweet spot     Diminishing returns
    for most       kick in here
    projects
```

Beyond ~100 images, you'll see diminishing returns unless you're training multiple distinct concepts or a very complex style.

### 8. Post-Processing Pipeline

Automate finishing touches:

```python
def post_process(image):
    # Auto color correction to brand palette
    image = adjust_to_brand_colors(image)

    # Sharpen for crisp edges (icons)
    image = apply_unsharp_mask(image, amount=0.5)

    # Export in multiple formats
    return {
        "png": export_png(image, optimize=True),
        "svg": trace_to_svg(image),  # For icons
        "webp": export_webp(image, quality=90),
    }
```

### 9. Recommended Upscalers

| Upscaler            | Best For         | Notes                         |
| ------------------- | ---------------- | ----------------------------- |
| **Real-ESRGAN**     | General purpose  | Fast, good quality            |
| **SUPIR**           | Photorealistic   | Slower, adds realistic detail |
| **Topaz Gigapixel** | Print assets     | Commercial, excellent quality |
| **Tile ControlNet** | Preserving style | Keeps artistic style intact   |

---

## Asset Type Pipeline

The studio needs to generate four distinct asset types, each with different style requirements, resolutions, and quality settings.

### Asset Types Overview

| Asset Type                     | Size   | Style                 | Typical Use                  | Resolution            |
| ------------------------------ | ------ | --------------------- | ---------------------------- | --------------------- |
| **Icons**                      | Small  | Fluent 2              | UI elements, app icons       | 256×256 → 1024×1024   |
| **Product Illustrations**      | Medium | Brand style           | Product pages, documentation | 1024×1024 → 2048×2048 |
| **Product Logo Illustrations** | Medium | Simple, iconic        | App tiles, feature callouts  | 512×512 → 1024×1024   |
| **Premium Illustrations**      | Large  | Rich, marketing-grade | Websites, banners, campaigns | 1024×1024 → 4096×4096 |

### LoRA Strategy: Separate LoRAs Per Asset Type

For best results, train dedicated LoRAs for each asset type:

```
/loras
  /flux
    icons-fluent2-v1.safetensors        # Fluent 2 icon style
    product-illustrations-v1.safetensors # Mid-complexity product art
    logo-illustrations-v1.safetensors    # Simple iconic style
    premium-illustrations-v1.safetensors # Rich marketing style
```

<aside>
💡

**Why separate LoRAs?** Each asset type has distinct visual characteristics. A single "brand style" LoRA would be a compromise. Dedicated LoRAs let each type shine.

</aside>

### Training Data Per Asset Type

| Asset Type                | Recommended Images | Notes                                                             |
| ------------------------- | ------------------ | ----------------------------------------------------------------- |
| **Icons (Fluent 2)**      | 40-60 icons        | Include variety: objects, actions, concepts, different complexity |
| **Product Illustrations** | 30-50 images       | Different products, compositions, contexts                        |
| **Logo Illustrations**    | 25-40 images       | Focus on simplicity and iconic clarity                            |
| **Premium Illustrations** | 50-80 images       | Most complex style needs more examples                            |

### Asset Type Configuration

```python
from dataclasses import dataclass
from enum import Enum

class AssetType(str, Enum):
    ICON = "icon"
    PRODUCT_ILLUSTRATION = "product_illustration"
    LOGO_ILLUSTRATION = "logo_illustration"
    PREMIUM_ILLUSTRATION = "premium_illustration"

@dataclass
class AssetTypeConfig:
    name: str
    lora_path: str
    lora_strength: float
    default_size: tuple[int, int]
    output_sizes: list[tuple[int, int]]
    steps: int
    guidance_scale: float
    prompt_template: str
    negative_prompt: str
    use_refiner: bool
    use_upscaler: bool

ASSET_CONFIGS = {
    AssetType.ICON: AssetTypeConfig(
        name="Fluent 2 Icon",
        lora_path="./loras/flux/icons-fluent2-v1.safetensors",
        lora_strength=0.85,
        default_size=(512, 512),
        output_sizes=[(256, 256), (512, 512), (1024, 1024)],
        steps=28,
        guidance_scale=3.5,
        prompt_template="""
            {subject}, Fluent 2 design icon,
            minimal vector style, solid background,
            clean geometric shapes, professional UI icon,
            Microsoft design language, subtle gradients,
            centered composition, high contrast
        """,
        negative_prompt="photorealistic, 3d render, complex, cluttered, text, watermark",
        use_refiner=False,
        use_upscaler=True,  # Upscale to crisp edges
    ),

    AssetType.PRODUCT_ILLUSTRATION: AssetTypeConfig(
        name="Product Illustration",
        lora_path="./loras/flux/product-illustrations-v1.safetensors",
        lora_strength=0.8,
        default_size=(1024, 1024),
        output_sizes=[(1024, 1024), (2048, 2048)],
        steps=35,
        guidance_scale=4.0,
        prompt_template="""
            {subject}, product illustration style,
            clean professional aesthetic, brand color palette,
            balanced composition, clear focal point,
            suitable for documentation and product pages
        """,
        negative_prompt="cluttered, amateur, low quality, watermark",
        use_refiner=True,
        use_upscaler=True,
    ),

    AssetType.LOGO_ILLUSTRATION: AssetTypeConfig(
        name="Logo Illustration",
        lora_path="./loras/flux/logo-illustrations-v1.safetensors",
        lora_strength=0.85,
        default_size=(512, 512),
        output_sizes=[(512, 512), (1024, 1024)],
        steps=30,
        guidance_scale=3.5,
        prompt_template="""
            {subject}, simple iconic illustration,
            logo-style artwork, clean and memorable,
            limited color palette, strong silhouette,
            works at small sizes, brand aesthetic
        """,
        negative_prompt="complex, detailed, photorealistic, busy, cluttered",
        use_refiner=False,
        use_upscaler=True,
    ),

    AssetType.PREMIUM_ILLUSTRATION: AssetTypeConfig(
        name="Premium Illustration",
        lora_path="./loras/flux/premium-illustrations-v1.safetensors",
        lora_strength=0.75,
        default_size=(1024, 1024),
        output_sizes=[(1024, 1024), (2048, 2048), (4096, 4096)],
        steps=45,
        guidance_scale=4.5,
        prompt_template="""
            {subject}, premium editorial illustration,
            marketing-grade quality, rich visual storytelling,
            sophisticated color palette, dynamic composition,
            hero image quality, brand aesthetic,
            suitable for websites and marketing campaigns
        """,
        negative_prompt="amateur, stock photo, generic, low effort, clipart",
        use_refiner=True,
        use_upscaler=True,
    ),
}
```

### API with Asset Type Selection

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class GenerateRequest(BaseModel):
    prompt: str
    asset_type: AssetType = AssetType.PRODUCT_ILLUSTRATION
    model: ModelType = ModelType.FLUX
    size_preset: str = "default"  # "small", "default", "large"
    quality: str = "standard"     # "draft", "standard", "high"
    num_variations: int = 1

@[app.post](http://app.post)("/generate")
async def generate(request: GenerateRequest):
    # Get asset config
    config = ASSET_CONFIGS[request.asset_type]

    # Get model
    model = get_model(request.model)
    model.load_lora(config.lora_path, strength=config.lora_strength)

    # Build full prompt from template
    full_prompt = config.prompt_template.format(subject=request.prompt)

    # Adjust steps based on quality setting
    steps = {
        "draft": config.steps // 2,
        "standard": config.steps,
        "high": int(config.steps * 1.5)
    }[request.quality]

    # Generate
    images = []
    for _ in range(request.num_variations):
        image = model.generate(
            prompt=full_prompt,
            negative_prompt=config.negative_prompt,
            width=config.default_size[0],
            height=config.default_size[1],
            steps=steps,
            guidance_scale=config.guidance_scale,
        )

        # Apply refinement pipeline if configured
        if config.use_refiner and request.quality != "draft":
            image = apply_refiner(image)
        if config.use_upscaler and request.quality == "high":
            image = upscale(image, scale=2)

        images.append(image)

    return {"images": [to_base64(img) for img in images]}
```

### Example UI Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  Brand Asset Generator                                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Asset Type:  ┌─────────────────────────────────────────────────┐   │
│               │ ○ Icons (Fluent 2)                              │   │
│               │ ● Product Illustrations                         │   │
│               │ ○ Logo Illustrations                            │   │
│               │ ○ Premium Illustrations (Marketing)             │   │
│               └─────────────────────────────────────────────────┘   │
│                                                                      │
│  Describe what you need:                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ A person collaborating with AI on a creative project       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Quality:     ○ Draft    ● Standard    ○ High                        │
│  Variations:  [ 4 ▼ ]                                                │
│                                                                      │
│               [ Generate ]                                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Visual Comparison: Asset Types

|                     | Icons       | Product       | Logo         | Premium    |
| ------------------- | ----------- | ------------- | ------------ | ---------- |
| **Complexity**      | Simple      | Medium        | Simple       | High       |
| **Detail level**    | Minimal     | Moderate      | Low          | Rich       |
| **Color palette**   | Limited     | Brand colors  | Very limited | Full range |
| **Generation time** | ~15 sec     | ~25 sec       | ~20 sec      | ~45 sec    |
| **Best for**        | UI, buttons | Docs, product | App tiles    | Marketing  |

<aside>
🔄

**Hot-swapping:** Users can generate the same concept across different asset types to see which works best. Generate "cloud computing" as an icon, product illustration, and premium illustration in one session.

</aside>

---

## Deployment Recommendation (Internal Microsoft Use)

Given the context:

- **Internal Microsoft project** with Azure access
- **~100 person studio** generating **10-100 images/month**
- **Cost-conscious** but not hyper-optimized

### Recommended: Azure Container Apps with Serverless GPU

This is the sweet spot for your usage pattern:

| Consideration   | Recommendation                                                 |
| --------------- | -------------------------------------------------------------- |
| **Compute**     | Azure Container Apps with serverless GPU (auto scale-to-zero)  |
| **Why**         | Pay only when generating; no idle costs during nights/weekends |
| **Cold start**  | ~30-60 seconds acceptable for internal tool use                |
| **GPU tier**    | NVIDIA T4 or A10G sufficient for inference                     |
| **Concurrency** | Queue requests; 1-2 GPU instances handles 100 users fine       |

### Cost Optimization Tips

1. **Scale to zero** — Don't keep GPUs warm. Cold starts are fine for internal tools.
2. **Single model loaded** — Keep only the default model (FLUX) loaded; lazy-load others on-demand for comparison testing.
3. **Batch requests** — If someone needs 10 icons, queue them rather than spinning up 10 parallel jobs.
4. **Use model caching** — Store model weights in Azure Blob so container restarts don't re-download from Hugging Face.
5. **Right-size GPU** — T4 (16GB VRAM) runs FLUX fine; no need for A100s for inference.

### Estimated Costs (Rough)

| Usage Pattern                        | Est. Monthly Cost |
| ------------------------------------ | ----------------- |
| **Your usage (10-100 images/month)** | **~$5-20**        |
| Moderate (200 images/month)          | $30-50            |
| Heavy (1,000+ images/month)          | $100-200          |

_Assumes scale-to-zero, T4 GPU, ~30 sec/image generation time._

<aside>
💸

**Great news:** At 10-100 images/month, your Azure costs will be negligible — likely under $20/month. The scale-to-zero model means you only pay for actual generation time.

</aside>

### Simple Architecture for Your Scale

For 100 users with intermittent use, keep it simple:

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Internal   │────▶│   FastAPI on     │────▶│   Azure Blob     │
│   Web UI     │     │   Container Apps │     │   (outputs +     │
│   or Slack   │◀────│   (serverless    │     │    model cache)  │
│   Bot        │     │    GPU)          │     │                  │
└──────────────┘     └──────────────────┘     └──────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │   Azure Queue    │  ← Optional: for
                     │   (if needed)    │    handling bursts
                     └──────────────────┘
```

<aside>
💡

**Skip the complexity:** For your scale, you likely don't need Kubernetes, multiple replicas, or sophisticated load balancing. A single Container App that scales 0→1→2 based on demand is plenty.

</aside>

### Frontend Options

Since it's internal, you have flexibility:

- **Simple web UI** — React/Vue app with auth via Microsoft Entra ID
- **Slack/Teams bot** — Let people request images via chat
- **Figma plugin** — If designers want it in their workflow
- **CLI tool** — For power users / batch jobs

---

## Licensing Considerations

Since you're training on your own assets and generating new assets for internal use and product:

### What You're Doing (Low Risk)

| Aspect                | Your Situation                              | Risk Level               |
| --------------------- | ------------------------------------------- | ------------------------ |
| **Training data**     | Your own brand assets                       | ✅ No issue — you own it |
| **Base model**        | FLUX.1-dev, HiDream, SD3.5                  | ⚠️ Check license terms   |
| **Generated outputs** | Reference for designers, or used in product | ✅ Generally fine        |
| **Use case**          | Internal tool, internal/product use         | ✅ Low risk              |

### Base Model License Summary

| Model              | License                     | Commercial Use      | Notes                                            |
| ------------------ | --------------------------- | ------------------- | ------------------------------------------------ |
| **FLUX.1-dev**     | FLUX.1-dev Non-Commercial   | ❌ No (dev version) | Use FLUX.1-pro or check for commercial license   |
| **FLUX.1-schnell** | Apache 2.0                  | ✅ Yes              | Faster, slightly lower quality                   |
| **HiDream-I1**     | Apache 2.0                  | ✅ Yes              | Fully open for commercial use                    |
| **SD 3.5 Large**   | Stability Community License | ⚠️ Conditional      | Free under $1M revenue, otherwise license needed |
| **SDXL**           | CreativeML Open RAIL++-M    | ✅ Yes              | Very permissive                                  |

### FLUX Commercial License Pricing (Black Forest Labs)

| Model                    | Monthly Cost  | Included Images | Overage     |
| ------------------------ | ------------- | --------------- | ----------- |
| **FLUX.2 [dev]**         | $1,999/month  | 200,000 images  | $0.01/image |
| **FLUX.1 Kontext [dev]** | $999/month    | 100,000 images  | $0.01/image |
| **FLUX.1 [dev]**         | Contact sales | —               | —           |

For enterprise/custom arrangements, Black Forest Labs offers a "Talk to Sales" option.

<aside>
💰

**Cost estimate for your usage:** At 10-100 images/month, the $1,999/month FLUX license is overkill. Stick with HiDream (Apache 2.0, free) unless FLUX quality becomes essential — then revisit licensing.

</aside>

### Recommended Approach: Dual-Track with User Notice

Support both FLUX (best quality) and HiDream (Apache 2.0) with clear UI messaging:

```
┌─────────────────────────────────────────────────────────────┐
│  Model Selection                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ● FLUX.2 (Highest Quality)                                 │
│    ⚠️ For design reference only unless commercial license    │
│       is purchased. Not for direct use in product.          │
│                                                             │
│  ○ HiDream (Commercial OK)                                  │
│    ✅ Apache 2.0 — can be used directly in product           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

This way:

1. Designers can use FLUX for highest quality during ideation
2. Clear notice that FLUX outputs are "reference only" without license
3. HiDream available for assets going directly into product
4. If the team decides FLUX quality is worth it, purchase the $1,999/month license and remove the restriction

### Your Specific Use Cases

**As design reference (designers create final art):**

- Very low risk regardless of model license
- Generated images are inspiration, not final deliverable
- Similar to using any reference image

**Directly in product:**

- Use a commercially-licensed model (HiDream, FLUX-schnell, SDXL)
- Or obtain commercial license for FLUX.1-dev/pro
- Document your training data provenance (your own assets)

### Recommendation

For maximum flexibility and zero licensing concerns:

1. **Primary model:** HiDream-I1 (Apache 2.0, commercial OK)
2. **Fallback:** SDXL or FLUX.1-schnell
3. **If quality demands FLUX.1-dev:** Use for reference only, or pursue commercial license

---

## Multi-Frontend Architecture

Bring the tool to the designer with a shared backend and multiple interfaces.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Frontends                                   │
│                                                                        │
│   ┌────────────────────┐   ┌────────────────────┐   ┌───────────────┐  │
│   │     Web App        │   │   Figma Plugin     │   │  Future: CLI  │  │
│   │   (React + Auth)   │   │   (TypeScript)     │   │  Teams Bot    │  │
│   │                    │   │                    │   │  VS Code ext  │  │
│   │  • General access  │   │  • In-workflow     │   │               │  │
│   │  • No install      │   │  • Direct insert   │   │               │  │
│   │  • Full features   │   │  • Asset library   │   │               │  │
│   └────────────────────┘   └────────────────────┘   └───────────────┘  │
│            │                        │                        │         │
└────────────┼────────────────────────┼────────────────────────┼─────────┘
             │                        │                        │
             └────────────┬───────────┴────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Shared REST API                                   │
│                     (FastAPI + Auth)                                   │
│                                                                        │
│   POST /generate     → Submit generation job, get job_id              │
│   GET  /jobs/{id}    → Poll status, get results when ready            │
│   GET  /jobs/{id}/images → Download generated images                  │
│   POST /regenerate   → Generate more variations of same prompt        │
│   GET  /asset-types  → List available asset types and configs        │
│   GET  /history      → User's generation history                      │
│                                                                        │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Generation Backend (GPU)                              │
│                 Azure Container Apps                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Frontend 1: Web App (Primary)

**Purpose:** General access, full features, no installation required.

**Tech stack:**

- React or Vue.js
- Microsoft Entra ID (Azure AD) for auth
- Hosted on Azure Static Web Apps

**Features:**

- Full asset type selection
- Quality and variation controls
- Generation history
- Download in multiple formats
- Side-by-side comparison
- Batch generation

**User flow:**

```
1. User visits internal URL, authenticates via Entra ID
2. Selects asset type (Icon, Product, Logo, Premium)
3. Enters description
4. Clicks Generate → sees spinner with progress
5. Views results grid (4 variations)
6. Picks favorite, downloads, or clicks "Generate More"
```

### Frontend 2: Figma Plugin

**Purpose:** In-context generation for designers, direct insert into designs.

**Tech stack:**

- TypeScript + Figma Plugin API
- Calls same REST backend

**Features:**

- Streamlined UI (fits Figma panel)
- Insert directly onto canvas
- Asset type presets
- Recent generations
- Quick regenerate

**User flow:**

```
1. Designer opens plugin panel in Figma
2. Selects asset type from dropdown
3. Types description
4. Clicks Generate
5. Sees thumbnail results in panel
6. Clicks image → inserted directly onto Figma canvas
7. Can regenerate or tweak from there
```

<aside>
🎨

**Figma-specific win:** Designers can generate, compare, and insert without leaving their workflow. No copy-paste, no downloads, no context switching.

</aside>

### Async Job Pattern

Since quality > speed, use an async pattern that keeps users informed:

```python
# Submit job
POST /generate
{
    "prompt": "cloud computing concept",
    "asset_type": "premium_illustration",
    "num_variations": 4,
    "quality": "high"
}

# Response
{
    "job_id": "abc-123",
    "status": "queued",
    "estimated_time_seconds": 45
}

# Poll for status
GET /jobs/abc-123
{
    "job_id": "abc-123",
    "status": "processing",  # queued → processing → complete
    "progress": 0.6,
    "images_completed": 2,
    "images_total": 4
}

# When complete
GET /jobs/abc-123
{
    "job_id": "abc-123",
    "status": "complete",
    "images": [
        {"url": "https://...", "seed": 12345},
        {"url": "https://...", "seed": 67890},
        ...
    ],
    "prompt": "cloud computing concept",
    "asset_type": "premium_illustration"
}

# Generate more with same settings
POST /regenerate
{
    "job_id": "abc-123",
    "num_variations": 4
}
```

### UI: Iterative Workflow

Make it easy to iterate:

```
┌─────────────────────────────────────────────────────────────┐
│  Results: "cloud computing concept"                       │
├─────────────────────────────────────────────────────────────┤
│                                                            │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│   │           │  │           │  │           │  │           │  │
│   │   Img 1   │  │   Img 2   │  │   Img 3   │  │   Img 4   │  │
│   │           │  │     ★     │  │           │  │           │  │
│   └───────────┘  └───────────┘  └───────────┘  └───────────┘  │
│                                                            │
│   [ ⬇ Download ]  [ ★ Favorite ]  [ 🔄 More Like This ]    │
│                                                            │
│   [ Generate 4 More ]   [ Tweak Prompt & Regenerate ]      │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

**Key iteration features:**

- **"Generate 4 More"** — Same prompt, new seeds
- **"More Like This"** — Use a favorite as seed for variations
- **"Tweak Prompt"** — Edit prompt, keep other settings
- **History sidebar** — Scroll back through session

### Development Priority

| Phase       | Deliverable                          | Effort    |
| ----------- | ------------------------------------ | --------- |
| **Phase 1** | Backend API + basic Web UI           | 4-6 weeks |
| **Phase 2** | Polish Web UI, add history/favorites | 2-3 weeks |
| **Phase 3** | Figma plugin (MVP)                   | 3-4 weeks |
| **Phase 4** | Figma polish, asset library features | 2-3 weeks |

---

## Project Timeline

### Key Dates

| Milestone                  | Target Date         | Notes                                |
| -------------------------- | ------------------- | ------------------------------------ |
| **Planning complete**      | Dec 2025            | This document                        |
| **Gather training assets** | Week of Jan 6, 2026 | Back in office, collect brand assets |
| **MVP launch**             | Jan 2026            | Basic Web UI + backend               |
| **Handoff to Engineering** | TBD                 | If MVP is successful                 |

### Proposed MVP Scope (January 2026)

Keep it tight for the initial build:

- [ ] **Backend:** FastAPI + Diffusers on Azure Container Apps
- [ ] **One model:** Start with HiDream (Apache 2.0, no licensing friction)
- [ ] **One asset type:** Product Illustrations (most general use)
- [ ] **Basic Web UI:** Prompt input, generate, view results, download
- [ ] **One LoRA:** Train on gathered assets
- [ ] **Auth:** Microsoft Entra ID

<aside>
🎯

**MVP philosophy:** Get something working end-to-end first. One model, one asset type, basic UI. Prove value, then expand.

</aside>

---

## v2 Roadmap

With agent-assisted development, these features can follow quickly after MVP. All specs are already documented above.

### v2.0 — Multi-Model & Asset Types

| Feature                   | Spec Location               | Key Work                                          |
| ------------------------- | --------------------------- | ------------------------------------------------- |
| **Add FLUX model**        | Model-Agnostic Architecture | Implement `FluxModel` adapter, train FLUX LoRA    |
| **Add SD 3.5 model**      | Model-Agnostic Architecture | Implement `SD3Model` adapter, train SD3 LoRA      |
| **Icons (Fluent 2)**      | Asset Type Pipeline         | Gather 40-60 icons, train LoRA, add asset config  |
| **Logo Illustrations**    | Asset Type Pipeline         | Gather 25-40 images, train LoRA, add asset config |
| **Premium Illustrations** | Asset Type Pipeline         | Gather 50-80 images, train LoRA, add asset config |
| **Model selection UI**    | Licensing Considerations    | Add model picker with license warnings            |

### v2.1 — Quality & Polish

| Feature                      | Spec Location                   | Key Work                                        |
| ---------------------------- | ------------------------------- | ----------------------------------------------- |
| **Quality presets**          | Quality Optimization Strategies | Draft/Standard/High/Ultra modes                 |
| **History & favorites**      | Multi-Frontend Architecture     | Add `/history` endpoint, favorites DB table, UI |
| **Batch generation**         | Multi-Frontend Architecture     | Queue multiple prompts, download as zip         |
| **IP-Adapter support**       | Quality Optimization Strategies | Reference image upload, style matching          |
| **Post-processing pipeline** | Quality Optimization Strategies | Auto color correction, multi-format export      |

### v2.2 — Figma Plugin

| Feature                    | Spec Location                            | Key Work                                            |
| -------------------------- | ---------------------------------------- | --------------------------------------------------- |
| **Figma plugin MVP**       | Multi-Frontend Architecture → Frontend 2 | TypeScript plugin, auth, generate, insert to canvas |
| **Asset library in Figma** | Multi-Frontend Architecture              | Browse history, re-use previous generations         |
| **Quick regenerate**       | Multi-Frontend Architecture              | "More like this" from selected image                |

### v2.3 — Advanced (If Needed)

| Feature                    | Spec Location                   | Key Work                                |
| -------------------------- | ------------------------------- | --------------------------------------- |
| **ControlNet integration** | Quality Optimization Strategies | Sketch-to-icon, pose control            |
| **Upscaler pipeline**      | Quality Optimization Strategies | Real-ESRGAN / SUPIR integration         |
| **Teams bot**              | Multi-Frontend Architecture     | Chat-based generation for non-designers |
| **CLI tool**               | Multi-Frontend Architecture     | Batch jobs, scripting support           |

<aside>
⚡

**Agent-assisted timeline:** With AI coding assistance, v2.0-v2.2 could realistically land in February 2026 if MVP goes smoothly. The architecture is designed to make each addition incremental.

</aside>

### Rough Timeline to MVP

```
Jan 6-10     Gather training assets (40-50 images)
             Set up Azure resources

Jan 13-17    Train first LoRA on HiDream
             Build FastAPI backend skeleton

Jan 20-24    Complete backend API
             Basic Web UI (React)

Jan 27-31    Integration, testing, polish
             Internal demo / soft launch
```

### Team

| Role                   | Person           | Notes                    |
| ---------------------- | ---------------- | ------------------------ |
| **Initial build**      | Jason            | Solo dev for MVP         |
| **Future maintenance** | Engineering team | If MVP proves successful |

---

## Open Questions (Resolved)

1. ~~What GPU budget/tier is available on Azure?~~ → _Resolved: Use T4/A10G with serverless scaling_
2. ~~How many images per day/hour do we need to generate?~~ → _Resolved: Intermittent, ~100 users_
3. ~~Do we need real-time generation or is batch/async acceptable?~~ → _Resolved: Async OK, quality > speed, easy iteration_
4. ~~What's the licensing situation?~~ → _Resolved: Training on own assets, use Apache 2.0 models (HiDream) for product use_
5. ~~What's the preferred interface?~~ → _Resolved: Web (primary) + Figma plugin (for designers)_
6. ~~Who will build/maintain this?~~ → _Resolved: Jason builds MVP, Engineering team may take over if successful_
7. ~~Timeline expectations?~~ → _Resolved: MVP in January 2026_
8. ~~Training data gathering?~~ → _Resolved: Week of Jan 6, 2026 when back in office_

[Product Strategy Brief](https://www.notion.so/Product-Strategy-Brief-2d779be0f2c58023aee8cee6fc89bb37?pvs=21)

[PM Specs](https://www.notion.so/PM-Specs-2d779be0f2c5801aacd0dc2b62a52471?pvs=21)

[Design Specs](https://www.notion.so/Design-Specs-2d779be0f2c580f28d79c687a3a2ae9d?pvs=21)

[Dev Specs](https://www.notion.so/Dev-Specs-2d779be0f2c58018badfc929a78701af?pvs=21)
