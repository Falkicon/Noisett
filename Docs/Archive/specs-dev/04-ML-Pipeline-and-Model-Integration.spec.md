# ML Pipeline & Model Integration

**Status:** Reference

**Framework:** PyTorch + Diffusers

**Primary Model:** HiDream-I1 (Apache 2.0)

---

## Model Overview

| Model | License | Commercial | VRAM | Phase |
| --- | --- | --- | --- | --- |
| HiDream-I1 | Apache 2.0 | ✅ Yes | ~16GB | MVP |
| FLUX.1-dev | FLUX-dev | ❌ No* | ~24GB | v2.0 |
| SD 3.5 Large | Community | ⚠️ Check | ~16GB | v2.0 |

*FLUX requires $1,999/month commercial license

---

## LoRA Training

### Training Data Requirements

| Asset Type | Minimum | Recommended |
| --- | --- | --- |
| Icons (Fluent 2) | 25 | 40-60 |
| Product Illustrations | 20 | 30-50 |
| Logo Illustrations | 15 | 25-40 |
| Premium Illustrations | 30 | 50-80 |

### Training Data Preparation

**Image Requirements:**

- Format: PNG or JPEG
- Resolution: 1024×1024
- Quality: High-quality, representative samples

**Directory Structure:**

```
training_data/
├── product_illustrations/
│   ├── image_001.png
│   ├── image_001.txt      # Caption
│   └── ...
├── icons/
├── logo_illustrations/
└── premium_illustrations/
```

### Training Script

```bash
accelerate launch train_[network.py](http://network.py) \
  --pretrained_model_name_or_path="HiDream/HiDream-I1-Full" \
  --train_data_dir="./training_data/product_illustrations" \
  --output_dir="./output/product_lora" \
  --output_name="brand_product_v1" \
  --network_module=networks.lora \
  --network_dim=32 \
  --network_alpha=16 \
  --resolution=1024,1024 \
  --train_batch_size=1 \
  --learning_rate=1e-4 \
  --max_train_epochs=10 \
  --mixed_precision="bf16"
```

---

## Inference Pipeline

### Core Implementation

```python
# ml/[inference.py](http://inference.py)
import torch
from diffusers import AutoPipelineForText2Image
from typing import List
from PIL import Image

class ImageGenerator:
    def __init__(self, model_id: str = "HiDream/HiDream-I1-Full"):
        self.model_id = model_id
        self.pipe = None
        self.device = "cuda"
        self.dtype = torch.bfloat16
        
    def load_model(self):
        if self.pipe is not None:
            return
            
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            self.model_id,
            torch_dtype=self.dtype,
            use_safetensors=True,
        ).to(self.device)
        
        self.pipe.enable_model_cpu_offload()
        
    def load_lora(self, lora_path: str, weight: float = 0.8):
        self.pipe.load_lora_weights(lora_path)
        self.pipe.fuse_lora(lora_scale=weight)
        
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_images: int = 4,
        num_inference_steps: int = 28,
        guidance_scale: float = 7.5,
    ) -> List[Image.Image]:
        self.load_model()
        
        results = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_images_per_prompt=num_images,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            width=1024,
            height=1024,
        )
        
        return results.images
```

### Prompt Templates

```python
ASSET_TYPE_TEMPLATES = {
    "product": {
        "trigger": "brandstyle",
        "prefix": "professional illustration, clean design,",
        "suffix": "high quality, detailed",
        "negative": "blurry, low quality, text, watermark",
    },
    "icons": {
        "trigger": "brandicon",
        "prefix": "minimal flat icon, fluent design,",
        "suffix": "clean lines, solid colors",
        "negative": "detailed, realistic, 3d, complex",
    },
    "logo": {
        "trigger": "brandlogo",
        "prefix": "logo illustration, iconic, simple,",
        "suffix": "clean design, professional",
        "negative": "complex, detailed, cluttered",
    },
    "premium": {
        "trigger": "brandpremium",
        "prefix": "premium marketing illustration, rich detail,",
        "suffix": "high quality, polished",
        "negative": "amateur, low quality, simple",
    },
}

def build_prompt(user_prompt: str, asset_type: str) -> tuple[str, str]:
    template = ASSET_TYPE_TEMPLATES[asset_type]
    full_prompt = f"{template['trigger']} {template['prefix']} {user_prompt}, {template['suffix']}"
    return full_prompt, template["negative"]
```

### Quality Presets

| Preset | Steps | Upscale | Est. Time |
| --- | --- | --- | --- |
| Draft | 15 | No | ~10 sec |
| Standard | 28 | No | ~25 sec |
| High | 40 | 2× | ~45 sec |
| Ultra | 50 | 4× | ~90 sec |

---

## Performance Benchmarks (A10 GPU)

| Model | Steps | Images | Time |
| --- | --- | --- | --- |
| HiDream | 15 | 4 | ~8-12 sec |
| HiDream | 28 | 4 | ~20-28 sec |
| HiDream | 40 | 4 | ~35-45 sec |

### Cold Start Times

| Operation | Time |
| --- | --- |
| Container startup | ~15-30 sec |
| Model load | ~20-40 sec |
| LoRA load | ~2-5 sec |
| **Total cold start** | ~45-75 sec |