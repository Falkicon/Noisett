# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Documentation Policy**: Skills are the source of truth for detailed knowledge.
> This file is a routing table. See [noisett skill](skills/noisett/) for commands, ML backends, and deployment.

> Remember your knowledge is 6-12 months old. Use the lushbot research MCP tool when current information is needed. For example, picking a package version, API changes, etc.

## Project Overview

Noisett is an **AI Brand Asset Generator** — generate on-brand illustrations and icons using AI. Built with Agent-First Development (AFD) principles where commands are the source of truth.

**Status:** AFD Compliant ✅ | Director Mode (v1.0)  
**Live URL:** https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io/

## Build Commands

```bash
# Install
pip install -e .              # Standard install
pip install -e ".[dev]"       # With dev dependencies
pip install -e ".[ml]"        # With ML dependencies

# Development
pytest tests/ -v              # Run tests (100 passing)
ruff check .                  # Lint code
ruff check . --fix            # Auto-fix lint issues

# CLI
noisett asset.generate '{"prompt": "...", "asset_type": "product"}'
noisett commands              # List all commands
noisett doctor                # System health check

# Server
uvicorn src.server.api:app --port 8000  # REST API
python -m src.server.mcp                 # MCP server (stdio)
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

## Key Directories

```
src/
├── commands/       # 25 AFD commands (asset, job, model, lora, quality, history, favorites)
├── core/           # CommandResult, errors, types
├── ml/             # ML backends
└── server/         # mcp.py, api.py

web/                # Vanilla JS frontend
figma-plugin/       # Figma plugin v2
infrastructure/     # Azure Container Apps
```

## MCP Configuration

```json
{
  "mcpServers": {
    "noisett": {
      "command": "python",
      "args": ["-m", "src.server.mcp"],
      "cwd": "/path/to/noisett"
    }
  }
}
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ML_BACKEND` | `mock`, `fireworks`, `huggingface`, `replicate` |
| `FIREWORKS_API_KEY` | Fireworks.ai API key |
| `GITHUB_TOKEN` | For CI/CD |

## AFD Workflow

```
1. DEFINE   → Create command with Pydantic schema
2. VALIDATE → Test via CLI: noisett <command> '<json>'
3. SURFACE  → Build UI that calls command
```

**The Honesty Check:** If it can't be done via CLI, the architecture is wrong.

## Skill Index

| Skill | When to Use |
|-------|-------------|
| [noisett](skills/noisett/) | Commands, ML backends, deployment, quality pipeline |

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](../CHANGELOG.md) | Release history |
| [Strategy/00-overview.md](../Docs/Strategy/00-overview.md) | Architecture |
| [Strategy/01-commands.md](../Docs/Strategy/01-commands.md) | Command specs |
| [Strategy/04-deployment.md](../Docs/Strategy/04-deployment.md) | Azure deployment |
