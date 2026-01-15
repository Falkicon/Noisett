---
name: noisett
description: >
  AI Brand Asset Generator with 25 commands for image generation, LoRA training,
  quality pipeline, and history management. Built with AFD principles.
version: "0.9.1"
category: core
triggers:
  - noisett
  - asset generator
  - image generation
  - LoRA training
  - quality pipeline
  - Fireworks
  - FLUX
---

# Noisett - AI Brand Asset Generator

Generate on-brand illustrations and icons using AI with Agent-First Development patterns.

## Capabilities

1. **Asset Generation** — Generate images from text prompts with brand alignment
2. **LoRA Training** — Train custom styles for brand consistency
3. **Quality Pipeline** — Refine, upscale, and post-process images
4. **History & Favorites** — Track and manage generated assets

## Routing Logic

| Request type | Load reference |
|--------------|----------------|
| Command schemas, CLI usage | [references/commands.md](references/commands.md) |
| ML backends, model selection | [references/ml-backends.md](references/ml-backends.md) |
| Azure deployment, CI/CD | [references/deployment.md](references/deployment.md) |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SURFACES (Thin Wrappers)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   VS Code /     │  │   Web UI        │  │   Figma Plugin          │  │
│  │   Cursor (MCP)  │  │   (Vanilla JS)  │  │   (v2)                  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬────────────┘  │
│           │ MCP (stdio)        │ REST API               │ REST API      │
│           └────────────────────┼────────────────────────┘               │
│                                ▼                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                        COMMAND LAYER (Source of Truth)                   │
│                    Python + FastMCP + Pydantic (25 Commands)             │
│  asset.* │ job.* │ model.* │ lora.* │ quality.* │ history.* │ favorites.* │
├─────────────────────────────────────────────────────────────────────────┤
│                           ML INFERENCE LAYER                             │
│          Mock | HuggingFace | Fireworks.ai (FLUX) | Replicate            │
└─────────────────────────────────────────────────────────────────────────┘
```

## Command Categories

| Category | Commands | Purpose |
|----------|----------|---------|
| `asset.*` | 2 | Image generation |
| `job.*` | 3 | Job management |
| `model.*` | 2 | Model discovery |
| `lora.*` | 7 | Custom style training |
| `quality.*` | 5 | Image refinement |
| `history.*` | 3 | Generation history |
| `favorites.*` | 3 | Saved generations |

## Quick CLI Examples

```bash
# Generate images
noisett asset.generate '{"prompt": "cloud computing concept", "asset_type": "product"}'

# LoRA Training workflow
noisett lora.create '{"name": "Xbox Style", "trigger_word": "xboxstyle"}'
noisett lora.upload-images '{"lora_id": "lora_xxx", "images": [...]}'
noisett lora.train '{"lora_id": "lora_xxx"}'

# Quality pipeline
noisett upscale '{"image_url": "...", "scale": 4}'
noisett refine '{"image_url": "...", "strength": 0.3}'
```

## CommandResult Pattern

All commands return structured results:

```python
{
  "success": true,
  "data": {...},
  "reasoning": "Started generation of 4 product illustrations",
  "confidence": 0.95,
  "suggestions": ["Try 'premium' for marketing-grade quality"]
}
```

## AFD Development Workflow

```
1. DEFINE   → Create command with Pydantic schema
2. VALIDATE → Test via CLI: noisett <command> '<json>'
3. SURFACE  → Build UI that calls command
```

**The Honesty Check:** If it can't be done via CLI, the architecture is wrong.

## Source Locations

```
src/
├── commands/           # Command definitions
│   ├── asset.py        # asset.generate, asset.types
│   ├── job.py          # job.status, job.cancel, job.list
│   ├── model.py        # model.list, model.info
│   ├── lora.py         # lora.* (7 commands)
│   ├── quality.py      # quality.* (5 commands)
│   ├── history.py      # history.* (3 commands)
│   └── favorites.py    # favorites.* (3 commands)
├── core/               # Shared types (CommandResult, errors)
├── ml/                 # ML backends
└── server/
    ├── mcp.py          # FastMCP server
    └── api.py          # FastAPI REST server
```

## When to Escalate

- Custom ML backend integration
- LoRA training infrastructure (GPU requirements)
- Azure deployment troubleshooting
