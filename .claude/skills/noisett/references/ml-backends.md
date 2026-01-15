# ML Backends Reference

Noisett supports multiple ML inference backends for flexibility and cost optimization.

## Available Backends

| Backend | Models | Cost | Speed | Quality |
|---------|--------|------|-------|---------|
| Mock | N/A | Free | Instant | Placeholder |
| Fireworks.ai | FLUX Schnell, Pro | ~$0.003/img | Fast | High |
| HuggingFace | SDXL, FLUX | API costs | Medium | High |
| Replicate | FLUX, SD | ~$0.01/img | Medium | High |

## Configuration

Set via environment variable:

```bash
export ML_BACKEND=fireworks  # Default for production
export ML_BACKEND=mock       # For development/testing
export ML_BACKEND=huggingface
export ML_BACKEND=replicate
```

## Fireworks.ai (Recommended)

Production backend using FLUX models.

**Setup:**
```bash
export FIREWORKS_API_KEY=your_api_key
export ML_BACKEND=fireworks
```

**Models:**
- `flux-schnell` — Fast generation (~2s), good quality
- `flux-pro` — Higher quality (~5s), better prompt following

**Pricing:** ~$0.003 per image

## Mock Backend

For development and testing without API costs.

**Setup:**
```bash
export ML_BACKEND=mock
```

**Behavior:**
- Returns placeholder images
- Simulates job queue with delays
- All commands work without external calls

## HuggingFace Inference API

Uses HuggingFace's hosted inference.

**Setup:**
```bash
export HF_TOKEN=your_token
export ML_BACKEND=huggingface
```

**Models:**
- `stabilityai/stable-diffusion-xl-base-1.0`
- `black-forest-labs/FLUX.1-schnell`

## Replicate

Pay-per-use cloud inference.

**Setup:**
```bash
export REPLICATE_API_TOKEN=your_token
export ML_BACKEND=replicate
```

**Models:**
- Various FLUX and Stable Diffusion versions

## Backend Selection Logic

```python
# src/ml/__init__.py
def get_generator():
    backend = os.getenv("ML_BACKEND", "mock")

    match backend:
        case "mock":
            return MockGenerator()
        case "fireworks":
            return FireworksGenerator()
        case "huggingface":
            return HuggingFaceGenerator()
        case "replicate":
            return ReplicateGenerator()
```

## Adding New Backends

Implement the `Generator` protocol:

```python
class Generator(Protocol):
    async def generate(
        self,
        prompt: str,
        asset_type: str,
        count: int = 1,
    ) -> list[GeneratedImage]:
        ...

    async def get_models(self) -> list[Model]:
        ...
```

## Cost Comparison

For 1000 images:

| Backend | Cost | Notes |
|---------|------|-------|
| Mock | $0 | Development only |
| Fireworks | ~$3 | Best value |
| HuggingFace | ~$5-10 | Varies by model |
| Replicate | ~$10 | Most expensive |
