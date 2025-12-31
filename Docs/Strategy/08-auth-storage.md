# Phase 8: Authentication & Storage

**Status:** 🔜 Planned  
**Dependencies:** Phase 4 (Deployment) ✅

---

## Goal

> Secure the application with corporate authentication and persist generated images for history/favorites.

From the original strategy:

> "Microsoft Entra ID for auth — Corporate SSO requirement."

---

## Authentication: Microsoft Entra ID

### Why Entra ID?

- **Corporate SSO** — Users sign in with work accounts
- **No password management** — Leverages existing identity
- **Conditional access** — Security policies apply
- **User context** — Know who generated what

### Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Web UI / Figma    │────▶│   Microsoft Entra   │
│                     │◀────│   ID (Azure AD)     │
└──────────┬──────────┘     └─────────────────────┘
           │
           │ Bearer Token
           ▼
┌─────────────────────┐
│   Noisett Backend   │
│   (FastAPI)         │
├─────────────────────┤
│  Validate JWT       │
│  Extract user_id    │
└─────────────────────┘
```

### FastAPI Integration

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from functools import lru_cache

security = HTTPBearer()

@lru_cache
def get_jwks():
    """Fetch Entra ID public keys."""
    tenant_id = os.environ["AZURE_TENANT_ID"]
    url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    return requests.get(url).json()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Validate JWT and extract user info."""
    token = credentials.credentials

    try:
        # Decode and validate token
        payload = jwt.decode(
            token,
            options={"verify_signature": True},
            algorithms=["RS256"],
            audience=os.environ["AZURE_CLIENT_ID"],
            issuer=f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}/v2.0"
        )

        return {
            "user_id": payload["oid"],  # Object ID
            "email": payload.get("preferred_username"),
            "name": payload.get("name"),
        }
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))

# Protected endpoint
@app.post("/api/generate")
async def generate(
    request: GenerateRequest,
    user: dict = Depends(get_current_user)
):
    # user["user_id"] available for tracking
    ...
```

### Web UI (React/JS)

```typescript
import { PublicClientApplication } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: "your-client-id",
    authority: "https://login.microsoftonline.com/your-tenant-id",
    redirectUri: window.location.origin,
  },
};

const pca = new PublicClientApplication(msalConfig);

// Login
async function login() {
  const result = await pca.loginPopup({
    scopes: ["api://noisett/.default"],
  });
  return result.accessToken;
}

// API calls with token
async function generate(prompt: string) {
  const token = await pca
    .acquireTokenSilent({
      scopes: ["api://noisett/.default"],
    })
    .then((r) => r.accessToken);

  return fetch("/api/generate", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
  });
}
```

### Azure App Registration

1. Go to Azure Portal → Entra ID → App registrations
2. New registration: "Noisett"
3. Configure:
   - Redirect URIs (Web UI URLs)
   - API permissions
   - Expose API scope
4. Note Client ID and Tenant ID

---

## Storage: Azure Blob

### Why Azure Blob?

- **Scalable** — No file system limits
- **Durable** — Geo-redundant
- **Fast** — CDN-capable
- **Integrated** — Works with Entra ID

### Architecture

```
Azure Blob Storage
└── noisett-storage/
    ├── generated/
    │   ├── {user_id}/
    │   │   ├── {job_id}/
    │   │   │   ├── image_0.jpg
    │   │   │   ├── image_1.jpg
    │   │   │   └── metadata.json
    │   │   └── ...
    │   └── ...
    ├── loras/                    # Phase 5
    │   └── ...
    └── training-data/            # Phase 5
        └── ...
```

### Blob Service Integration

```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
blob_service = BlobServiceClient(
    account_url="https://noisettstorage.blob.core.windows.net",
    credential=credential
)

container = blob_service.get_container_client("noisett-storage")

async def save_generated_image(
    user_id: str,
    job_id: str,
    image_index: int,
    image_bytes: bytes
) -> str:
    """Save image to blob storage, return URL."""
    blob_name = f"generated/{user_id}/{job_id}/image_{image_index}.jpg"
    blob_client = container.get_blob_client(blob_name)

    await blob_client.upload_blob(image_bytes, overwrite=True)

    return blob_client.url

async def get_user_history(user_id: str, limit: int = 50) -> list:
    """List user's recent generations."""
    prefix = f"generated/{user_id}/"
    blobs = container.list_blobs(name_starts_with=prefix)

    # Group by job_id, return recent
    jobs = {}
    for blob in blobs:
        if blob.name.endswith("metadata.json"):
            job_id = blob.name.split("/")[2]
            jobs[job_id] = blob.last_modified

    # Sort by date, limit
    recent = sorted(jobs.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [job_id for job_id, _ in recent]
```

### Metadata Storage

Each generation stores metadata:

```json
{
  "job_id": "abc123",
  "user_id": "oid-xyz",
  "prompt": "cloud computing concept",
  "asset_type": "premium",
  "quality": "high",
  "model": "flux",
  "created_at": "2025-12-31T12:00:00Z",
  "images": [
    { "index": 0, "seed": 12345, "filename": "image_0.jpg" },
    { "index": 1, "seed": 67890, "filename": "image_1.jpg" }
  ]
}
```

---

## History & Favorites

### Commands

```bash
# Get user's generation history
noisett history.list '{"limit": 50}'

# Get specific job details
noisett history.get '{"job_id": "abc123"}'

# Mark as favorite
noisett history.favorite '{"job_id": "abc123", "image_index": 0}'

# List favorites
noisett favorites.list '{}'

# Delete from history
noisett history.delete '{"job_id": "abc123"}'
```

### Database Schema (Optional)

For faster queries, consider SQLite or Azure Cosmos DB:

```sql
CREATE TABLE generations (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    quality TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_count INTEGER
);

CREATE TABLE favorites (
    user_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    image_index INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, job_id, image_index)
);

CREATE INDEX idx_generations_user ON generations(user_id, created_at);
```

---

## Pydantic Schemas

```python
from pydantic import BaseModel, Field
from datetime import datetime

class User(BaseModel):
    user_id: str
    email: str | None
    name: str | None

class GenerationRecord(BaseModel):
    job_id: str
    prompt: str
    asset_type: str
    quality: str
    created_at: datetime
    images: list[str]  # URLs

class HistoryListInput(BaseModel):
    limit: int = Field(50, ge=1, le=200)

class HistoryListOutput(BaseModel):
    generations: list[GenerationRecord]
    total_count: int

class FavoriteInput(BaseModel):
    job_id: str
    image_index: int = Field(..., ge=0, le=7)

class FavoritesListOutput(BaseModel):
    favorites: list[dict]  # {job_id, image_index, url, prompt, created_at}
```

---

## Environment Variables

```bash
# Entra ID
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id

# Storage
AZURE_STORAGE_ACCOUNT=noisettstorage
AZURE_STORAGE_CONTAINER=noisett-storage

# Optional: Cosmos DB for metadata
COSMOS_ENDPOINT=https://noisett.documents.azure.com:443/
COSMOS_DATABASE=noisett
```

---

## Migration Path

### Phase 1: Add Auth (Non-Breaking)

1. Add Entra ID validation
2. Make auth optional initially (`X-Auth-Optional: true` header)
3. Test with authenticated users
4. Enable required auth

### Phase 2: Add Storage

1. Create Azure Storage account
2. Update generate endpoint to save to blob
3. Add history endpoints
4. Migrate temp storage to blob

### Phase 3: Add History/Favorites

1. Add database (SQLite or Cosmos)
2. Implement history commands
3. Add favorites functionality
4. Update UI

---

## Success Criteria

- [ ] Users authenticate via Entra ID
- [ ] Invalid tokens rejected with 401
- [ ] Generated images saved to Azure Blob
- [ ] User can view their generation history
- [ ] User can mark favorites
- [ ] History persists across sessions
- [ ] Old images eventually cleaned up (retention policy)

---

## Timeline Estimate

| Task                      | Effort       |
| ------------------------- | ------------ |
| Entra ID app registration | 1 day        |
| FastAPI auth middleware   | 2 days       |
| Web UI auth integration   | 2 days       |
| Azure Blob setup          | 1 day        |
| Save images to blob       | 2 days       |
| History commands          | 2 days       |
| Favorites commands        | 1 day        |
| Testing                   | 2 days       |
| **Total**                 | **~2 weeks** |

---

## Related Documents

- [Original Strategy: Auth](../Archive/image-generation-strategy.md#recommended-azure-container-apps-with-serverless-gpu)
- [Azure Entra ID Docs](https://learn.microsoft.com/en-us/entra/identity-platform/)
- [Azure Blob Storage Docs](https://learn.microsoft.com/en-us/azure/storage/blobs/)
