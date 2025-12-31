# Changelog

All notable changes to Noisett will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned

- Microsoft Entra ID authentication
- Azure Blob storage integration
- Application Insights monitoring
- GPU quota approval for real inference

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
