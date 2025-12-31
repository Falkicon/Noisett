# Phase 5: LoRA Training Pipeline

**Status:** 🔜 Planned  
**Dependencies:** Phase 4 (Deployment) ✅

---

## Goal

> Enable training custom LoRAs on brand assets, so generated images match the studio's visual language.

This is the **core differentiator** from generic image generation. The original strategy document emphasized:

> "The AI is trained on our existing brand assets, so outputs match our style without manual guidance."

---

## Why Training Matters

| Without Training                      | With Training                                     |
| ------------------------------------- | ------------------------------------------------- |
| Generic FLUX outputs                  | Brand-aligned outputs                             |
| Designers manually adjust every image | Outputs usable immediately or with minimal tweaks |
| Inconsistent style across generations | Cohesive visual language                          |
| Prompt engineering required           | Simple descriptions work                          |

---

## Training Approach: LoRA

**LoRA (Low-Rank Adaptation)** is the recommended approach from the original strategy:

- **Small file sizes:** 10-200 MB vs 6+ GB for full model
- **Combinable:** Style + subject + composition LoRAs can stack
- **Fast training:** Hours, not days
- **Easy versioning:** Swap LoRAs without redeploying model

---

## LoRA Strategy: Per Asset Type

Train **separate LoRAs for each asset type** for best results:

| Asset Type                | Training Images | LoRA File                              |
| ------------------------- | --------------- | -------------------------------------- |
| **Icons**                 | 40-60           | `icons-fluent2-v1.safetensors`         |
| **Product Illustrations** | 30-50           | `product-illustrations-v1.safetensors` |
| **Logo Illustrations**    | 25-40           | `logo-illustrations-v1.safetensors`    |
| **Premium Illustrations** | 50-80           | `premium-illustrations-v1.safetensors` |

```
/loras
  /flux
    icons-fluent2-v1.safetensors
    product-illustrations-v1.safetensors
    logo-illustrations-v1.safetensors
    premium-illustrations-v1.safetensors
```

---

## Training Data Requirements

### Volume Guidelines

| Level         | Image Count | Expected Results                   |
| ------------- | ----------- | ---------------------------------- |
| **Minimum**   | 10-15       | Basic style transfer, inconsistent |
| **Good**      | 20-35       | Solid adherence, single concept    |
| **Great**     | 50-100      | Strong generalization              |
| **Excellent** | 100-200     | Near-perfect matching              |

### Quality Checklist

- [ ] All images 1024×1024 or higher
- [ ] Consistent style (don't mix old/new brand styles)
- [ ] Detailed, accurate captions per image
- [ ] Consistent caption terminology
- [ ] No watermarks or compression artifacts
- [ ] Variety in subject, consistency in style
- [ ] Hand-picked by best designer

### Caption Quality

**Bad:**

> icon

**Good:**

> A flat design clipboard icon with three checkmarks, orange and white color scheme, minimal vector style, solid light gray background, clean edges, professional UI icon

---

## Commands (AFD Pattern)

Following Agent-First Development, training is exposed as commands:

### `lora.create`

Initialize a new LoRA training project.

```bash
noisett lora.create '{
  "name": "icons-fluent2-v1",
  "description": "Fluent 2 style icons for UI",
  "base_model": "flux",
  "asset_type": "icons"
}'
```

**Output:**

```json
{
  "success": true,
  "data": {
    "lora_id": "lora_abc123",
    "name": "icons-fluent2-v1",
    "status": "created",
    "image_count": 0
  },
  "reasoning": "Created new LoRA project. Add 40-60 training images."
}
```

### `lora.upload-images`

Add training images with captions.

```bash
noisett lora.upload-images '{
  "lora_id": "lora_abc123",
  "images": [
    {
      "path": "./training/icon-001.png",
      "caption": "A flat clipboard icon with checkmarks, orange and white..."
    }
  ]
}'
```

### `lora.train`

Start training job.

```bash
noisett lora.train '{
  "lora_id": "lora_abc123",
  "epochs": 1000,
  "learning_rate": 1e-4
}'
```

**Output:**

```json
{
  "success": true,
  "data": {
    "training_job_id": "train_xyz789",
    "status": "queued",
    "estimated_time_minutes": 45
  },
  "reasoning": "Training job queued. Will train for 1000 epochs on 45 images."
}
```

### `lora.status`

Check training progress.

```bash
noisett lora.status '{"lora_id": "lora_abc123"}'
```

### `lora.list`

List available LoRAs.

```bash
noisett lora.list '{}'
```

### `lora.activate`

Set active LoRA for generation.

```bash
noisett lora.activate '{
  "lora_id": "lora_abc123",
  "strength": 0.85
}'
```

### `lora.delete`

Remove a LoRA.

```bash
noisett lora.delete '{"lora_id": "lora_abc123"}'
```

---

## Backend Options

### Option 1: Replicate (Recommended for MVP)

Replicate offers hosted LoRA training for FLUX models.

| Aspect     | Details                          |
| ---------- | -------------------------------- |
| **Cost**   | ~$5-20 per training run          |
| **Time**   | 30-60 minutes                    |
| **Ease**   | Simple API, no GPU management    |
| **Output** | Downloadable `.safetensors` file |

```python
import replicate

training = replicate.trainings.create(
    version="ostris/flux-dev-lora-trainer",
    input={
        "input_images": "https://...",  # Zip of training images
        "trigger_word": "fluenticon",
        "steps": 1000,
    },
    destination="your-username/icons-fluent2"
)
```

### Option 2: Modal

Pay-per-second GPU compute with Python-native workflow.

| Aspect      | Details                           |
| ----------- | --------------------------------- |
| **Cost**    | ~$2-10 per training run           |
| **Time**    | 30-60 minutes                     |
| **Control** | Full control over training script |
| **Ease**    | More setup than Replicate         |

### Option 3: Azure ML

Enterprise option with full audit trail.

| Aspect      | Details             |
| ----------- | ------------------- |
| **Cost**    | Variable (GPU time) |
| **Time**    | 30-90 minutes       |
| **Control** | Maximum control     |
| **Ease**    | Most complex        |

---

## Integration with Fireworks.ai

**Current state:** Noisett uses Fireworks.ai for inference (FLUX-1 Schnell).

**Challenge:** Fireworks doesn't support custom LoRA uploads (as of Dec 2025).

**Options:**

1. **Train elsewhere, use elsewhere** — Train on Replicate, deploy trained model to Replicate for inference
2. **Hybrid** — Keep Fireworks for base generation, switch to Replicate when LoRA needed
3. **Wait for Fireworks LoRA support** — May come in 2025

**Recommendation:** Start with Replicate for both training AND inference when LoRAs are needed. Fireworks remains the default for non-customized generation.

---

## Storage Architecture

```
Azure Blob Storage
└── noisett/
    ├── loras/
    │   ├── icons-fluent2-v1.safetensors
    │   ├── product-illustrations-v1.safetensors
    │   └── ...
    ├── training-data/
    │   ├── lora_abc123/
    │   │   ├── images/
    │   │   └── captions.json
    │   └── ...
    └── generated/
        └── ...
```

---

## Pydantic Schemas

```python
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

class LoraStatus(str, Enum):
    CREATED = "created"
    UPLOADING = "uploading"
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"

class CreateLoraInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    base_model: Literal["flux", "sdxl"] = "flux"
    asset_type: Literal["icons", "product", "logo", "premium"]

class CreateLoraOutput(BaseModel):
    lora_id: str
    name: str
    status: LoraStatus
    image_count: int

class TrainingImage(BaseModel):
    path: str
    caption: str = Field(..., min_length=10, max_length=500)

class UploadImagesInput(BaseModel):
    lora_id: str
    images: list[TrainingImage]

class TrainLoraInput(BaseModel):
    lora_id: str
    epochs: int = Field(1000, ge=100, le=5000)
    learning_rate: float = Field(1e-4, ge=1e-6, le=1e-2)

class LoraInfo(BaseModel):
    lora_id: str
    name: str
    description: str
    status: LoraStatus
    image_count: int
    asset_type: str
    created_at: str
    trained_at: str | None
    file_url: str | None
```

---

## Success Criteria

- [ ] `lora.create` command works via CLI
- [ ] Training images can be uploaded with captions
- [ ] Training job completes successfully on Replicate
- [ ] Trained LoRA produces visibly different output than base model
- [ ] LoRA can be activated for generation
- [ ] All commands return `CommandResult` with reasoning

---

## Dependencies

- **Replicate account** with billing
- **Azure Blob Storage** for training data and LoRA files
- **Training data** from design team (20-50 images per asset type)

---

## Timeline Estimate

| Task                       | Effort         |
| -------------------------- | -------------- |
| Command schemas + handlers | 2-3 days       |
| Replicate integration      | 1-2 days       |
| Azure Blob storage         | 1 day          |
| CLI commands               | 1 day          |
| Testing + iteration        | 2-3 days       |
| **Total**                  | **~1.5 weeks** |

---

## Related Documents

- [Original Strategy: Fine-Tuning Approaches](../Archive/image-generation-strategy.md#fine-tuning-approaches-for-brand-training)
- [Original Strategy: Training Data Quality](../Archive/image-generation-strategy.md#7-training-data-quality--volume)
- [01-commands.md](./01-commands.md) — Command patterns
