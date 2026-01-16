# Noisett API Contracts

> **AFD Principle**: This document is the single source of truth for API interfaces.
> Agents should reference this before making API calls. Tests validate these contracts.

## TypeSpec: The Source of Truth

All API schemas are now defined in **TypeSpec** files in `contracts/`:

```
contracts/
├── main.tsp              # Entry point
├── models/
│   ├── common.tsp        # Shared types (ConvexId, StorageId, Timestamp)
│   ├── asset-type.tsp    # AssetType, CreateRequest, UpdateRequest
│   ├── lora.tsp          # Lora, LoraStatus enum, LoraCreateRequest
│   ├── job.tsp           # Job, JobStatus enum, QualityPreset enum
│   └── generation.tsp    # GenerateRequest, GenerateResponse
└── generated/
    ├── openapi.yaml      # OpenAPI 3.0 spec (auto-generated)
    ├── types.ts          # TypeScript types (auto-generated)
    └── python/Models.py  # Python Pydantic models (auto-generated)
```

**Regenerate after changing .tsp files:**
```bash
npm run contracts:generate
```

---

## Quick Reference

| Domain | Endpoint Pattern | Backend |
|--------|-----------------|---------|
| Generation | `/api/generate`, `/api/jobs/*` | FastAPI |
| Asset Types | `/api/asset-types/*` | Convex HTTP |
| LoRAs | `/api/loras/*`, `/api/lora/{id}/*` | Convex HTTP + FastAPI |
| Uploads | `/api/upload/*` | FastAPI |
| Storage | `/api/storage/*` | Convex HTTP |

---

## Generation API (FastAPI)

### POST /api/generate
Create a new image generation job.

**Request:**
```json
{
  "prompt": "string (required, 1-500 chars)",
  "asset_type": "string (default: 'product')",
  "model": "string (default: 'hidream', e.g. 'replicate:flux-2-max')",
  "quality": "string (default: 'standard', options: draft|standard|high)",
  "count": "integer (1-4, default: 1)",
  "lora": "string|null (Convex LoRA ID, optional)",
  "asset_type_id": "string|null (Convex Asset Type ID for reference images)"
}
```

**Response:**
```json
{
  "job": { "id": "uuid", "status": "queued", ... },
  "estimated_seconds": 20
}
```

### GET /api/jobs/{job_id}
Get job status and results.

### POST /api/jobs/{job_id}/cancel
Cancel a running job.

---

## Asset Types API (Convex HTTP)

### POST /api/asset-types/create
Create a new asset type configuration.

**Request:**
```json
{
  "name": "string (required)",
  "slug": "string (optional, backend API identifier)",
  "description": "string (optional)",
  "prePrompt": "string (required)",
  "postPrompt": "string (required)",
  "model": "string (required, e.g. 'replicate:flux-dev-lora')",
  "modelSettings": "object (required, model-specific params)",
  "loraId": "string|null (optional, Convex LoRA ID)",
  "qualityPreset": "string (optional)",
  "isActive": "boolean (required)",
  "createdAt": "number (required, timestamp)"
}
```

**Edge Cases:**
- `loraId: null` → Accepted (no LoRA selected)
- `loraId: undefined` → Accepted (no LoRA selected)
- `loraId: "invalid"` → Error: Invalid Convex ID format

### GET /api/asset-types/list
List all asset types. Query param: `?activeOnly=true|false`

### GET /api/asset-types/get?id={id}
Get a single asset type by ID.

### POST /api/asset-types/update
Update an asset type.

**Request:**
```json
{
  "id": "string (required, Convex ID)",
  "name": "string (optional)",
  "loraId": "string|null (optional, null clears the field)",
  ...other fields optional
}
```

### DELETE /api/asset-types/delete?id={id}
Soft-delete (sets `isActive: false`).

---

## LoRA API

### Convex Routes

#### POST /api/loras/create
```json
{
  "name": "string (required)",
  "triggerWord": "string (required)",
  "baseModel": "string (default: 'flux')",
  "steps": "number (100-5000, default: 1000)"
}
```

#### GET /api/loras/list
Returns all LoRAs.

#### GET /api/loras/get?id={id}
Get single LoRA by Convex ID.

#### POST /api/loras/update
```json
{
  "id": "string (required, Convex ID)",
  "status": "string (optional, enum: created|uploading|ready_to_train|training|completed|deployed|failed)",
  "loraUrl": "string (optional, Replicate weights URL)",
  "isActive": "boolean (optional)",
  ...other optional fields
}
```

### FastAPI Routes

#### POST /api/lora/{lora_id}/train
Start LoRA training on Replicate.

**Response:**
```json
{
  "success": true,
  "data": {
    "lora_id": "string",
    "training_id": "string (Replicate training ID)",
    "status": "training"
  }
}
```

#### POST /api/lora/{lora_id}/sync
Sync training status from Replicate to Convex.

**Response:**
```json
{
  "success": true,
  "data": {
    "lora_id": "string",
    "replicate_status": "succeeded|failed|processing",
    "new_status": "completed|training|failed",
    "lora_url": "string|null (weights URL if completed)"
  }
}
```

**Side Effects (when succeeded):**
- Sets `status: "completed"`
- Sets `loraUrl` to weights URL
- Sets `isActive: true` (makes LoRA usable)

---

## Upload API (FastAPI)

### POST /api/upload/image
Upload an image to Convex storage.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "storageId": "string (Convex storage ID)",
  "url": "string (public URL)"
}
```

### POST /api/upload/training-image
Upload a training image for a LoRA.

**Request:** `multipart/form-data`
- `file`: Image file
- `loraId`: Convex LoRA ID

---

## Model Registry

Models are defined in `src/ml/models.json`. Key capabilities:

| Model | LoRA Support | Reference Images | Max Refs |
|-------|--------------|------------------|----------|
| replicate:flux-dev-lora | ✓ | ✗ | - |
| replicate:flux-2-max | ✗ | ✓ | 8 |
| replicate:nano-banana-pro | ✗ | ✓ | 14 |
| replicate:seedream-4.5 | ✗ | ✓ | 14 |

---

## Common Error Patterns

### Convex Validation Errors
```
ArgumentValidationError: Object contains extra field `fieldName`
```
**Fix:** Field not in mutation validator. Add to `convex/*.ts` args.

```
ArgumentValidationError: Value does not match validator. Path: .fieldName
```
**Fix:** Type mismatch. Check if sending `null` vs `undefined`.

### LoRA Errors
```
LoRA is not active
```
**Fix:** Call `/api/lora/{id}/sync` to set `isActive: true` after training.

```
LoRA is not ready (status: training)
```
**Fix:** Wait for training to complete or sync status.

---

## Test Coverage

Contract tests should validate:
- [ ] All endpoints accept documented fields
- [ ] Optional fields accept `null`, `undefined`, and omission
- [ ] Error cases return expected error codes
- [ ] Convex mutations match their validators

See: `tests/api/test_contracts.py` (TODO)
