# Development Environment Setup

**Status:** Reference

**Prerequisites:** Python 3.11, Node.js 20+, Docker, NVIDIA GPU (optional for local ML)

---

## Quick Start

### 1. Clone Repository

```bash
git clone [https://github.com/your-org/brand-asset-generator.git](https://github.com/your-org/brand-asset-generator.git)
cd brand-asset-generator
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your values

# Run development server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local
# Edit .env.local with your values

# Run development server
npm run dev
```

---

## Environment Variables

### Backend (.env)

```bash
# Azure AD
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_SECRET=your-client-secret  # Optional for backend

# Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=generated-images

# ML Settings
MODEL_ID=HiDream/HiDream-I1-Full
LORA_PATH=./loras/brand_product_v1.safetensors
DEFAULT_STEPS=28
DEFAULT_GUIDANCE=7.5

# App Settings
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=[http://localhost:5173](http://localhost:5173)
```

### Frontend (.env.local)

```bash
VITE_API_URL=[http://localhost:8000/api/v1](http://localhost:8000/api/v1)
VITE_AZURE_CLIENT_ID=your-client-id
VITE_AZURE_TENANT_ID=your-tenant-id
```

---

## Local Development Options

### Option A: Full Local (with GPU)

Best for ML development. Requires NVIDIA GPU with 16GB+ VRAM.

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Option B: Docker Compose

Best for testing full stack locally.

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - AZURE_AD_CLIENT_ID=${AZURE_AD_CLIENT_ID}
      - AZURE_AD_TENANT_ID=${AZURE_AD_TENANT_ID}
    volumes:
      - ./backend:/app
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=[http://localhost:8000/api/v1](http://localhost:8000/api/v1)
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

```bash
docker-compose up
```

### Option C: Mock API (No GPU)

Best for frontend development without GPU.

```bash
# Use mock API server
cd backend
python mock_[server.py](http://server.py)  # Serves static responses

# Frontend as normal
cd frontend
npm run dev
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_[generate.py](http://generate.py) -v
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm test -- --coverage

# E2E tests (Playwright)
npm run test:e2e
```

---

## Code Quality

### Linting & Formatting

```bash
# Backend
cd backend
ruff check .          # Linting
ruff format .         # Formatting

# Frontend
cd frontend
npm run lint          # ESLint
npm run format        # Prettier
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install
```

**.pre-commit-config.yaml:**

```yaml
repos:
  - repo: [https://github.com/astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit)
    rev: v0.1.9
    hooks:
      - id: ruff
      - id: ruff-format
        
  - repo: [https://github.com/pre-commit/mirrors-prettier](https://github.com/pre-commit/mirrors-prettier)
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, typescript, css, json]
```

---

## Debugging Tips

### Backend

```python
# Add to any route for debugging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@[app.post](http://app.post)("/generate")
async def generate(request: GenerateRequest):
    logger.debug(f"Received request: {request}")
    # ...
```

### Frontend

```tsx
// React Query DevTools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Add to App.tsx
<ReactQueryDevtools initialIsOpen={false} />
```

### GPU/ML Issues

```python
# Check CUDA availability
import torch
print(f"CUDA available: {[torch.cuda.is](http://torch.cuda.is)_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
```

---

## Common Issues

| Issue | Solution |
| --- | --- |
| CORS errors | Check CORS_ORIGINS in backend .env matches frontend URL |
| Auth redirect loop | Verify redirect URI in Azure AD app registration |
| GPU out of memory | Reduce batch size, enable CPU offload, use float16 |
| Slow model loading | Pre-download model, use safetensors format |
| Token expired | MSAL should auto-refresh; check acquireTokenSilent |

---

## VS Code Setup

**.vscode/settings.json:**

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

**Recommended Extensions:**

- Python (ms-python.python)
- Ruff (charliermarsh.ruff)
- Prettier (esbenp.prettier-vscode)
- ESLint (dbaeumer.vscode-eslint)
- Docker (ms-azuretools.vscode-docker)