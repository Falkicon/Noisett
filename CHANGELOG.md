# Changelog

All notable changes to Noisett will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned

- Microsoft Entra ID authentication
- Azure Blob storage integration
- Application Insights monitoring

---

## [0.9.0] - 2025-12-31

### Added

- **Figma Plugin** (Phase 7 Complete ✅)

  - TypeScript-based Figma plugin for in-workflow image generation
  - `figma-plugin/src/code.ts` — Main plugin code (Figma API, image insertion)
  - `figma-plugin/src/ui.html` — Plugin panel with prompt input, asset selector, results grid
  - `figma-plugin/src/ui.ts` — UI logic and state management
  - `figma-plugin/src/api.ts` — Backend API client with polling
  - `figma-plugin/src/types.ts` — Shared TypeScript types

- **Plugin Features**

  - Generate images directly in Figma
  - 4 asset types: icons, product, logo, premium
  - One-click image insertion at viewport center
  - Progress indicator with real-time polling
  - Settings persistence via Figma clientStorage
  - Keyboard shortcut: Cmd/Ctrl+Enter to generate

- **Build System**
  - Custom esbuild-based build script
  - Inlines UI JavaScript into HTML (Figma requirement)
  - Development watch mode: `pnpm dev`
  - Production build: `pnpm build`

### Changed

- Total surfaces: CLI, MCP, REST API, Web UI, **Figma Plugin**
- Updated AGENTS.md with Phase 7 completion and plugin structure

### Technical Notes

- Plugin calls existing REST API endpoints (`/api/generate`, `/api/jobs/{id}`)
- No backend changes required — AFD architecture validated
- Plugin follows Figma design language (Inter font, 8px grid, dark theme)

---

## [0.8.0] - 2025-12-31

### Added

- **Quality Pipeline** (Phase 6 Complete ✅)

  - 5 new quality commands for multi-stage image refinement
  - `quality.presets` — List available quality presets (DRAFT, STANDARD, HIGH)
  - `refine` — Apply img2img refinement pass with configurable denoise
  - `upscale` — Upscale images 2x/4x using Real-ESRGAN or SUPIR
  - `variations` — Generate 1-8 variations from a source image
  - `post-process` — Sharpen, color correct, and format conversion

- **Quality Types** (`src/core/types.py`)

  - `UpscaleModel` enum (REAL_ESRGAN, SUPIR)
  - `OutputFormat` enum (PNG, WEBP, JPEG)
  - `QualityPresetInfo`, `QUALITY_PRESET_CONFIGS` dict
  - `RefinedImage`, `UpscaledImage`, `ImageVariation`, `PostProcessedImage` models

- **Quality Error Codes** (`src/core/errors.py`)

  - 6 new error codes: IMAGE_URL_INVALID, IMAGE_FETCH_FAILED, REFINE_FAILED, UPSCALE_FAILED, VARIATIONS_FAILED, POST_PROCESS_FAILED

- **21 new tests** in `tests/test_quality.py`

### Changed

- CLI now has 19 commands total (7 asset/job/model + 7 lora + 5 quality)
- Total test count: 72 tests (71 passing + 1 expected degraded health)
- Updated AGENTS.md with Phase 6 completion status

---

## [0.7.0] - 2025-12-31

### Added

- **LoRA Training Pipeline** (Phase 5 Complete ✅)

  - 7 new `lora.*` commands for custom model training
  - `lora.create` — Create new training project with trigger word
  - `lora.upload-images` — Upload training images with captions
  - `lora.train` — Start training (MVP: simulates completion)
  - `lora.status` — Get training progress and details
  - `lora.list` — List all LoRA projects with filtering
  - `lora.activate` — Toggle LoRA activation for inference
  - `lora.delete` — Remove LoRA projects (blocked if active)

- **LoRA Types** (`src/core/types.py`)

  - `LoraStatus` enum (CREATED, UPLOADING, READY_TO_TRAIN, TRAINING, COMPLETED, FAILED)
  - `BaseModelType` enum (FLUX, SDXL)
  - `Lora`, `TrainingImage`, `LoraInfo` models

- **LoRA Error Codes** (`src/core/errors.py`)
  - 11 new error codes with templates and recovery suggestions

### Changed

- CLI now has 14 commands total (7 asset/job/model + 7 lora)
- Updated AGENTS.md with Phase 5 completion status

### Fixed

- Fixed datetime serialization in CLI output (`mode="json"`)
- Fixed `datetime.utcnow()` deprecation warnings with `_now()` helper

### Technical

- 22 new LoRA tests (51 total tests, 50 passing + 1 expected degraded)
- In-memory storage pattern for MVP (ready for database backend)

---

## [0.6.3] - 2025-01-01

### Added

- **Fireworks.ai Backend** - Real AI image generation with FLUX models
  - `FireworksGenerator` class using Fireworks REST API
  - FLUX-1 Schnell FP8 model for fast, cost-effective generation (~$0.003/image)
  - Support for multiple image sizes (512x512 draft, 1024x1024 standard/high)

### Changed

- Updated ML_BACKEND default from `mock` to `fireworks` for production
- AGENTS.md documentation updated with Fireworks integration details

### Technical

- Using Fireworks `/workflows` API endpoint (not SDK's `/image_generation`)
- Models available: `flux-1-schnell-fp8` (fast), `flux-1-dev-fp8` (high quality)
- Images saved as JPEG to temp directory with seed-based filenames

---

## [0.6.2] - 2025-12-31

### Fixed

- Fixed JobStatus enum value (`COMPLETE` not `COMPLETED`)
- Background job processing now correctly marks jobs as complete

---

## [0.6.1] - 2025-12-31

### Added

- Background job processing in FastAPI (`process_job` async function)
- Jobs now automatically transition from QUEUED → PROCESSING → COMPLETE

### Fixed

- Fixed issue where jobs were created but never processed
- Generation no longer stuck on "Generating..." indefinitely

---

## [0.6.0] - 2025-12-31

### Added

- **Deployment Infrastructure** (Phase 6 Complete ✅)
  - Dockerfile with PyTorch CUDA base image
  - requirements.txt with production dependencies
  - GitHub Actions CI/CD workflow (`deploy.yml`)
  - Azure Container Apps YAML configuration
  - Infrastructure setup script (`setup-azure.sh`)

### Deployed

- **Live URL:** https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io/
- **Container Registry:** noisettacr.azurecr.io
- **Container App:** noisett (East US, CPU-only)
- **Resource Group:** noisett-rg
- **Backend:** ML_BACKEND=mock (placeholder images for testing)

### Changed

- Enhanced `/health` endpoint with GPU detection
- Health endpoint now returns version and environment

### Files Added

- `Dockerfile` - Production container with CUDA support
- `requirements.txt` - Pinned production dependencies
- `.github/workflows/deploy.yml` - CI/CD pipeline
- `infrastructure/container-app.yaml` - Azure Container Apps config
- `infrastructure/setup-azure.sh` - Azure resource provisioning script

---

## [0.5.0] - 2025-12-30

### Added

- **Web UI** (Phase 5 complete)
  - Vanilla JS frontend with no frameworks, no build step
  - Fluent 2 inspired design tokens (`--color-primary: #0078D4`)
  - Input section with prompt, asset type, quality selectors
  - Loading section with progress bar and cancel button
  - Results section with image grid
  - Error section with recovery suggestions
  - Responsive design with mobile breakpoints
  - Reduced motion support for accessibility

### Files Added

- `web/index.html` - SPA shell with semantic HTML
- `web/styles.css` - Design tokens and component styles
- `web/api.js` - Thin API client over fetch
- `web/app.js` - Application logic and state management

---

## [0.4.0] - 2025-12-29

### Added

- **REST API** (Phase 4 complete)
  - FastAPI server with 8 endpoints
  - Static file serving for Web UI
  - CORS configuration for development
  - Health check endpoint

### Endpoints

| Endpoint                 | Method | Description      |
| ------------------------ | ------ | ---------------- |
| `/health`                | GET    | Health check     |
| `/api/generate`          | POST   | Generate images  |
| `/api/asset-types`       | GET    | List asset types |
| `/api/jobs/{job_id}`     | GET    | Get job status   |
| `/api/jobs/{job_id}`     | DELETE | Cancel job       |
| `/api/jobs`              | GET    | List user's jobs |
| `/api/models`            | GET    | List models      |
| `/api/models/{model_id}` | GET    | Get model info   |

### Tests

- Added 14 REST API tests (`test_api.py`)
- Total test count: 29

---

## [0.3.0] - 2025-12-28

### Added

- **ML Pipeline** (Phase 3 complete)
  - `MockGenerator` - Instant placeholder images for testing
  - `HuggingFaceGenerator` - FLUX model via HuggingFace Inference API
  - `ReplicateGenerator` - Production-quality via Replicate API
  - Backend selection via environment variable

### Backend Options

| Backend       | Cost         | Speed         | Use Case                 |
| ------------- | ------------ | ------------- | ------------------------ |
| `mock`        | Free         | Instant       | Testing, development     |
| `huggingface` | Free tier    | ~15-30s/image | Testing with real images |
| `replicate`   | ~$0.03/image | ~10-15s/image | Production quality       |

---

## [0.2.0] - 2025-12-27

### Added

- **MCP Server** (Phase 2 complete)
  - FastMCP integration (official Python SDK v2.14.1)
  - 7 tools exposed to AI agents
  - VS Code/Cursor configuration example

### Tools

- `asset_generate` - Generate brand-aligned images
- `asset_types` - List available asset types
- `job_status` - Get job status
- `job_cancel` - Cancel running job
- `job_list` - List recent jobs
- `model_list` - List available models
- `model_info` - Get model details

---

## [0.1.0] - 2025-12-26

### Added

- **Commands** (Phase 1 complete)
  - 7 commands with Pydantic schemas
  - CLI entry point (`noisett`)
  - CommandResult schema with UX-enabling fields
  - Standard error codes with recovery suggestions

### Commands

- `asset.generate` - Generate images from prompt
- `asset.types` - List asset types
- `job.status` - Get job status
- `job.cancel` - Cancel job
- `job.list` - List jobs
- `model.list` - List models
- `model.info` - Get model info

### Tests

- 15 core command tests

---

## Architecture

Noisett follows **Agent-First Development (AFD)** principles:

```
SURFACES (UI, MCP, CLI)
        │
        ▼
COMMAND LAYER (Source of Truth)
        │
        ▼
ML INFERENCE LAYER
```

All functionality flows through the command layer. UI and MCP are thin wrappers.
