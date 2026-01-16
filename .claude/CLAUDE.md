# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Documentation Policy**: Skills are the source of truth for detailed knowledge.
> See [noisett skill](skills/noisett/) for commands, ML backends, and deployment.

## Project Overview

Noisett is an **AI Brand Asset Generator** — generate on-brand illustrations and icons using AI. Built with Agent-First Development (AFD) principles where commands are the source of truth.

**Live URL:** https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io/

## Build Commands

```bash
# Install
pip install -e .              # Standard install
pip install -e ".[dev]"       # With dev dependencies
pip install -e ".[ml]"        # With ML dependencies (torch, diffusers)

# Development
pytest tests/ -v              # Run all tests
pytest tests/test_asset.py -v # Run single test file
pytest tests/ -k "test_generate"  # Run tests matching pattern
ruff check .                  # Lint code
ruff check . --fix            # Auto-fix lint issues

# CLI (validate commands work before building UI)
noisett asset.generate '{"prompt": "...", "asset_type": "product"}'
noisett commands              # List all 25 commands
noisett doctor                # System health check

# Servers
uvicorn src.server.api:app --port 8000  # REST API
python -m src.server.mcp                 # MCP server (stdio)

# Frontend (vanilla JS)
cd app && python -m http.server 3000
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SURFACES (Thin Wrappers)                       │
│     VS Code/Cursor (MCP)  │  Web UI (Vanilla JS)  │  Figma Plugin (v2)   │
├─────────────────────────────────────────────────────────────────────────┤
│                        COMMAND LAYER (Source of Truth)                   │
│                    Python + FastMCP + Pydantic (25 Commands)             │
│  asset.* │ job.* │ model.* │ lora.* │ quality.* │ history.* │ favorites.* │
├─────────────────────────────────────────────────────────────────────────┤
│                           ML INFERENCE LAYER                             │
│          Mock | HuggingFace | Fireworks.ai (FLUX) | Replicate            │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Patterns

### CommandResult (AFD Standard)
All commands return `CommandResult[T]` from `src/core/result.py`:
```python
{
  "success": true,
  "data": {...},
  "reasoning": "Started generation of 4 product illustrations",
  "confidence": 0.95,
  "warnings": [...],
  "suggestions": ["Try 'premium' for marketing-grade quality"]
}
```

Use `success()` and `error()` helpers to construct results consistently.

### Adding a New Command
1. Create Pydantic input/output schemas in `src/commands/<domain>.py`
2. Implement async function returning `CommandResult[OutputType]`
3. Register in `src/server/mcp.py` and `src/server/api.py`
4. Validate via CLI: `noisett <command> '<json>'`
5. Add tests in `tests/test_<domain>.py`

### ML Backend Selection
Set `ML_BACKEND` env var: `mock` (dev), `fireworks` (production), `replicate`, `huggingface`.
Mock backend returns placeholders and simulates delays — no API keys needed for development.

## Key Files

| File | Purpose |
|------|---------|
| `src/core/result.py` | `CommandResult`, `success()`, `error()` helpers |
| `src/core/types.py` | Shared Pydantic models (Job, AssetType, ModelId) |
| `src/core/errors.py` | Error codes and templates |
| `src/ml/registry.py` | Dynamic model discovery from `models.json` |
| `src/server/api.py` | FastAPI REST endpoints |
| `src/server/mcp.py` | FastMCP server for VS Code/Cursor |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ML_BACKEND` | `mock` (default), `fireworks`, `huggingface`, `replicate` |
| `FIREWORKS_API_KEY` | Fireworks.ai API key (for `fireworks` backend) |
| `REPLICATE_API_TOKEN` | Replicate API key (for `replicate` backend) |
| `CONVEX_URL` | Convex backend URL (for storage) |
| `DEBUG` | Set `true` to enable `/api/test-replicate` endpoint |

## AFD Workflow

```
1. DEFINE   → Create command with Pydantic schema
2. VALIDATE → Test via CLI: noisett <command> '<json>'
3. SURFACE  → Build UI that calls command
```

**The Honesty Check:** If it can't be done via CLI, the architecture is wrong.

## Skill Reference

| Skill | When to Use |
|-------|-------------|
| [noisett](skills/noisett/) | Commands, ML backends, deployment, quality pipeline |

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](../CHANGELOG.md) | Release history |
| [STATUS.md](../STATUS.md) | Current working state and known issues |
| [Strategy/](../Docs/Strategy/) | Architecture docs (00-overview through 09-future) |
