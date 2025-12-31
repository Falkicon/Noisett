# Command Definitions

Complete command specifications for Noisett, following AFD principles. All commands are defined with Pydantic schemas and must pass CLI validation before UI implementation.

---

## Command Response Schema

All commands return a `CommandResult` with UX-enabling metadata:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from enum import Enum

T = TypeVar('T')

class CommandError(BaseModel):
    """Structured error with recovery guidance."""
    code: str
    message: str
    suggestion: Optional[str] = None

class Warning(BaseModel):
    """Non-fatal warning about side effects."""
    code: str
    message: str

class CommandResult(BaseModel, Generic[T]):
    """Standard response for all commands."""
    success: bool
    data: Optional[T] = None
    error: Optional[CommandError] = None
    
    # UX-enabling fields
    reasoning: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    warnings: Optional[List[Warning]] = None
    suggestions: Optional[List[str]] = None
```

### Helper Functions

```python
def success(
    data: T,
    reasoning: Optional[str] = None,
    confidence: Optional[float] = None,
    warnings: Optional[List[Warning]] = None,
    suggestions: Optional[List[str]] = None
) -> CommandResult[T]:
    """Create a successful command result."""
    return CommandResult(
        success=True,
        data=data,
        reasoning=reasoning,
        confidence=confidence,
        warnings=warnings,
        suggestions=suggestions
    )

def error(
    code: str,
    message: str,
    suggestion: Optional[str] = None
) -> CommandResult:
    """Create an error command result."""
    return CommandResult(
        success=False,
        error=CommandError(code=code, message=message, suggestion=suggestion)
    )
```

---

## Standard Error Codes

| Code | When to Use |
|------|-------------|
| `NOT_FOUND` | Resource doesn't exist |
| `VALIDATION_ERROR` | Input fails schema validation |
| `FORBIDDEN` | User lacks permission |
| `RATE_LIMITED` | Too many requests |
| `MODEL_UNAVAILABLE` | ML model not loaded/available |
| `GENERATION_FAILED` | Image generation failed |
| `JOB_NOT_FOUND` | Job ID doesn't exist |
| `JOB_ALREADY_COMPLETE` | Can't cancel completed job |
| `INTERNAL_ERROR` | Unexpected server error |

---

## Domain Types

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AssetType(str, Enum):
    """Available asset types for generation."""
    ICONS = "icons"
    PRODUCT = "product"
    LOGO = "logo"
    PREMIUM = "premium"

class ModelId(str, Enum):
    """Available image generation models."""
    HIDREAM = "hidream"
    FLUX = "flux"
    SD35 = "sd35"

class JobStatus(str, Enum):
    """Generation job status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class QualityPreset(str, Enum):
    """Generation quality presets."""
    DRAFT = "draft"       # Fast, lower quality
    STANDARD = "standard" # Balanced
    HIGH = "high"         # Slower, higher quality

class GeneratedImage(BaseModel):
    """A single generated image."""
    index: int
    url: str
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None

class Job(BaseModel):
    """Image generation job."""
    id: str
    status: JobStatus
    prompt: str
    asset_type: AssetType
    model: ModelId
    quality: QualityPreset
    count: int
    progress: float = Field(default=0, ge=0, le=100)
    images: List[GeneratedImage] = []
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class Model(BaseModel):
    """Image generation model info."""
    id: ModelId
    name: str
    description: str
    license: str
    commercial_ok: bool
    available: bool
    default_steps: int
    default_guidance: float

class AssetTypeInfo(BaseModel):
    """Asset type configuration."""
    id: AssetType
    name: str
    description: str
    prompt_template: str
    negative_prompt: str
    recommended_for: List[str]
```

---

## Commands

### `asset.generate`

Generate images from a text prompt.

**Input Schema:**

```python
class AssetGenerateInput(BaseModel):
    """Input for asset.generate command."""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Text description of the image to generate"
    )
    asset_type: AssetType = Field(
        default=AssetType.PRODUCT,
        description="Type of asset to generate"
    )
    model: ModelId = Field(
        default=ModelId.HIDREAM,
        description="Model to use for generation"
    )
    quality: QualityPreset = Field(
        default=QualityPreset.STANDARD,
        description="Quality preset affecting speed vs quality"
    )
    count: int = Field(
        default=4,
        ge=1,
        le=4,
        description="Number of variations to generate"
    )
```

**Output Schema:**

```python
class AssetGenerateOutput(BaseModel):
    """Output for asset.generate command."""
    job: Job
    estimated_seconds: int
```

**Example:**

```bash
# CLI
noisett asset.generate '{
  "prompt": "A person collaborating with AI on a creative project",
  "asset_type": "product",
  "count": 4
}'

# Response
{
  "success": true,
  "data": {
    "job": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "queued",
      "prompt": "A person collaborating with AI...",
      "asset_type": "product",
      "model": "hidream",
      "quality": "standard",
      "count": 4,
      "progress": 0,
      "images": [],
      "created_at": "2026-01-15T10:30:00Z"
    },
    "estimated_seconds": 30
  },
  "reasoning": "Started generation of 4 product illustrations using HiDream"
}
```

**Error Cases:**

| Error Code | Condition |
|------------|-----------|
| `VALIDATION_ERROR` | Prompt empty or too long |
| `MODEL_UNAVAILABLE` | Selected model not loaded |
| `RATE_LIMITED` | Too many concurrent requests |

---

### `asset.types`

List available asset types and their configurations.

**Input Schema:**

```python
class AssetTypesInput(BaseModel):
    """Input for asset.types command (no parameters)."""
    pass
```

**Output Schema:**

```python
class AssetTypesOutput(BaseModel):
    """Output for asset.types command."""
    types: List[AssetTypeInfo]
```

**Example:**

```bash
# CLI
noisett asset.types '{}'

# Response
{
  "success": true,
  "data": {
    "types": [
      {
        "id": "icons",
        "name": "Icons (Fluent 2)",
        "description": "Minimal vector-style icons for UI",
        "prompt_template": "{subject}, Fluent 2 design icon, minimal vector style...",
        "negative_prompt": "photorealistic, 3d render, complex...",
        "recommended_for": ["UI elements", "app icons", "buttons"]
      },
      {
        "id": "product",
        "name": "Product Illustrations",
        "description": "Clean illustrations for product pages and docs",
        "prompt_template": "{subject}, product illustration style...",
        "negative_prompt": "cluttered, amateur...",
        "recommended_for": ["documentation", "product pages", "feature callouts"]
      },
      {
        "id": "logo",
        "name": "Logo Illustrations",
        "description": "Simple iconic illustrations for branding",
        "prompt_template": "{subject}, simple iconic illustration...",
        "negative_prompt": "complex, detailed...",
        "recommended_for": ["app tiles", "feature icons", "badges"]
      },
      {
        "id": "premium",
        "name": "Premium Illustrations",
        "description": "Rich marketing-grade illustrations",
        "prompt_template": "{subject}, premium editorial illustration...",
        "negative_prompt": "amateur, stock photo...",
        "recommended_for": ["marketing", "hero images", "campaigns"]
      }
    ]
  },
  "reasoning": "4 asset types available"
}
```

---

### `job.status`

Get the current status of a generation job.

**Input Schema:**

```python
class JobStatusInput(BaseModel):
    """Input for job.status command."""
    job_id: str = Field(..., description="Job ID to check")
```

**Output Schema:**

```python
class JobStatusOutput(BaseModel):
    """Output for job.status command."""
    job: Job
```

**Example:**

```bash
# CLI (in progress)
noisett job.status '{"job_id": "550e8400-e29b-41d4-a716-446655440000"}'

# Response (processing)
{
  "success": true,
  "data": {
    "job": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "processing",
      "prompt": "A person collaborating with AI...",
      "progress": 65,
      "images": []
    }
  },
  "reasoning": "Generation 65% complete, 2 of 4 images done"
}

# Response (complete)
{
  "success": true,
  "data": {
    "job": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "complete",
      "progress": 100,
      "images": [
        {"index": 0, "url": "https://storage.blob.../img0.png", "seed": 12345},
        {"index": 1, "url": "https://storage.blob.../img1.png", "seed": 67890},
        {"index": 2, "url": "https://storage.blob.../img2.png", "seed": 11111},
        {"index": 3, "url": "https://storage.blob.../img3.png", "seed": 22222}
      ],
      "completed_at": "2026-01-15T10:30:32Z"
    }
  },
  "reasoning": "Generation complete, 4 images ready for download"
}
```

**Error Cases:**

| Error Code | Condition |
|------------|-----------|
| `JOB_NOT_FOUND` | Job ID doesn't exist |

---

### `job.cancel`

Cancel a queued or in-progress job.

**Input Schema:**

```python
class JobCancelInput(BaseModel):
    """Input for job.cancel command."""
    job_id: str = Field(..., description="Job ID to cancel")
```

**Output Schema:**

```python
class JobCancelOutput(BaseModel):
    """Output for job.cancel command."""
    job: Job
```

**Example:**

```bash
# CLI
noisett job.cancel '{"job_id": "550e8400-e29b-41d4-a716-446655440000"}'

# Response
{
  "success": true,
  "data": {
    "job": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "cancelled"
    }
  },
  "reasoning": "Job cancelled, no images were completed"
}
```

**Error Cases:**

| Error Code | Condition |
|------------|-----------|
| `JOB_NOT_FOUND` | Job ID doesn't exist |
| `JOB_ALREADY_COMPLETE` | Job already finished |

---

### `job.list`

List recent generation jobs for the current user.

**Input Schema:**

```python
class JobListInput(BaseModel):
    """Input for job.list command."""
    limit: int = Field(default=20, ge=1, le=100, description="Max jobs to return")
    status: Optional[JobStatus] = Field(default=None, description="Filter by status")
```

**Output Schema:**

```python
class JobListOutput(BaseModel):
    """Output for job.list command."""
    jobs: List[Job]
    total: int
```

**Example:**

```bash
# CLI
noisett job.list '{"limit": 10}'

# Response
{
  "success": true,
  "data": {
    "jobs": [
      {"id": "...", "status": "complete", "prompt": "...", "created_at": "..."},
      {"id": "...", "status": "processing", "prompt": "...", "created_at": "..."}
    ],
    "total": 2
  },
  "reasoning": "Found 2 recent jobs"
}
```

---

### `model.list`

List available image generation models.

**Input Schema:**

```python
class ModelListInput(BaseModel):
    """Input for model.list command (no parameters)."""
    pass
```

**Output Schema:**

```python
class ModelListOutput(BaseModel):
    """Output for model.list command."""
    models: List[Model]
    default: ModelId
```

**Example:**

```bash
# CLI
noisett model.list '{}'

# Response
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "hidream",
        "name": "HiDream-I1",
        "description": "High quality diffusion model with Apache 2.0 license",
        "license": "Apache 2.0",
        "commercial_ok": true,
        "available": true,
        "default_steps": 28,
        "default_guidance": 7.5
      },
      {
        "id": "flux",
        "name": "FLUX.1-dev",
        "description": "Excellent prompt adherence, non-commercial license",
        "license": "FLUX-dev (non-commercial)",
        "commercial_ok": false,
        "available": true,
        "default_steps": 28,
        "default_guidance": 3.5
      }
    ],
    "default": "hidream"
  },
  "reasoning": "2 models available, HiDream recommended for commercial use"
}
```

---

### `model.info`

Get detailed information about a specific model.

**Input Schema:**

```python
class ModelInfoInput(BaseModel):
    """Input for model.info command."""
    model_id: ModelId = Field(..., description="Model to get info for")
```

**Output Schema:**

```python
class ModelInfoOutput(BaseModel):
    """Output for model.info command."""
    model: Model
    lora_available: bool
    vram_required_gb: float
    estimated_time_per_image: int  # seconds
```

**Example:**

```bash
# CLI
noisett model.info '{"model_id": "hidream"}'

# Response
{
  "success": true,
  "data": {
    "model": {
      "id": "hidream",
      "name": "HiDream-I1",
      "license": "Apache 2.0",
      "commercial_ok": true,
      "available": true
    },
    "lora_available": true,
    "vram_required_gb": 16,
    "estimated_time_per_image": 7
  },
  "reasoning": "HiDream is ready with brand LoRA loaded"
}
```

**Error Cases:**

| Error Code | Condition |
|------------|-----------|
| `NOT_FOUND` | Model ID doesn't exist |

---

## CLI Usage

The CLI wraps all commands for testing:

```bash
# General syntax
noisett <command> '<json_input>'

# Examples
noisett asset.generate '{"prompt": "cloud computing concept"}'
noisett job.status '{"job_id": "abc-123"}'
noisett model.list '{}'

# With pretty output
noisett asset.types '{}' --pretty

# Help
noisett --help
noisett asset.generate --help
```

---

## Validation Checklist

Before building any UI surface, verify each command:

- [ ] `asset.generate` — Can start generation via CLI
- [ ] `asset.types` — Returns all asset type configs
- [ ] `job.status` — Shows progress and completed images
- [ ] `job.cancel` — Successfully cancels running job
- [ ] `job.list` — Returns user's recent jobs
- [ ] `model.list` — Lists available models with licensing
- [ ] `model.info` — Returns model details

**Only proceed to UI implementation after all commands pass CLI validation.**
