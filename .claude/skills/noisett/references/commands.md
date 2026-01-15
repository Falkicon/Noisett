# Noisett Commands Reference

Complete reference for all 25 commands.

## Core Commands

### asset.generate

Generate images from text prompt.

```bash
noisett asset.generate '{"prompt": "cloud computing concept", "asset_type": "product"}'
```

**Input Schema:**
```python
class GenerateInput(BaseModel):
    prompt: str                    # Text description
    asset_type: str = "product"    # icon, product, logo, premium
    count: int = 1                 # Number of images (1-4)
    style: str | None = None       # Optional style override
```

**Output:** `CommandResult` with `job_id` for polling.

### asset.types

List available asset types and their characteristics.

```bash
noisett asset.types '{}'
```

**Output:** List of asset types with descriptions, recommended sizes.

### job.status

Get generation job status and progress.

```bash
noisett job.status '{"job_id": "abc-123"}'
```

**Statuses:** `pending`, `running`, `completed`, `failed`, `cancelled`

### job.cancel

Cancel a running generation job.

```bash
noisett job.cancel '{"job_id": "abc-123"}'
```

### job.list

List user's recent jobs.

```bash
noisett job.list '{"limit": 10}'
```

### model.list

List available models and their capabilities.

```bash
noisett model.list '{}'
```

### model.info

Get detailed model information including licensing.

```bash
noisett model.info '{"model_id": "flux-schnell"}'
```

## LoRA Training Commands

### lora.create

Create new LoRA training project.

```bash
noisett lora.create '{"name": "Xbox Style", "trigger_word": "xboxstyle"}'
```

**Input Schema:**
```python
class LoRACreateInput(BaseModel):
    name: str           # Human-readable name
    trigger_word: str   # Word to activate style in prompts
    description: str | None = None
```

### lora.upload-images

Upload training images with captions.

```bash
noisett lora.upload-images '{
  "lora_id": "lora_xxx",
  "images": [
    {"url": "https://...", "caption": "xbox controller in xboxstyle"},
    {"url": "https://...", "caption": "xbox logo in xboxstyle"}
  ]
}'
```

**Requirements:**
- 10-50 images recommended
- Captions must include trigger word
- Images should be high quality, consistent style

### lora.train

Start LoRA training job.

```bash
noisett lora.train '{"lora_id": "lora_xxx"}'
```

**Options:**
```python
class LoRATrainInput(BaseModel):
    lora_id: str
    steps: int = 1000           # Training steps
    learning_rate: float = 1e-4 # Learning rate
```

### lora.status

Get training status and progress.

```bash
noisett lora.status '{"lora_id": "lora_xxx"}'
```

**Output:** Progress percentage, estimated time, current step.

### lora.list

List all LoRA projects.

```bash
noisett lora.list '{}'
```

### lora.activate

Activate or deactivate a LoRA for generation.

```bash
noisett lora.activate '{"lora_id": "lora_xxx", "active": true}'
```

### lora.delete

Delete a LoRA project and its weights.

```bash
noisett lora.delete '{"lora_id": "lora_xxx"}'
```

## Quality Pipeline Commands

### quality.presets

List available quality presets.

```bash
noisett quality.presets '{}'
```

**Presets:** `fast`, `balanced`, `quality`, `premium`

### refine

Apply img2img refinement pass.

```bash
noisett refine '{"image_url": "...", "strength": 0.3}'
```

**Input Schema:**
```python
class RefineInput(BaseModel):
    image_url: str
    strength: float = 0.3    # 0.1-0.5 recommended
    prompt: str | None = None  # Optional guidance
```

### upscale

Upscale image 2x or 4x.

```bash
noisett upscale '{"image_url": "...", "scale": 4}'
```

**Options:** `scale: 2` or `scale: 4`

### variations

Generate variations from source image.

```bash
noisett variations '{"image_url": "...", "count": 4}'
```

### post-process

Apply post-processing effects.

```bash
noisett post-process '{
  "image_url": "...",
  "sharpen": 0.5,
  "color_correct": true,
  "format": "png"
}'
```

**Options:**
```python
class PostProcessInput(BaseModel):
    image_url: str
    sharpen: float = 0.0       # 0.0-1.0
    color_correct: bool = False
    format: str = "png"        # png, jpg, webp
```

## History & Favorites Commands

### history.list

List user's generation history.

```bash
noisett history.list '{"limit": 50}'
```

### history.get

Get specific generation details.

```bash
noisett history.get '{"generation_id": "gen_xxx"}'
```

### history.delete

Delete generation from history.

```bash
noisett history.delete '{"generation_id": "gen_xxx"}'
```

### favorites.add

Add generation to favorites.

```bash
noisett favorites.add '{"generation_id": "gen_xxx", "prompt": "cloud computing concept"}'
```

### favorites.list

List user's favorite generations.

```bash
noisett favorites.list '{}'
```

### favorites.remove

Remove from favorites.

```bash
noisett favorites.remove '{"generation_id": "gen_xxx"}'
```

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_INPUT` | Malformed JSON or missing required field |
| `JOB_NOT_FOUND` | Job ID does not exist |
| `MODEL_NOT_FOUND` | Requested model unavailable |
| `LORA_NOT_FOUND` | LoRA project not found |
| `TRAINING_FAILED` | LoRA training error |
| `GENERATION_FAILED` | Image generation error |
| `RATE_LIMITED` | Too many requests |
| `BACKEND_ERROR` | ML backend unavailable |
