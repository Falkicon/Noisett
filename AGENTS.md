# Noisett - AI Agent Context

> **Project:** Noisett (Brand Asset Generator)
> **Architecture:** Agent-First Development (AFD)
> **Status:** Phase 1-5 Complete ✅ | Phase 6 (Deployment) In Progress 🔄

---

## Implementation Progress

| Phase | Component   | Status     | Notes                           |
| ----- | ----------- | ---------- | ------------------------------- |
| 1     | Commands    | ✅ Done    | 7 commands implemented          |
| 2     | MCP Server  | ✅ Done    | FastMCP integration             |
| 3     | ML Pipeline | ✅ Done    | Mock + HuggingFace backends     |
| 4     | REST API    | ✅ Done    | FastAPI, 8 endpoints            |
| 5     | Web UI      | ✅ Done    | Vanilla JS frontend             |
| 6     | Deployment  | 🔄 Started | Dockerfile, CI/CD, Azure config |

**Tests:** 29 passing

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
│                    Python + FastMCP + Pydantic                           │
│  asset.generate │ asset.types │ job.status │ job.cancel │ model.list    │
├─────────────────────────────────────────────────────────────────────────┤
│                           ML INFERENCE LAYER                             │
│              PyTorch + Diffusers + HiDream + LoRAs                       │
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

# List asset types
noisett asset.types '{}'
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

| Layer       | Technology                    | Status         |
| ----------- | ----------------------------- | -------------- |
| Commands    | Python + Pydantic             | ✅ Implemented |
| MCP Server  | FastMCP (official Python SDK) | ✅ Implemented |
| ML Backends | Mock, HuggingFace (FLUX)      | ✅ Implemented |
| REST API    | FastAPI                       | ✅ Implemented |
| Web UI      | Vanilla JS/HTML/CSS           | ✅ Implemented |
| Auth        | Microsoft Entra ID            | ⏳ Pending     |
| Storage     | Azure Blob                    | ⏳ Pending     |
| Compute     | Azure Container Apps (GPU)    | ⏳ Pending     |

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
├── infrastructure/              # Azure deployment files 🔄
│   ├── container-app.yaml       # Container Apps config
│   └── setup-azure.sh           # Provisioning script
│
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline 🔄
│
├── Dockerfile                   # Production container 🔄
├── requirements.txt             # Production dependencies 🔄
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
- [ ] MCP server discoverable in VS Code/Cursor
- [ ] Can generate images via CLI, MCP, and Web UI (same commands)
- [ ] Architecture allows swapping UI without touching commands
