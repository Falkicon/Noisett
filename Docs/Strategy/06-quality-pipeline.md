# Phase 6: Quality Pipeline

**Status:** 🔜 Planned  
**Dependencies:** Phase 4 (Deployment) ✅, Phase 5 (Training) recommended

---

## Goal

> Move from "good" to "impressive" outputs through multi-stage refinement, intelligent prompting, and post-processing.

The original strategy emphasized:

> "For impressive, production-ready outputs, consider these techniques beyond the base model + LoRA setup."

---

## Quality Tiers

Offer different quality levels based on user needs:

| Preset       | Steps | Resolution | Refinement       | Use Case       | Est. Time |
| ------------ | ----- | ---------- | ---------------- | -------------- | --------- |
| **Draft**    | 4     | 512×512    | None             | Quick ideation | ~2s       |
| **Standard** | 8     | 1024×1024  | None             | Most use cases | ~5s       |
| **High**     | 12    | 1024×1024  | Upscale          | Final assets   | ~10s      |
| **Ultra**    | 20    | 1024×1024  | Refine + Upscale | Hero images    | ~20s      |

---

## Multi-Stage Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Base      │────▶│   Refiner   │────▶│  Upscaler   │────▶│   Post-     │
│   Generate  │     │   Pass      │     │  (2-4x)     │     │  Processing │
│   1024×1024 │     │   (optional)│     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Stage 1: Base Generation

Current implementation using Fireworks FLUX-1 Schnell.

### Stage 2: Refiner Pass (Optional)

Img2img at low denoise (0.2-0.4) to add detail while preserving composition.

**When to use:**

- Premium illustrations
- Marketing assets
- Hero images

**Command:**

```bash
noisett refine '{"image_url": "...", "denoise_strength": 0.3}'
```

### Stage 3: Upscaling

Increase resolution for crisp final output.

| Upscaler            | Best For         | Speed  | Quality   |
| ------------------- | ---------------- | ------ | --------- |
| **Real-ESRGAN**     | General          | Fast   | Good      |
| **SUPIR**           | Photorealistic   | Slow   | Excellent |
| **Tile ControlNet** | Preserving style | Medium | Excellent |

**Command:**

```bash
noisett upscale '{"image_url": "...", "scale": 2, "model": "real-esrgan"}'
```

### Stage 4: Post-Processing

Automated finishing touches:

- **Color correction** — Align to brand palette
- **Sharpening** — Crisp edges (especially for icons)
- **Format optimization** — PNG/WebP/SVG output

---

## Intelligent Prompt Engineering

### Built-in Prompt Templates

The original strategy defined templates per asset type:

```python
PROMPT_TEMPLATES = {
    "icons": """
        {subject}, Fluent 2 design icon,
        minimal vector style, solid background,
        clean geometric shapes, professional UI icon,
        Microsoft design language, subtle gradients,
        centered composition, high contrast
    """,
    "product": """
        {subject}, product illustration style,
        clean professional aesthetic, brand color palette,
        balanced composition, clear focal point,
        suitable for documentation and product pages
    """,
    "logo": """
        {subject}, simple iconic illustration,
        logo-style artwork, clean and memorable,
        limited color palette, strong silhouette,
        works at small sizes, brand aesthetic
    """,
    "premium": """
        {subject}, premium editorial illustration,
        marketing-grade quality, rich visual storytelling,
        sophisticated color palette, dynamic composition,
        hero image quality, brand aesthetic
    """
}

NEGATIVE_PROMPT = """
    blurry, low quality, distorted,
    watermark, text artifacts,
    oversaturated, amateur
"""
```

### Command Integration

Update `asset.generate` to use templates:

```bash
noisett asset.generate '{
  "prompt": "cloud computing",
  "asset_type": "premium",
  "quality": "high"
}'
```

The command internally expands:

- User prompt: "cloud computing"
- Full prompt: Template + user prompt + negative prompt
- Quality settings: Steps, resolution, refinement based on preset

---

## Variation Generation

### Generate Multiple Options

For important assets, don't settle for one output:

```bash
noisett asset.generate '{
  "prompt": "cloud computing concept",
  "asset_type": "premium",
  "count": 4
}'
```

Returns 4 variations with different seeds.

### "More Like This"

Generate variations based on a favorite:

```bash
noisett variations '{
  "source_image": "https://...",
  "count": 4,
  "variation_strength": 0.3
}'
```

---

## Commands

### `quality.presets`

List available quality presets.

```bash
noisett quality.presets '{}'
```

### `refine`

Apply refinement pass to an image.

```bash
noisett refine '{
  "image_url": "https://...",
  "denoise_strength": 0.3,
  "steps": 20
}'
```

### `upscale`

Upscale an image.

```bash
noisett upscale '{
  "image_url": "https://...",
  "scale": 2,
  "model": "real-esrgan"
}'
```

### `variations`

Generate variations of an existing image.

```bash
noisett variations '{
  "source_image": "https://...",
  "count": 4,
  "variation_strength": 0.3
}'
```

### `post-process`

Apply automated post-processing.

```bash
noisett post-process '{
  "image_url": "https://...",
  "sharpen": true,
  "format": "png"
}'
```

---

## IP-Adapter Integration (Future)

Use reference images to guide style beyond text prompts:

```bash
noisett asset.generate '{
  "prompt": "clipboard icon",
  "style_reference": "https://brand-reference.png",
  "style_strength": 0.6
}'
```

**Why this matters:** LoRAs teach the model your style, but IP-Adapter ensures every output matches a specific reference. Great for icon sets that need cohesion.

---

## Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

class QualityPreset(str, Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"

class QualityPresetInfo(BaseModel):
    name: QualityPreset
    steps: int
    resolution: tuple[int, int]
    use_refiner: bool
    use_upscaler: bool
    description: str
    estimated_seconds: int

class RefineInput(BaseModel):
    image_url: str
    denoise_strength: float = Field(0.3, ge=0.1, le=0.5)
    steps: int = Field(20, ge=10, le=50)

class UpscaleInput(BaseModel):
    image_url: str
    scale: Literal[2, 4] = 2
    model: Literal["real-esrgan", "supir"] = "real-esrgan"

class VariationsInput(BaseModel):
    source_image: str
    count: int = Field(4, ge=1, le=8)
    variation_strength: float = Field(0.3, ge=0.1, le=0.7)

class PostProcessInput(BaseModel):
    image_url: str
    sharpen: bool = False
    color_correct: bool = False
    format: Literal["png", "webp", "jpeg"] = "png"
```

---

## Implementation Notes

### Upscaling Service Options

| Service         | API                | Cost           |
| --------------- | ------------------ | -------------- |
| **Replicate**   | Real-ESRGAN models | ~$0.01/image   |
| **Fireworks**   | Check availability | Variable       |
| **Self-hosted** | Real-ESRGAN Python | Free (compute) |

### Refinement via Img2Img

Most providers support img2img for refinement:

```python
# Fireworks example (if supported)
response = client.workflows.run(
    model="flux-1-dev-fp8",
    input={
        "prompt": "...",
        "image": base64_image,
        "strength": 0.3  # Low denoise preserves composition
    }
)
```

---

## Success Criteria

- [ ] Quality presets reflected in generation settings
- [ ] Prompt templates improve output consistency
- [ ] Upscaling command produces 2x resolution images
- [ ] Variations command generates coherent alternatives
- [ ] "High" quality visibly better than "Standard"

---

## Timeline Estimate

| Task                                    | Effort      |
| --------------------------------------- | ----------- |
| Quality presets in asset.generate       | 1 day       |
| Prompt templates                        | 1 day       |
| Upscale command + Replicate integration | 2 days      |
| Variations command                      | 1 day       |
| Post-processing                         | 2 days      |
| Testing                                 | 1-2 days    |
| **Total**                               | **~1 week** |

---

## Related Documents

- [Original Strategy: Quality Optimization](../Archive/image-generation-strategy.md#quality-optimization-strategies)
- [Original Strategy: Quality Presets](../Archive/image-generation-strategy.md#6-quality-presets)
