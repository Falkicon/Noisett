# Noisett Architecture Overview

**Project:** Noisett (Brand Asset Generator)
**Architecture:** Agent-First Development (AFD)
**Status:** Phase 1-5 Complete ✅ | Phase 6 (Deployment) In Progress 🔄

---

## Implementation Progress

| Phase | Component   | Status     | Notes                              |
| ----- | ----------- | ---------- | ---------------------------------- |
| 1     | Commands    | ✅ Done    | 7 commands with Pydantic schemas   |
| 2     | MCP Server  | ✅ Done    | FastMCP integration, 7 tools       |
| 3     | ML Pipeline | ✅ Done    | Mock + HuggingFace (FLUX) backends |
| 4     | REST API    | ✅ Done    | FastAPI, 8 endpoints, 14 tests     |
| 5     | Web UI      | ✅ Done    | Vanilla JS frontend                |
| 6     | Deployment  | 🔄 Started | Dockerfile, CI/CD, Azure configs   |

**Tests:** 29 passing

---

## Executive Summary

Noisett is an internal AI image generation tool built using **Agent-First Development** principles. Commands are the source of truth—validated via CLI before any UI surface is built. This architecture enables:

- **Multi-surface deployment**: Same commands power MCP (VS Code/Cursor), REST API (Web UI), and future Figma plugin
- **Fearless UI experimentation**: Swap UI implementations without touching business logic
- **CLI-first validation**: Every feature works via command line before UI investment
- **AI-native integration**: First-class MCP support for agent workflows

---

## Core Principle: Commands First

> "If it can't be done via CLI, the architecture is wrong."

All functionality flows through the command layer:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SURFACES (Thin Wrappers)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   VS Code /     │  │   Web UI        │  │   Figma Plugin          │  │
│  │   Cursor (MCP)  │  │   (Vanilla JS)  │  │   (v2, TypeScript)      │  │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬────────────┘  │
│           │                    │                        │               │
│           │ MCP (stdio)        │ REST API               │ REST API      │
│           └────────────────────┼────────────────────────┘               │
│                                ▼                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                        COMMAND LAYER (Source of Truth)                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Python + FastMCP + Pydantic                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │    │
│  │  │ asset.      │  │ model.      │  │ job.                    │  │    │
│  │  │ generate    │  │ list        │  │ status                  │  │    │
│  │  │ types       │  │ info        │  │ cancel                  │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                │                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                           ML INFERENCE LAYER                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              PyTorch + Diffusers + HiDream + LoRAs              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer           | Technology                    | Rationale                                             | Status |
| --------------- | ----------------------------- | ----------------------------------------------------- | ------ |
| **Commands**    | Python + Pydantic             | Native ML ecosystem, type-safe schemas                | ✅     |
| **MCP Server**  | FastMCP (official Python SDK) | Simplest path to MCP, auto-generates tool definitions | ✅     |
| **ML Backends** | Mock, HuggingFace, Replicate  | Multiple options: free testing → paid production      | ✅     |
| **REST API**    | FastAPI                       | Async, shares Pydantic models with commands           | ✅     |
| **Web UI**      | Vanilla JS/HTML/CSS           | Small surface, easy to swap, AFD philosophy           | ✅     |
| **Auth**        | Microsoft Entra ID            | Corporate SSO requirement                             | ⏳     |
| **Storage**     | Azure Blob                    | Generated images                                      | ⏳     |
| **Compute**     | Azure Container Apps (GPU)    | Serverless scaling                                    | ⏳     |

---

## AFD Principles Applied

### 1. Command-First Development

All functionality is exposed as commands before any UI is built:

```python
# Step 1: Define command with Pydantic schema
class GenerateInput(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    asset_type: AssetType = AssetType.PRODUCT
    count: int = Field(default=4, ge=1, le=4)

# Step 2: Implement handler
async def asset_generate(input: GenerateInput) -> CommandResult:
    # Business logic here
    return success(job, reasoning=f"Started generation of {input.count} images")

# Step 3: Validate via CLI
# noisett asset.generate '{"prompt": "A person working on laptop"}'

# Step 4: Build UI only after CLI works
```

### 2. The Honesty Check

Before any UI work, verify:

- Can this action be performed via CLI?
- Does the CLI return all data the UI needs?
- Is the response schema complete?

If any answer is "no", fix the command layer first.

### 3. UX-Enabling Responses

Commands return metadata that enables good UX for both humans and agents:

```python
class CommandResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[CommandError] = None

    # UX-enabling fields
    reasoning: Optional[str] = None      # Explain "why" to users
    confidence: Optional[float] = None   # 0-1, reliability indicator
    warnings: Optional[List[Warning]] = None
    suggestions: Optional[List[str]] = None
```

### 4. Structured Errors

Errors include recovery guidance:

```python
return error(
    code="PROMPT_TOO_LONG",
    message="Prompt exceeds 500 character limit",
    suggestion="Shorten your prompt or split into multiple requests"
)
```

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

---

## Project Structure

```
noisett/
├── AGENTS.md                    # Project index
├── pyproject.toml               # Python project config
├── test_generate.py             # Quick test script for ML backends
│
├── Docs/
│   └── Strategy/                # AFD-first strategy docs
│       ├── 00-overview.md       # Architecture + AFD principles (this file)
│       ├── 01-commands.md       # Command definitions + schemas
│       ├── 02-mcp-server.md     # MCP integration details
│       ├── 03-web-ui.md         # Vanilla JS UI approach
│       └── 04-deployment.md     # Azure infrastructure
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
│   │   ├── errors.py            # Standard error codes + templates
│   │   └── types.py             # Domain types (Job, Model, AssetType, etc.)
│   │
│   ├── ml/                      # ML inference layer ✅
│   │   └── __init__.py          # MockGenerator, HuggingFaceGenerator, ReplicateGenerator
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
└── tests/                       # Test suite ✅
    ├── test_api.py              # 14 tests (REST API)
    ├── test_asset.py            # 5 tests
    ├── test_job.py              # 6 tests
    └── test_model.py            # 4 tests
```

---

## Key Decisions

| Decision              | Choice                 | Rationale                                             |
| --------------------- | ---------------------- | ----------------------------------------------------- |
| Backend language      | Python                 | Native ML ecosystem, FastMCP simplicity               |
| Schema validation     | Pydantic               | Python-native, same philosophy as Zod                 |
| MCP implementation    | FastMCP (official SDK) | Auto-generates tool definitions from type hints       |
| Web UI framework      | None (vanilla JS)      | Small surface, AFD makes UI swappable                 |
| Frontend architecture | Thin wrapper           | UI only calls commands, no business logic             |
| Base model            | HiDream / FLUX         | HiDream (Apache 2.0, commercial OK), FLUX (reference) |

---

## ML Backends

Three backends available for different use cases:

| Backend       | Cost         | Speed         | Use Case                 |
| ------------- | ------------ | ------------- | ------------------------ |
| `mock`        | Free         | Instant       | Testing, development     |
| `huggingface` | Free tier    | ~15-30s/image | Testing with real images |
| `replicate`   | ~$0.03/image | ~10-15s/image | Production quality       |

```bash
# Test with mock (instant placeholders)
python test_generate.py "robot mascot" --backend mock

# Test with real images (needs HF_TOKEN)
python test_generate.py "robot mascot" --backend huggingface

# Production quality (needs REPLICATE_API_TOKEN)
python test_generate.py "robot mascot" --backend replicate
```

---

## Success Criteria

- [x] All commands work via CLI before UI exists
- [x] MCP server created with FastMCP
- [x] ML pipeline supports multiple backends (mock, huggingface, replicate)
- [x] 29 tests passing
- [x] REST API exposes commands (8 endpoints)
- [x] Web UI with vanilla JS (4 files)
- [x] UI is a thin wrapper with no business logic
- [x] Deployment infrastructure (Dockerfile, CI/CD, Azure configs) — Phase 6 started
- [ ] Can generate images via CLI, MCP, and Web UI (same commands)
- [ ] MCP server discoverable in VS Code/Cursor
- [ ] Azure deployment live with GPU

---

## Related Documents

| Document                               | Description                               |
| -------------------------------------- | ----------------------------------------- |
| [CHANGELOG.md](../../CHANGELOG.md)     | Release history and changes               |
| [01-commands.md](./01-commands.md)     | Command definitions with Pydantic schemas |
| [02-mcp-server.md](./02-mcp-server.md) | FastMCP integration details               |
| [03-web-ui.md](./03-web-ui.md)         | Vanilla JS UI approach                    |
| [04-deployment.md](./04-deployment.md) | Azure deployment guide                    |

---

## Legacy Documentation

The following docs in `Docs/Archive/specs-*` folders contain earlier planning work done before adopting AFD. They remain as reference but the Strategy docs supersede them for implementation:

- `Archive/specs-pm/` — Original PM specs (user stories, requirements)
- `Archive/specs-dev/` — Original dev specs (pre-AFD architecture)
- `Archive/specs-design/` — UI wireframes, design tokens (still relevant for visual design)
