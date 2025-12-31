# Noisett - AI Agent Context

> **Project:** Noisett (Brand Asset Generator)  
> **Architecture:** Agent-First Development (AFD)  
> **Status:** Phases 1-8 Complete ✅ | Code Review Fixes Applied | **v0.9.1-dev**  
> **Live URL:** https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io/

---

## Implementation Progress

### Completed (v0.9.x)

| Phase | Component        | Status  | Notes                                      |
| ----- | ---------------- | ------- | ------------------------------------------ |
| 1     | Commands         | ✅ Done | 7 asset/job commands with Pydantic         |
| 2     | MCP Server       | ✅ Done | FastMCP integration, 12 tools              |
| 3     | ML Pipeline      | ✅ Done | Mock, HuggingFace, **Fireworks (FLUX)**    |
| 4     | Deployment       | ✅ Done | Azure Container Apps, CI/CD, REST API      |
| 5     | LoRA Training    | ✅ Done | 7 lora.\* commands (MVP simulation)        |
| 6     | Quality Pipeline | ✅ Done | 5 quality commands (refine, upscale, etc)  |
| 7     | Figma Plugin     | ✅ Done | TypeScript plugin, esbuild, REST API       |
| 8     | Auth & Storage   | ✅ Done | SQLite storage, history/favorites commands |

**Tests:** 100 passing (all tests)

---

## Live Deployment

| Resource           | Value                                                                |
| ------------------ | -------------------------------------------------------------------- |
| **Live URL**       | https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io/ |
| **Container App**  | noisett (East US)                                                    |
| **Registry**       | noisettacr.azurecr.io                                                |
| **Resource Group** | noisett-rg                                                           |
| **Version**        | v0.6.3                                                               |
| **Backend**        | ML_BACKEND=fireworks (real FLUX inference via Fireworks.ai)          |

> **Note:** Now using Fireworks.ai for real AI image generation with FLUX models (~$0.003/image).

---

## What is Noisett?

Noisett is an internal AI image generation tool that creates on-brand illustrations and icons. Built with **Agent-First Development** principles—commands are the source of truth, validated via CLI before any UI surface is built.

**Key Capabilities:**

- Generate brand-aligned images from text prompts
- Support for multiple asset types (icons, product illustrations, logos, premium)
- MCP integration for VS Code/Cursor agent workflows
- Web UI for non-technical users
- Figma plugin (v2) for in-workflow generation

---

## Architecture at a Glance

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

---

## Quick Start

### CLI (Primary Development Interface)

```bash
# Generate images
noisett asset.generate '{"prompt": "cloud computing concept", "asset_type": "product"}'

# Check job status
noisett job.status '{"job_id": "abc-123"}'

# List available models
noisett model.list '{}'

# LoRA Training workflow
noisett lora.create '{"name": "Xbox Style", "trigger_word": "xboxstyle"}'
noisett lora.upload-images '{"lora_id": "lora_xxx", "images": [{"url": "...", "caption": "..."}]}'
noisett lora.train '{"lora_id": "lora_xxx"}'
noisett lora.status '{"lora_id": "lora_xxx"}'
noisett lora.activate '{"lora_id": "lora_xxx"}'
noisett lora.list '{}'

# History and favorites
noisett history.list '{}'
noisett history.get '{"generation_id": "gen_xxx"}'
noisett history.delete '{"generation_id": "gen_xxx"}'
noisett favorites.add '{"generation_id": "gen_xxx", "prompt": "cloud computing concept"}'
noisett favorites.list '{}'
noisett favorites.remove '{"generation_id": "gen_xxx"}'
```

### MCP (VS Code/Cursor)

Configure in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "noisett": {
      "command": "python",
      "args": ["-m", "src.server.mcp"],
      "cwd": "D:/Github/Falkicon/Noisett"
    }
  }
}
```

---

## Core Commands

| Command          | Description                   | Mutation |
| ---------------- | ----------------------------- | -------- |
| `asset.generate` | Generate images from prompt   | Yes      |
| `asset.types`    | List available asset types    | No       |
| `job.status`     | Get generation job status     | No       |
| `job.cancel`     | Cancel a running job          | Yes      |
| `job.list`       | List user's recent jobs       | No       |
| `model.list`     | List available models         | No       |
| `model.info`     | Get model details + licensing | No       |

### LoRA Training Commands (Phase 5)

| Command              | Description                      | Mutation |
| -------------------- | -------------------------------- | -------- |
| `lora.create`        | Create new LoRA training project | Yes      |
| `lora.upload-images` | Upload training images           | Yes      |
| `lora.train`         | Start training job               | Yes      |
| `lora.status`        | Get training status/progress     | No       |
| `lora.list`          | List all LoRA projects           | No       |
| `lora.activate`      | Activate/deactivate LoRA         | Yes      |
| `lora.delete`        | Delete a LoRA project            | Yes      |

### Quality Pipeline Commands (Phase 6)

| Command           | Description                     | Mutation |
| ----------------- | ------------------------------- | -------- |
| `quality.presets` | List available quality presets  | No       |
| `refine`          | Apply refinement pass (img2img) | No       |
| `upscale`         | Upscale image 2x/4x             | No       |
| `variations`      | Generate variations from source | No       |
| `post-process`    | Sharpen, color correct, convert | No       |

### History & Favorites Commands (Phase 8)

| Command            | Description                      | Mutation |
| ------------------ | -------------------------------- | -------- |
| `history.list`     | List user's generation history   | No       |
| `history.get`      | Get specific generation details  | No       |
| `history.delete`   | Delete generation from history   | Yes      |
| `favorites.add`    | Add generation to favorites      | Yes      |
| `favorites.list`   | List user's favorite generations | No       |
| `favorites.remove` | Remove from favorites            | Yes      |

All commands return `CommandResult` with UX-enabling fields:

```python
{
  "success": true,
  "data": {...},
  "reasoning": "Started generation of 4 product illustrations",
  "confidence": 0.95,
  "suggestions": ["Try 'premium' for marketing-grade quality"]
}
```

---

## Tech Stack

| Layer       | Technology                             | Status         |
| ----------- | -------------------------------------- | -------------- |
| Commands    | Python + Pydantic                      | ✅ Implemented |
| MCP Server  | FastMCP (official Python SDK)          | ✅ Implemented |
| ML Backends | Mock, HuggingFace, Fireworks.ai (FLUX) | ✅ Implemented |
| REST API    | FastAPI                                | ✅ Implemented |
| Web UI      | Vanilla JS/HTML/CSS                    | ✅ Implemented |
| Compute     | Azure Container Apps (CPU)             | ✅ Deployed    |
| Registry    | Azure Container Registry               | ✅ Deployed    |
| Auth        | Microsoft Entra ID (JWT middleware)    | ✅ Implemented |
| Storage     | SQLite (local)                         | ✅ Implemented |

---

## Documentation

| Document                                                      | Description                               |
| ------------------------------------------------------------- | ----------------------------------------- |
| [CHANGELOG.md](./CHANGELOG.md)                                | Release history and changes               |
| [Strategy/00-overview.md](./Docs/Strategy/00-overview.md)     | Architecture and AFD principles           |
| [Strategy/01-commands.md](./Docs/Strategy/01-commands.md)     | Command definitions with Pydantic schemas |
| [Strategy/02-mcp-server.md](./Docs/Strategy/02-mcp-server.md) | FastMCP integration guide                 |
| [Strategy/03-web-ui.md](./Docs/Strategy/03-web-ui.md)         | Vanilla JS UI implementation              |
| [Strategy/04-deployment.md](./Docs/Strategy/04-deployment.md) | Azure deployment guide                    |

### Legacy Docs (Pre-AFD)

The `specs-*` folders contain earlier planning work. Strategy docs supersede them for implementation, but design specs remain useful for visual reference.

---

## Development Workflow

```
┌─────────────────────────────────────────────────┐
│  1. DEFINE                                      │
│  • Create command with Pydantic schema          │
│  • Define inputs, outputs, error codes          │
├─────────────────────────────────────────────────┤
│  2. VALIDATE                                    │
│  • Test via CLI: noisett <command> '<json>'     │
│  • ⛔ Do NOT proceed until CLI works            │
├─────────────────────────────────────────────────┤
│  3. SURFACE                                     │
│  • Build UI that calls command                  │
│  • Use metadata for UX (reasoning, confidence)  │
└─────────────────────────────────────────────────┘
```

### The Honesty Check

> "If it can't be done via CLI, the architecture is wrong."

Before building any UI:

- Can this action be performed via CLI?
- Does the CLI return all data the UI needs?
- Is the response schema complete?

---

## Project Structure

```
noisett/
├── AGENTS.md                    # This file
├── pyproject.toml               # Python project config
├── test_generate.py             # Quick test script
│
├── Docs/
│   ├── Strategy/                # AFD-first documentation
│   │   ├── 00-overview.md       # Architecture + principles
│   │   ├── 01-commands.md       # Command specifications
│   │   ├── 02-mcp-server.md     # MCP integration
│   │   ├── 03-web-ui.md         # Web UI design
│   │   └── 04-deployment.md     # Azure deployment
│   └── Archive/                 # Legacy specs (pre-AFD)
│
├── infrastructure/              # Azure deployment files ✅
│   ├── container-app.yaml       # Container Apps config
│   └── setup-azure.sh           # Provisioning script
│
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline ✅
│
├── Dockerfile                   # Production container ✅
├── requirements.txt             # Production dependencies ✅
│
├── src/
│   ├── __init__.py
│   ├── cli.py                   # CLI entry point ✅
│   │
│   ├── commands/                # Command definitions ✅
│   │   ├── __init__.py
│   │   ├── asset.py             # asset.generate, asset.types
│   │   ├── job.py               # job.status, job.cancel, job.list
│   │   └── model.py             # model.list, model.info
│   │
│   ├── core/                    # Shared types ✅
│   │   ├── __init__.py
│   │   ├── result.py            # CommandResult schema
│   │   ├── errors.py            # Error codes + templates
│   │   └── types.py             # Domain types (Job, Model, etc.)
│   │
│   ├── ml/                      # ML inference ✅
│   │   └── __init__.py          # Mock, HuggingFace, Replicate generators
│   │
│   └── server/
│       ├── __init__.py
│       ├── mcp.py               # FastMCP server ✅
│       └── api.py               # FastAPI REST server ✅
│
├── web/                         # Vanilla JS frontend ✅
│   ├── index.html               # Main HTML
│   ├── styles.css               # Design tokens + components
│   ├── api.js                   # API client
│   └── app.js                   # Application logic
│
├── figma-plugin/                # Figma plugin (v2) ✅
│   ├── manifest.json            # Plugin manifest
│   ├── package.json             # Dependencies (esbuild)
│   ├── build.js                 # Custom build script
│   ├── src/
│   │   ├── code.ts              # Main plugin code (Figma API)
│   │   ├── ui.html              # Plugin panel UI
│   │   ├── ui.ts                # UI logic
│   │   ├── api.ts               # Backend API client
│   │   └── types.ts             # TypeScript types
│   └── dist/                    # Built output (code.js, ui.html)
│
└── tests/                       # Test suite ✅
    ├── __init__.py
    ├── test_api.py              # 14 tests (REST API)
    ├── test_asset.py            # 5 tests
    ├── test_job.py              # 6 tests
    └── test_model.py            # 4 tests
```

---

## For AI Agents

### When Building Features

1. **Define the command first** — Create Pydantic schema, implement handler
2. **Test via CLI** — Validate all inputs, outputs, error cases
3. **Build UI surface** — Thin wrapper that calls the command

### When Fixing Bugs

1. **Reproduce via CLI** — Can you trigger the bug without UI?
2. **Fix at command layer** — Fix should work for all surfaces
3. **Verify via CLI** — Confirm fix before checking UI

### Code Conventions

- Commands return `CommandResult` with `success`, `data`, `error`
- Include `reasoning` for human-readable explanations
- Include `suggestion` in errors for recovery guidance
- Use Pydantic for all input/output validation
- UI contains zero business logic

---

## Related Projects

| Project                | Description                         |
| ---------------------- | ----------------------------------- |
| [AFD](../afd/)         | Agent-First Development methodology |
| [WEB_DEV](../WEB_DEV/) | Development guides and tools        |

---

## Success Criteria

- [x] All commands work via CLI before UI exists
- [x] MCP server created with FastMCP
- [x] ML pipeline supports multiple backends (mock, huggingface)
- [x] 29 tests passing
- [x] REST API exposes commands (8 endpoints)
- [x] Web UI is thin wrapper with no business logic
- [x] Deployed to Azure Container Apps
- [x] Can generate images via CLI, MCP, and Web UI (same commands)
- [x] Architecture allows swapping UI without touching commands
- [ ] MCP server discoverable in VS Code/Cursor
- [ ] GPU quota approved for real inference
