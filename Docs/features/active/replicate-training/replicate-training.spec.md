# Replicate LoRA Training Integration - Specification

**Status:** READY  
**Proposal:** [replicate-training.proposal.md](./replicate-training.proposal.md)  
**Created:** 2026-01-13  
**Review Feedback Applied:** 2026-01-13  

---

## Overview

Implement real LoRA training pipeline with Replicate (training) → Fireworks (inference), replacing MVP simulation. Convex backend for storage and real-time sync.

---

## Phase 1: Convex Storage Migration

### 1.1 Convex Project Setup

- [ ] Create new Convex project or use existing `stoic-bee-395`
- [ ] Add schema to `convex/schema.ts`
- [ ] Deploy schema: `npx convex dev`

**Schema (updated with error fields [S8]):**
```typescript
// convex/schema.ts
export default defineSchema({
  loras: defineTable({
    name: v.string(),
    triggerWord: v.string(),
    description: v.optional(v.string()),
    baseModel: v.union(v.literal("flux"), v.literal("sdxl")),  // [S7] Removed sd35 for Python consistency
    status: v.union(
      v.literal("created"),
      v.literal("uploading"),
      v.literal("ready_to_train"),
      v.literal("training"),
      v.literal("completed"),
      v.literal("deployment_pending"),   // [B3] Added
      v.literal("deployment_failed"),    // [B3] Added
      v.literal("failed"),
      v.literal("deployed")
    ),
    steps: v.number(),
    progress: v.optional(v.number()),
    currentStep: v.optional(v.number()),
    replicateTrainingId: v.optional(v.string()),
    fireworksModelId: v.optional(v.string()),
    loraUrl: v.optional(v.string()),
    isActive: v.boolean(),
    createdAt: v.number(),
    trainStartedAt: v.optional(v.number()),
    completedAt: v.optional(v.number()),
    userId: v.optional(v.string()),
    // Error tracking [S8]
    errorMessage: v.optional(v.string()),
    errorCode: v.optional(v.string()),
  })
    .index("by_user", ["userId"])
    .index("by_status", ["status"])
    .index("by_trigger_word", ["triggerWord"]),

  trainingImages: defineTable({
    loraId: v.id("loras"),
    storageId: v.id("_storage"),
    filename: v.string(),
    caption: v.optional(v.string()),
    sizeBytes: v.number(),
    width: v.optional(v.number()),
    height: v.optional(v.number()),
    uploadedAt: v.number(),
  })
    .index("by_lora", ["loraId"]),

  // Webhook idempotency tracking [S10/B4]
  webhookEvents: defineTable({
    eventId: v.string(),  // Replicate webhook ID
    processedAt: v.number(),
    eventType: v.string(),
  })
    .index("by_event_id", ["eventId"]),
});
```

### 1.2 Convex HTTP Actions [B2 RESOLVED]

**Add `convex/http.ts` for Python client access:**
```typescript
// convex/http.ts
import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";

const http = httpRouter();

// LoRA endpoints
http.route({
  path: "/api/loras/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.loras.create, body);
    return new Response(JSON.stringify({ id }));
  }),
});

http.route({
  path: "/api/loras/list",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const userId = url.searchParams.get("userId");
    const data = await ctx.runQuery(internal.loras.list, { userId });
    return new Response(JSON.stringify(data));
  }),
});

// ... additional routes for get, update, delete, byReplicateId

export default http;
```

### 1.3 Convex Functions

- [ ] `loras.create` mutation
- [ ] `loras.get` query
- [ ] `loras.list` query (with filters)
- [ ] `loras.update` mutation
- [ ] `loras.delete` mutation
- [ ] `loras.byReplicateId` query (for webhook)
- [ ] `loras.byTriggerWord` query (for duplicate detection [EC4])

### 1.4 Python Convex Client (depends on 1.2, 1.3) [S7]

- [ ] Create `src/core/convex_client.py`
- [ ] HTTP client for Convex HTTP Actions
- [ ] Async methods matching each Convex function
- [ ] Add rate limit handling with exponential backoff [S3]

### 1.5 Update LoRA Commands (depends on 1.4)

- [ ] Update `lora.create` to use Convex
- [ ] Update `lora.get` / `lora.status` to use Convex
- [ ] Update `lora.list` to use Convex
- [ ] Update `lora.activate` / `lora.deactivate` to use Convex
- [ ] Update `lora.delete` to use Convex
- [ ] Remove in-memory `_loras` dict
- [ ] **Update LoraStatus enum [S1]:** Add `DEPLOYMENT_PENDING`, `DEPLOYMENT_FAILED`, `DEPLOYED`

### 1.6 Phase 1 Verification

- [ ] All existing LoRA tests pass with Convex backend
- [ ] CLI commands work: `noisett lora.create`, `noisett lora.list`
- [ ] Data persists across server restarts

---

## Phase 2: Convex File Storage + Image Validation

### 2.1 Image Upload Endpoint

- [ ] Create `/api/lora/{id}/upload-url` endpoint
- [ ] Generate Convex upload URL
- [ ] Return URL to client

### 2.2 Image Validation [S3, S5]

- [ ] Validate individual images:
  - Minimum dimensions: 512x512
  - Maximum file size: 10MB
  - Formats: JPEG, PNG only
- [ ] Validate collection constraints [S5]:
  - Minimum images: 5 (error if fewer)
  - Maximum images: 100 (error if more)
  - Warning: < 15 images may produce poor results
- [ ] Return warnings in CommandResult

### 2.3 Training Images Table

- [ ] `trainingImages.create` mutation
- [ ] `trainingImages.list` query (by loraId)
- [ ] `trainingImages.delete` mutation
- [ ] `trainingImages.count` query (for validation)

### 2.4 Update lora.upload-images

- [ ] Accept file uploads via Convex URLs
- [ ] Store metadata in trainingImages table
- [ ] Update lora status to "uploading" → "ready_to_train"

### 2.5 Storage Quota Handling [EC2]

- [ ] Check Convex storage usage before upload
- [ ] Return clear error if quota exceeded
- [ ] Suggest cleanup of old LoRAs

### 2.6 Phase 2 Verification

- [ ] Images upload successfully to Convex
- [ ] Validation rejects bad images with helpful errors
- [ ] Collection constraints enforced
- [ ] Image metadata queryable by loraId

---

## Phase 3: Replicate Training Integration

### 3.1 Dependencies

- [ ] Add `replicate>=1.0.0` to pyproject.toml
- [ ] Add `REPLICATE_API_TOKEN` to required env vars
- [ ] Add `REPLICATE_WEBHOOK_SECRET` for verification

### 3.2 Zip Export Function [B4 RESOLVED]

```python
# src/ml/training.py
import tempfile
import zipfile
import httpx

async def export_training_images_to_zip(lora_id: str) -> str:
    """Export Convex images to zip for Replicate."""
    images = await convex.query("trainingImages:list", {"loraId": lora_id})
    
    # Validate image count [EC5]
    if len(images) == 0:
        raise ValueError("Cannot train with 0 images. Upload at least 5 images.")
    
    # Use temp file to avoid OOM [S8/S9]
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        try:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for i, img in enumerate(images):
                        url = await convex.query("storage:getUrl", 
                                                 {"storageId": img["storageId"]})
                        response = await client.get(url)
                        
                        ext = img["filename"].split(".")[-1]
                        zf.writestr(f"image_{i:03d}.{ext}", response.content)
                        if img.get("caption"):
                            zf.writestr(f"image_{i:03d}.txt", img["caption"])
            
            # Upload to Convex storage
            tmp.seek(0)
            upload_url = await convex.mutation("storage:generateUploadUrl", {})
            
            async with httpx.AsyncClient() as client:
                # Capture storage ID from upload response [B4]
                with open(tmp.name, 'rb') as f:
                    upload_response = await client.post(upload_url, content=f.read())
                storage_id = upload_response.json()["storageId"]
            
            # Get public URL
            return await convex.query("storage:getUrl", {"storageId": storage_id})
        finally:
            # Cleanup temp file [S9]
            os.unlink(tmp.name)
```

### 3.3 Training Job Creation

- [ ] Create `start_replicate_training()` function
- [ ] Use `replicate.trainings.create()` API
- [ ] Set webhook URL and events filter
- [ ] Store replicateTrainingId in Convex
- [ ] Update lora status to "training"
- [ ] Add rate limit handling [S3]

### 3.4 Webhook Endpoint [B1 RESOLVED]

```python
# src/server/api.py
import hmac
import hashlib

REPLICATE_WEBHOOK_SECRET = os.getenv("REPLICATE_WEBHOOK_SECRET")

@app.post("/api/webhooks/replicate/training")
async def replicate_training_webhook(request: Request):
    """Handle Replicate training webhooks with signature verification."""
    
    # [B1] Verify webhook signature
    signature = request.headers.get("Webhook-Signature", "")
    body = await request.body()
    expected = hmac.new(
        REPLICATE_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected}", signature):
        logger.warning(f"Invalid webhook signature from {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = json.loads(body)
    training_id = payload["id"]
    
    # [S10] Idempotency check
    existing = await convex.query("webhookEvents:byEventId", {"eventId": training_id})
    if existing:
        return {"ok": True, "skipped": True, "reason": "already_processed"}
    
    # Record event before processing
    await convex.mutation("webhookEvents:create", {
        "eventId": training_id,
        "processedAt": int(time.time() * 1000),
        "eventType": payload["status"],
    })
    
    # Find LoRA
    lora = await convex.query("loras:byReplicateId", {"id": training_id})
    if not lora:
        logger.error(f"LoRA not found for training {training_id}")
        return {"ok": False, "error": "lora_not_found"}
    
    if payload["status"] == "succeeded":
        output_url = payload["output"]["weights"]
        
        # [B3] Set intermediate status
        await convex.mutation("loras:update", {
            "id": lora["_id"],
            "status": "deployment_pending",
            "loraUrl": output_url,
            "completedAt": int(time.time() * 1000),
        })
        
        # Trigger async deployment with error handling
        asyncio.create_task(
            deploy_with_error_handling(lora["_id"], output_url, lora["name"])
        )
        
    elif payload["status"] == "failed":
        await convex.mutation("loras:update", {
            "id": lora["_id"],
            "status": "failed",
            "errorMessage": payload.get("error", "Training failed"),
            "errorCode": "REPLICATE_TRAINING_FAILED",
        })
    
    return {"ok": True}


async def deploy_with_error_handling(lora_id: str, url: str, name: str):
    """Deploy with retry and error tracking [B3]."""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            model_id = await deploy_to_fireworks(url, name)
            await convex.mutation("loras:update", {
                "id": lora_id,
                "status": "deployed",
                "fireworksModelId": model_id,
            })
            return
        except Exception as e:
            logger.error(f"Deployment attempt {attempt+1} failed: {e}")
            if attempt == max_attempts - 1:
                await convex.mutation("loras:update", {
                    "id": lora_id,
                    "status": "deployment_failed",
                    "errorMessage": str(e),
                    "errorCode": "FIREWORKS_DEPLOYMENT_FAILED",
                })
            else:
                await asyncio.sleep(5 * (attempt + 1))  # Backoff
```

### 3.5 lora.train Command Update

- [ ] Validate image count before training [EC5]
- [ ] Check for duplicate trigger words [EC4]
- [ ] Call zip export
- [ ] Call Replicate training
- [ ] Return HandoffResult with SSE endpoint

### 3.6 SSE Progress Endpoint Update (depends on 3.5) [S4]

- [ ] Read progress from Convex (not in-memory)
- [ ] Accept `?lastEventId=X` for reconnection
- [ ] Send events with sequential IDs
- [ ] Handle training cancellation [EC1]

### 3.7 lora.estimate Command [S4]

**Input/Output Schemas:**
```python
class EstimateLoraInput(BaseModel):
    lora_id: Optional[str] = None  # Use existing LoRA's steps
    steps: int = 1000              # Or specify steps directly

class EstimateLoraOutput(BaseModel):
    estimated_cost_usd: float      # ~$2.00 for 1000 steps
    estimated_time_minutes: int    # ~20 min for 1000 steps
    steps: int
```

- [ ] Calculate cost based on steps (~$0.002/step)
- [ ] Return estimate in CommandResult
- [ ] Show warning before training

### 3.8 lora.cleanup Command [S1]

- [ ] Delete LoRAs stuck in "uploading" > 24h
- [ ] Cancel orphaned Replicate jobs
- [ ] Purge orphaned zip files from storage

### 3.9 Phase 3 Verification

- [ ] `lora.train` creates Replicate job
- [ ] Webhook signature verified
- [ ] Webhook idempotency works
- [ ] Progress stored in Convex
- [ ] SSE shows real progress with reconnection
- [ ] Training completes with .safetensors URL

---

## Phase 4: Fireworks LoRA Deployment

### 4.1 Dependencies

- [ ] Add `FIREWORKS_API_KEY` to required env vars
- [ ] Add `FIREWORKS_ACCOUNT_ID` to required env vars

### 4.2 Fireworks Upload Function [S6]

```python
# src/ml/deployment.py
DEPLOYMENT_TIMEOUT = 600  # 10 minutes

async def deploy_to_fireworks(lora_url: str, lora_name: str) -> str:
    """Upload trained LoRA to Fireworks with timeout [S6]."""
    async with httpx.AsyncClient() as client:
        # Download weights
        weights = await client.get(lora_url)
        
        # Create model
        create_resp = await client.post(
            f"https://api.fireworks.ai/v1/accounts/{ACCOUNT_ID}/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "displayName": lora_name,
                "kind": "HF_PEFT_ADDON",
                "baseModel": "accounts/fireworks/models/flux-1-dev",
            }
        )
        model_id = create_resp.json()["id"]
        
        # Get upload endpoint
        upload_resp = await client.post(
            f".../models/{model_id}:getUploadEndpoint",
            json={"adapter_model.safetensors": len(weights.content)}
        )
        signed_url = upload_resp.json()["uploadUrls"]["adapter_model.safetensors"]
        
        # Upload
        await client.put(signed_url, content=weights.content)
        
        # Validate with timeout [S6]
        await client.get(f".../models/{model_id}:validateUpload")
        
        start = time.time()
        while True:
            if time.time() - start > DEPLOYMENT_TIMEOUT:
                raise TimeoutError(f"Fireworks deployment timed out after {DEPLOYMENT_TIMEOUT}s")
            
            status = await client.get(f".../models/{model_id}")
            if status.json()["state"] == "READY":
                return model_id
            await asyncio.sleep(5)
```

### 4.3 Auto-Deployment on Training Complete

- [ ] Webhook triggers `deploy_with_error_handling()`
- [ ] Uses intermediate status: `deployment_pending` → `deployed` or `deployment_failed`
- [ ] Includes retry logic with backoff

### 4.4 lora.deploy Command

- [ ] Retry Fireworks upload for failed deployments
- [ ] Check if loraUrl still valid (24h expiry) [EC3]
- [ ] If expired, show error with re-training suggestion
- [ ] Update status on success

### 4.5 Rollback Strategy

- [ ] Store Replicate loraUrl (valid ~24h)
- [ ] If Fireworks fails within 24h, `lora.deploy` can retry
- [ ] After 24h, require re-training
- [ ] Clear error messaging about expiry

### 4.6 Update asset.generate

- [ ] Add `--lora` parameter
- [ ] If LoRA specified:
  - Query Convex for fireworksModelId
  - Use Fireworks LoRA inference endpoint
- [ ] If no LoRA: use existing Fireworks base model

### 4.7 Phase 4 Verification

- [ ] Trained LoRA auto-deploys to Fireworks
- [ ] Intermediate status updates properly
- [ ] `lora.deploy` works for retry
- [ ] Timeout handling works
- [ ] `asset.generate --lora` produces LoRA-styled images
- [ ] Fallback to Replicate inference if Fireworks fails

---

## Files to Create

| File | Purpose |
|------|---------|
| `convex/schema.ts` | Convex schema with error fields |
| `convex/http.ts` | HTTP Actions for Python client [B2] |
| `convex/loras.ts` | LoRA CRUD functions |
| `convex/trainingImages.ts` | Image metadata functions |
| `convex/webhookEvents.ts` | Idempotency tracking [S10] |
| `convex/storage.ts` | File storage helpers |
| `src/core/convex_client.py` | Python HTTP client |
| `src/ml/training.py` | Zip export, Replicate training |
| `src/ml/deployment.py` | Fireworks upload with timeout |

## Files to Modify

| File | Changes |
|------|---------|
| `src/commands/lora.py` | Use Convex, add estimate/deploy/cleanup |
| `src/commands/asset.py` | Add --lora parameter |
| `src/server/api.py` | Add webhook with signature verification |
| `pyproject.toml` | Add replicate dependency |

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `CONVEX_URL` | Yes | Convex deployment URL |
| `REPLICATE_API_TOKEN` | Yes | Replicate auth |
| `REPLICATE_WEBHOOK_SECRET` | Yes | Webhook signature verification |
| `FIREWORKS_API_KEY` | Yes | Fireworks auth |
| `FIREWORKS_ACCOUNT_ID` | Yes | Fireworks account |

---

## Testing Plan

### Unit Tests

- [ ] Convex client methods
- [ ] Image validation logic (individual + collection)
- [ ] Zip export with temp file cleanup
- [ ] Webhook signature verification [B1]
- [ ] Fireworks upload logic

### Integration Tests

- [ ] Full training flow (with Replicate sandbox/mock)
- [ ] Fireworks deployment with timeout
- [ ] SSE reconnection with lastEventId
- [ ] Webhook → Convex → SSE E2E flow [S2]

### Error Case Tests [EC1-EC6]

- [ ] Training cancellation handling (server restart)
- [ ] Storage quota error response
- [ ] Expired URL retry behavior (24h after training)
- [ ] Duplicate trigger word detection
- [ ] Zero-image training rejection
- [ ] Network failure recovery in zip upload

### Manual Verification

- [ ] Train real LoRA with 10-15 test images
- [ ] Verify .safetensors downloads
- [ ] Test `asset.generate --lora` produces different style
- [ ] Test Fireworks deployment and inference
- [ ] Test `lora.deploy` retry after simulated failure

---

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Convex Migration | 1-2 days |
| Phase 2: File Storage | 1 day |
| Phase 3: Replicate Training | 2-3 days |
| Phase 4: Fireworks Deployment | 1-2 days |
| Testing & Polish | 1-2 days |
| **Total** | **~1 week** |

---

## Blocker Resolutions

| ID | Issue | Resolution |
|----|-------|------------|
| B1 | Webhook signature | Added HMAC-SHA256 verification code |
| B2 | Convex HTTP Actions | Added `convex/http.ts` with route structure |
| B3 | Deployment failure handling | Added `deployment_pending`/`deployment_failed` status + retry |
| B4 | Zip storage ID capture | Added response parsing in zip export code |

## Suggestions Incorporated

| ID | Suggestion | Location |
|----|------------|----------|
| S1 | Cleanup command | Phase 3.8 `lora.cleanup` |
| S2 | Webhook E2E test | Testing Plan |
| S3 | Rate limit handling | Phase 1.4, 3.3 |
| S4 | SSE reconnection | Phase 3.6 with `lastEventId` |
| S5 | Image count validation | Phase 2.2 |
| S6 | Deployment timeout | Phase 4.2 (10 min) |
| S7 | Task dependencies | Noted in phase headers |
| S8 | Error fields in schema | Phase 1.1 schema |
| S9 | Temp file cleanup | Phase 3.2 code |
| S10 | Webhook idempotency | Phase 3.4 + webhookEvents table |

## Edge Cases Addressed

| ID | Edge Case | Handling |
|----|-----------|----------|
| EC1 | Training cancelled | SSE handles, Replicate job continues |
| EC2 | Storage quota | Check before upload, clear error |
| EC3 | URL expiry (24h) | Check in `lora.deploy`, suggest re-train |
| EC4 | Duplicate trigger | Query before create, error if exists |
| EC5 | 0 images | Validate in lora.train, reject |
| EC6 | Network failure | Temp file cleanup, retry logic |
