# Phase 9: Future Enhancements

> **Status:** Optional / Post-MVP  
> **Priority:** When resources available  
> **Prerequisite:** Phases 1-8 complete ✅

---

## Overview

Phase 9 captures enhancements that improve Noisett's production readiness but aren't required for the core AFD implementation. These can be tackled independently as needs arise.

---

## 9.1 GPU-Enabled Inference

**Goal:** Real-time image generation with dedicated GPU compute.

### Current State

- Using Fireworks.ai API (FLUX models, ~$0.003/image)
- ~10-30 second generation time
- No Azure GPU quota yet

### Target State

- Azure Container Apps with GPU workload profile
- Self-hosted inference (Stable Diffusion, FLUX)
- Sub-5 second generation time
- Cost optimization for high volume

### Implementation Steps

1. **Request Azure GPU Quota**

   ```bash
   # Check current quota
   az vm list-usage --location eastus --query "[?contains(name.value, 'NC')]"

   # Request increase via Azure Portal > Subscriptions > Usage + quotas
   ```

2. **Update Container App Configuration**

   ```yaml
   # infrastructure/container-app.yaml
   resources:
     cpu: 4
     memory: 16Gi
     gpu: 1
     gpuSku: nvidia-a10g # or T4 for cost savings
   ```

3. **Add Local Inference Backend**

   ```python
   # src/ml/local.py
   class LocalGenerator(Generator):
       """Self-hosted inference with ComfyUI or diffusers."""

       def __init__(self):
           self.pipeline = load_flux_pipeline()

       async def generate(self, prompt: str, ...) -> list[str]:
           # Direct GPU inference
           pass
   ```

4. **Backend Selection Logic**
   ```python
   # Environment-based backend selection
   ML_BACKEND = os.getenv("ML_BACKEND", "fireworks")
   # Options: mock, huggingface, fireworks, local
   ```

### Success Criteria

- [ ] GPU quota approved
- [ ] Container App running with GPU
- [ ] Generation time < 5 seconds
- [ ] Cost per image < $0.001

---

## 9.2 Application Insights Monitoring

**Goal:** Production observability with Azure Application Insights.

### Current State

- Basic logging to stdout
- No centralized telemetry
- Manual error discovery

### Target State

- Structured logging with correlation IDs
- Request/response tracing
- Error alerting
- Performance dashboards

### Implementation Steps

1. **Add OpenTelemetry Dependencies**

   ```toml
   # pyproject.toml
   [project.optional-dependencies]
   monitoring = [
       "azure-monitor-opentelemetry>=1.0.0",
       "opentelemetry-instrumentation-fastapi>=0.40b0",
   ]
   ```

2. **Create Telemetry Module**

   ```python
   # src/core/telemetry.py
   from azure.monitor.opentelemetry import configure_azure_monitor
   from opentelemetry import trace

   def init_telemetry():
       """Initialize Azure Monitor telemetry."""
       connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
       if connection_string:
           configure_azure_monitor(connection_string=connection_string)

   tracer = trace.get_tracer(__name__)

   def track_generation(prompt: str, duration: float, success: bool):
       """Track generation metrics."""
       with tracer.start_as_current_span("generation") as span:
           span.set_attribute("prompt.length", len(prompt))
           span.set_attribute("duration_ms", duration * 1000)
           span.set_attribute("success", success)
   ```

3. **Instrument FastAPI**

   ```python
   # src/server/api.py
   from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

   app = FastAPI()
   FastAPIInstrumentor.instrument_app(app)
   ```

4. **Add Custom Metrics**
   ```python
   # Track per-command execution
   @track_command("asset.generate")
   async def generate_asset(...):
       ...
   ```

### Success Criteria

- [ ] Application Insights resource created
- [ ] All API requests traced
- [ ] Error rate alerts configured
- [ ] Generation latency dashboard

---

## 9.3 Advanced LoRA Training UI

**Goal:** Visual interface for LoRA training workflow.

### Current State

- LoRA commands exist (7 commands)
- CLI-only interaction
- MVP simulation (no real training)

### Target State

- Web UI for training project management
- Image upload with drag-and-drop
- Training progress visualization
- Model comparison gallery

### Implementation Steps

1. **Extend Web UI** (`web/lora.html`)

   - Project list view
   - Image upload dropzone
   - Training status cards
   - Generated samples gallery

2. **Add REST Endpoints**

   ```python
   # src/server/api.py
   @app.post("/api/lora")
   async def create_lora_project(...): ...

   @app.post("/api/lora/{id}/images")
   async def upload_training_images(...): ...

   @app.post("/api/lora/{id}/train")
   async def start_training(...): ...

   @app.get("/api/lora/{id}/status")
   async def get_training_status(...): ...
   ```

3. **Real Training Integration**
   - Replicate API for cloud training
   - Or self-hosted with kohya_ss
   - Webhook for training completion

### Success Criteria

- [ ] Web UI for LoRA management
- [ ] Image upload working
- [ ] Real training backend connected
- [ ] Trained models usable in generation

---

## 9.4 User Management & Multi-Tenancy

**Goal:** Support multiple users with isolated data.

### Current State

- Auth middleware exists (Phase 8)
- SQLite with user_id column
- Anonymous user for CLI

### Target State

- Microsoft Entra ID login flow
- Per-user history and favorites
- Usage quotas per user
- Admin dashboard

### Implementation Steps

1. **Enable Auth by Default**

   ```bash
   # Environment variables
   AUTH_REQUIRED=true
   AZURE_TENANT_ID=<your-tenant>
   AZURE_CLIENT_ID=<your-app-id>
   ```

2. **Add Login Flow to Web UI**

   ```javascript
   // web/auth.js
   import { PublicClientApplication } from "@azure/msal-browser";

   const msalConfig = {
     auth: {
       clientId: "YOUR_CLIENT_ID",
       authority: "https://login.microsoftonline.com/YOUR_TENANT_ID",
     },
   };
   ```

3. **Implement Usage Quotas**
   ```python
   # src/core/quotas.py
   async def check_quota(user_id: str, action: str) -> bool:
       """Check if user has remaining quota for action."""
       usage = await get_user_usage(user_id, action)
       limit = get_quota_limit(user_id, action)
       return usage < limit
   ```

### Success Criteria

- [ ] Entra ID login working
- [ ] Users see only their data
- [ ] Quota enforcement active
- [ ] Admin can view all users

---

## 9.5 Production Database Migration

**Goal:** Move from SQLite to cloud database.

### Current State

- SQLite for local storage
- Single-file database
- No backup strategy

### Target State

- Azure Cosmos DB (or PostgreSQL)
- Automatic backups
- Multi-region replication
- Connection pooling

### Implementation Steps

1. **Abstract Storage Interface**

   ```python
   # src/core/storage.py
   class StorageBackend(Protocol):
       async def save_generation(...): ...
       async def get_generation(...): ...
       # ... other methods

   class SQLiteBackend(StorageBackend): ...
   class CosmosDBBackend(StorageBackend): ...
   ```

2. **Add Cosmos DB Backend**

   ```python
   # src/core/storage_cosmos.py
   from azure.cosmos.aio import CosmosClient

   class CosmosDBBackend(StorageBackend):
       def __init__(self):
           self.client = CosmosClient(
               os.getenv("COSMOS_ENDPOINT"),
               credential=os.getenv("COSMOS_KEY")
           )
   ```

3. **Migration Script**

   ```python
   # scripts/migrate_to_cosmos.py
   async def migrate():
       sqlite = SQLiteBackend()
       cosmos = CosmosDBBackend()

       for record in sqlite.list_all_generations():
           await cosmos.save_generation(record)
   ```

### Success Criteria

- [ ] Cosmos DB resource provisioned
- [ ] Backend selection via env var
- [ ] Data migrated from SQLite
- [ ] Backup policy configured

---

## Priority Matrix

| Enhancement        | Effort | Impact | Priority                  |
| ------------------ | ------ | ------ | ------------------------- |
| GPU Inference      | High   | High   | P1 (when quota available) |
| App Insights       | Medium | High   | P1                        |
| LoRA Training UI   | High   | Medium | P2                        |
| User Management    | Medium | Medium | P2                        |
| Database Migration | Medium | Low    | P3                        |

---

## Getting Started

Pick one enhancement and create a focused implementation plan:

```bash
# Example: Start with monitoring
cd Noisett
# 1. Create Docs/PLAN/Phase-09/9.2-monitoring.plan.md
# 2. Implement in small PRs
# 3. Validate via CLI before UI
```

Remember: **AFD principles apply** — every feature is a command first, validated via CLI, UI last.

---

## 9.6 Code Review Findings (2025-12-31)

Code review performed before production release. Issues logged for tracking.

**Update (2025-01-01):** All CRITICAL, HIGH, and most MEDIUM issues fixed. Tests: 100/100 passing.

### 🔴 CRITICAL (Must Fix)

| ID    | Issue                                                                         | File                | Status   |
| ----- | ----------------------------------------------------------------------------- | ------------------- | -------- |
| CR-01 | JWT validation lacks cryptographic verification - only base64 decodes payload | `src/core/auth.py`  | ✅ Fixed |
| CR-02 | CORS allows all origins (`allow_origins=["*"]`)                               | `src/server/api.py` | ✅ Fixed |
| CR-03 | Silent exception swallowing in auth masks attack attempts                     | `src/core/auth.py`  | ✅ Fixed |

### 🟠 HIGH (Should Fix)

| ID    | Issue                                                            | File                  | Status                      |
| ----- | ---------------------------------------------------------------- | --------------------- | --------------------------- |
| CR-04 | `CommandResult[Any]` loses type safety in error helper           | `src/core/result.py`  | ✅ Fixed                    |
| CR-05 | Inconsistent error format (dict vs CommandError model)           | Various commands      | N/A (not an issue)          |
| CR-06 | API endpoints use hardcoded anonymous user_id                    | `src/server/api.py`   | ✅ Fixed (uses auth module) |
| CR-07 | `JobCancelInput` missing `reason` field (API/command mismatch)   | `src/commands/job.py` | ✅ Fixed                    |
| CR-08 | `JobListInput` field name mismatch (`status` vs `status_filter`) | `src/server/api.py`   | ✅ Fixed                    |

### 🟡 MEDIUM (Nice to Fix)

| ID    | Issue                                                    | File                                      | Status                |
| ----- | -------------------------------------------------------- | ----------------------------------------- | --------------------- |
| CR-09 | Database initialization on import (side effects)         | `src/core/storage.py`                     | ⏳ Deferred           |
| CR-10 | Silent exception in storage context manager (no logging) | `src/core/storage.py`                     | ✅ Fixed              |
| CR-11 | MCP server missing history/favorites tools               | `src/server/mcp.py`                       | ✅ Fixed              |
| CR-12 | Duplicate/inconsistent FavoritesListInput definition     | `src/commands/favorites.py`               | N/A (not a duplicate) |
| CR-13 | Deprecated `datetime.utcnow()` usage                     | `src/core/auth.py`, `src/core/storage.py` | ✅ Fixed              |
| CR-14 | In-memory job store not shared across workers            | `src/commands/job.py`                     | ⏳ Deferred           |
| CR-15 | In-memory LoRA store not shared across workers           | `src/commands/lora.py`                    | ⏳ Deferred           |

### 🟢 LOW (Optional)

| ID    | Issue                                       | File                | Status                    |
| ----- | ------------------------------------------- | ------------------- | ------------------------- |
| CR-16 | Import inside function (`base64`, `json`)   | `src/core/auth.py`  | ✅ Fixed (imports at top) |
| CR-17 | Health check reports "degraded" without GPU | `src/server/api.py` | N/A (expected behavior)   |
| CR-18 | Minimal docstrings in CLI wrappers          | `src/cli.py`        | ⏳ Deferred               |
| CR-19 | Hardcoded inconsistent version numbers      | Multiple files      | ⏳ Deferred               |
| CR-20 | Mixed `List` vs `list` annotation styles    | All Python files    | ✅ Fixed                  |

### Missing Test Coverage

| Area                                             | Priority |
| ------------------------------------------------ | -------- |
| Auth middleware (validate_jwt, get_current_user) | HIGH     |
| MCP server tools                                 | MEDIUM   |
| CLI command routing                              | LOW      |
| Quality/LoRA commands                            | LOW      |
| Error handling paths in API                      | MEDIUM   |
