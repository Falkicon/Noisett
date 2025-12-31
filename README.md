# Noisett

**AI Brand Asset Generator** - Generate on-brand illustrations and icons using AI.

Built with **Agent-First Development (AFD)** principles—commands are the source of truth, validated via CLI before any UI surface is built.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run CLI commands
noisett asset.generate '{"prompt": "cloud computing concept", "asset_type": "product"}'
noisett asset.types '{}'
noisett model.list '{}'
noisett job.list '{}'

# Check system health
noisett doctor

# List available commands
noisett commands
```

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
│                    Python + FastMCP + Pydantic                           │
│  asset.generate │ asset.types │ job.status │ job.cancel │ model.list    │
├─────────────────────────────────────────────────────────────────────────┤
│                           ML INFERENCE LAYER                             │
│              PyTorch + Diffusers + HiDream + LoRAs                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Commands

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

## MCP Integration

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

## REST API

Start the API server:

```bash
uvicorn src.server.api:app --port 8000
```

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

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install with ML dependencies (for actual image generation)
pip install -e ".[ml]"

# Run tests (29 tests)
pytest tests/ -v

# Lint code
ruff check .
```

## Implementation Status

| Phase | Component   | Status  |
| ----- | ----------- | ------- |
| 1     | Commands    | ✅ Done |
| 2     | MCP Server  | ✅ Done |
| 3     | ML Pipeline | ✅ Done |
| 4     | REST API    | ✅ Done |
| 5     | Web UI      | ✅ Done |
| 6     | Deployment  | 🔜 Next |

## Documentation

| Document                                                      | Description                               |
| ------------------------------------------------------------- | ----------------------------------------- |
| [CHANGELOG.md](./CHANGELOG.md)                                | Release history and changes               |
| [Strategy/00-overview.md](./Docs/Strategy/00-overview.md)     | Architecture and AFD principles           |
| [Strategy/01-commands.md](./Docs/Strategy/01-commands.md)     | Command definitions with Pydantic schemas |
| [Strategy/02-mcp-server.md](./Docs/Strategy/02-mcp-server.md) | FastMCP integration guide                 |
| [Strategy/03-web-ui.md](./Docs/Strategy/03-web-ui.md)         | Vanilla JS UI implementation              |
| [Strategy/04-deployment.md](./Docs/Strategy/04-deployment.md) | Azure deployment guide                    |

## License

MIT
