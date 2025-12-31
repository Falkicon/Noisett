# Architecture & System Design

**Status:** Reference

**Last Updated:** December 2025

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────┐                         │
│  │   React Web App     │    │   Figma Plugin      │  (v2.2)                 │
│  │   (Static Web Apps) │    │   (TypeScript)      │                         │
│  └──────────┬──────────┘    └──────────┬──────────┘                         │
│             │                          │                                     │
│             └──────────┬───────────────┘                                     │
│                        ▼                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                           API GATEWAY                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Azure Container Apps                              │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │                    FastAPI Application                         │  │    │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │  │    │
│  │  │  │   Auth      │  │   Jobs      │  │   Generation        │   │  │    │
│  │  │  │   Module    │  │   Queue     │  │   Worker            │   │  │    │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                        │                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                           GPU LAYER                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ML Inference Engine                               │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │    │
│  │  │  HiDream    │  │   FLUX      │  │   SD 3.5                    │  │    │
│  │  │  + LoRA     │  │   + LoRA    │  │   + LoRA                    │  │    │
│  │  │  (MVP)      │  │   (v2.0)    │  │   (v2.0)                    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                        │                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                           STORAGE                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐      │
│  │  Azure Blob     │  │   SQLite        │  │   Azure CDN            │      │
│  │  (Images)       │  │   (MVP Jobs)    │  │   (Image delivery)     │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Web Frontend

| Aspect | Details |
| --- | --- |
| Framework | React 18 with TypeScript |
| Build Tool | Vite |
| State Management | React Query (TanStack Query) for server state |
| Styling | CSS Modules or Tailwind CSS |
| Auth Library | @azure/msal-react |
| Hosting | Azure Static Web Apps |

**Key Dependencies:**

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.x",
  "@tanstack/react-query": "^5.x",
  "@azure/msal-browser": "^3.x",
  "@azure/msal-react": "^2.x"
}
```

### 2. Backend API

| Aspect | Details |
| --- | --- |
| Framework | FastAPI 0.109+ |
| Python Version | 3.11 |
| ASGI Server | Uvicorn |
| Task Queue | In-memory asyncio queue (MVP), Redis/Celery (v2+) |
| Auth Validation | python-jose for JWT validation |

**Key Dependencies:**

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-jose[cryptography]>=3.3.0
httpx>=0.26.0
pydantic>=2.5.0
python-multipart>=0.0.6
```

### 3. ML Inference Engine

| Aspect | Details |
| --- | --- |
| Framework | PyTorch 2.1+ with CUDA 12.1 |
| Diffusion Library | diffusers 0.25+ |
| Model Format | SafeTensors |
| LoRA Library | PEFT |
| GPU Requirement | 16GB+ VRAM (A10, A100, or T4) |

**Key Dependencies:**

```
torch>=2.1.0
diffusers>=0.25.0
transformers>=4.36.0
accelerate>=0.25.0
peft>=0.7.0
safetensors>=0.4.0
```

---

## Directory Structure

```
brand-asset-generator/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Route pages
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API client
│   │   ├── types/              # TypeScript types
│   │   ├── styles/             # Global styles, tokens
│   │   ├── config/             # Auth config
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   ├── core/               # Config, security, logging
│   │   ├── models/             # Pydantic models
│   │   ├── services/           # Business logic
│   │   └── [main.py](http://main.py)             # FastAPI entry
│   ├── ml/
│   │   ├── models/             # Model configs
│   │   ├── loras/              # LoRA weights
│   │   └── [inference.py](http://inference.py)        # Generation logic
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── figma-plugin/                # v2.2
│   ├── src/
│   ├── manifest.json
│   └── package.json
│
├── infra/                       # Infrastructure as Code
│   └── terraform/
│
└── docs/
```

---

## Data Flow

### Generation Request Flow

```
1. User submits prompt
   │
   ▼
2. Frontend sends POST /generate
   │  - Authorization: Bearer {token}
   │  - Body: { prompt: "..." }
   │
   ▼
3. Backend validates token with Azure AD
   │
   ▼
4. Backend creates Job record (status: "queued")
   │  - Returns job_id immediately
   │
   ▼
5. Frontend polls GET /jobs/{id} every 2 seconds
   │
   ▼
6. Worker picks up job from queue
   │
   ▼
7. ML Engine generates 4 images
   │  - Load base model + LoRA
   │  - Run inference (28 steps)
   │
   ▼
8. Worker uploads images to Blob Storage
   │
   ▼
9. Worker updates Job (status: "complete")
   │
   ▼
10. Frontend displays images
```

---

## Authentication Flow

### Token Validation (Backend)

```python
async def validate_token(token: str) -> User:
    # 1. Decode JWT header (get key ID)
    header = jwt.get_unverified_header(token)
    
    # 2. Fetch Azure AD public keys (cached)
    keys = await get_azure_ad_keys()
    
    # 3. Verify signature
    payload = jwt.decode(
        token,
        keys[header["kid"]],
        algorithms=["RS256"],
        audience=AZURE_AD_CLIENT_ID,
        issuer=f"[https://login.microsoftonline.com/{TENANT_ID}/v2.0](https://login.microsoftonline.com/{TENANT_ID}/v2.0)"
    )
    
    # 4. Check group membership (optional)
    if REQUIRED_GROUP_ID not in payload.get("groups", []):
        raise HTTPException(403, "Not authorized")
    
    return User(
        id=payload["oid"],
        email=payload["preferred_username"],
        name=payload.get("name")
    )
```

---

## Scaling Considerations

| Concern | MVP Solution | Scaled Solution |
| --- | --- | --- |
| Job Queue | In-memory asyncio | Redis + Celery |
| Database | SQLite file | Azure PostgreSQL |
| Compute | Single GPU container | Multiple replicas |
| Caching | None | Redis |
| CDN | Direct Blob access | Azure CDN |

---

## Security Architecture

1. **Network:** HTTPS only (TLS 1.3)
2. **Authentication:** Azure AD SSO required, JWT validation
3. **Authorization:** Group-based access control
4. **Application:** Input validation, rate limiting, CORS
5. **Storage:** SAS tokens (24hr expiry), auto-deletion (30 days)

---

## Error Handling

| Category | HTTP Code | Handling |
| --- | --- | --- |
| Validation | 400 | Return specific field errors |
| Authentication | 401 | Prompt re-login |
| Authorization | 403 | Access denied message |
| Not Found | 404 | Job doesn't exist |
| Rate Limit | 429 | Retry-after message |
| Generation Failure | 500 | Generic error, log details |
| GPU Unavailable | 503 | Queue full, try later |