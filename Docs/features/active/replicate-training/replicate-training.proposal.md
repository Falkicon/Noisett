# Replicate LoRA Training Integration

**Status:** READY  
**Author:** Agent  
**Created:** 2026-01-13  
**Research Date:** 2026-01-13  
**Review Feedback Applied:** 2026-01-13  

---

## Summary

Enable real LoRA training via cloud API, replacing the current MVP simulation. Training data stored in Convex for real-time sync, with Convex Auth for user management.

---

## Problem

The current LoRA training pipeline is **MVP simulation only**:
- In-memory `_loras` dict (no persistence across restarts)
- Training "completes" instantly (no real training)
- Images stored as URL references only (no actual upload)
- No real `.safetensors` output

**Impact:** Users cannot train custom brand LoRAs, the core differentiator of Noisett.

---

## Research Findings (January 2026)

### Training Providers

| Feature | **Replicate** | **Fal.ai** |
|---------|---------------|------------|
| **Best For** | FLUX.1 [dev] &amp; [schnell] | FLUX 1.1 [pro], speed |
| **Trainer** | `ostris/flux-dev-lora-trainer` | `fal-ai/flux-lora-fast-training` |
| **Pricing** | ~$1.85-2.00/run | ~$2.00/run |
| **Training Time** | ~20 minutes (1000 steps) | ~2-5 minutes (fast) |
| **Output** | `.safetensors` + hosted | `.safetensors` + hosted |

**Recommendation:** Replicate as primary (established patterns). Fal.ai as fallback for speed. [S4]

### Fireworks Custom LoRA Support ✅

Fireworks REST API for programmatic LoRA uploads (no CLI needed):

```python
# 4-step programmatic upload (January 2026)
from fireworks.client import Fireworks

client = Fireworks(api_key="...")
my_lora = client.models.create(
    name="noisett-brand-lora",
    base_model="accounts/fireworks/models/flux-1-dev",
    source_path="./lora_files/"  # Local .safetensors
)
my_lora.wait_until_ready()
```

Or via REST API:
1. `POST /v1/accounts/{id}/models` (create model entry, kind=`HF_PEFT_ADDON`)
2. `POST .../models/{id}:getUploadEndpoint` (get signed URLs)
3. `PUT` files to signed URLs
4. `GET .../models/{id}:validateUpload` (wait for READY)

### Replicate Training API Pattern [B1 RESOLVED]

Training uses different API than inference:

```python
import replicate
import time

# Create training job
training = replicate.trainings.create(
    model="ostris/flux-dev-lora-trainer",
    version="4ffd32160efd92e956d39c5338a9b8fbafca58e03f7...",
    destination="your-username/your-model-name",
    input={
        "input_images": "https://storage.convex.cloud/...",  # Zip URL
        "trigger_word": "brandstyle",
        "steps": 1000,
    },
    webhook="https://noisett.api/webhooks/replicate/training",  # [S1]
    webhook_events_filter=["completed", "failed"]
)

# Webhook preferred (20 min training, polling wasteful) [S1]
# If polling needed:
while training.status not in ["succeeded", "failed"]:
    time.sleep(30)
    training = replicate.trainings.get(training.id)

# Output: training.output["weights"] → URL to .safetensors
```

### Convex File Storage (2026 State)

- **Production-ready:** Out of beta, stable
- **Upload URLs for bulk:** Use `storage.generateUploadUrl()` for training images
- **Cost:** ~$0.03/GB storage, $0.30/GB bandwidth
- **Best practice:** Never run training logic in Convex Actions — use for data orchestration only

---

## Convex Schema [B3 RESOLVED]

```typescript
// convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  loras: defineTable({
    // Core fields
    name: v.string(),
    triggerWord: v.string(),
    description: v.optional(v.string()),
    baseModel: v.union(v.literal("flux"), v.literal("sd35"), v.literal("sdxl")),
    
    // Status tracking
    status: v.union(
      v.literal("created"),
      v.literal("uploading"),
      v.literal("ready_to_train"),
      v.literal("training"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("deployed")
    ),
    
    // Training config
    steps: v.number(),
    progress: v.optional(v.number()),  // 0-100 [S6]
    currentStep: v.optional(v.number()),
    
    // External IDs
    replicateTrainingId: v.optional(v.string()),
    fireworksModelId: v.optional(v.string()),
    
    // URLs
    loraUrl: v.optional(v.string()),  // Replicate output
    
    // Activation
    isActive: v.boolean(),
    
    // Timestamps
    createdAt: v.number(),
    trainStartedAt: v.optional(v.number()),
    completedAt: v.optional(v.number()),
    
    // User isolation (Phase 5)
    userId: v.optional(v.string()),
  })
    .index("by_user", ["userId"])
    .index("by_status", ["status"])
    .index("by_trigger_word", ["triggerWord"]),

  trainingImages: defineTable({
    loraId: v.id("loras"),
    storageId: v.id("_storage"),  // Convex file reference
    filename: v.string(),
    caption: v.optional(v.string()),
    sizeBytes: v.number(),
    width: v.optional(v.number()),  // [S3] Validation
    height: v.optional(v.number()),
    uploadedAt: v.number(),
  })
    .index("by_lora", ["loraId"]),
});
```

---

## Image Zip Export Workflow [B4 RESOLVED]

```python
# In lora.py train() handler
import io
import zipfile
import httpx

async def export_training_images_to_zip(lora_id: str) -> str:
    """Export Convex images to a zip file for Replicate.
    
    1. Query Convex for all images for this lora_id
    2. Download each image from Convex storage URL
    3. Create in-memory zip with images + captions
    4. Upload zip to temp storage (Convex or Replicate)
    5. Return public URL
    """
    # Get images from Convex
    images = await convex.query("trainingImages:list", {"loraId": lora_id})
    
    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        async with httpx.AsyncClient() as client:
            for i, img in enumerate(images):
                # Download image
                url = await convex.query("storage:getUrl", {"storageId": img["storageId"]})
                response = await client.get(url)
                
                # Add to zip (Replicate expects: image_001.jpg, image_001.txt)
                ext = img["filename"].split(".")[-1]
                zf.writestr(f"image_{i:03d}.{ext}", response.content)
                if img.get("caption"):
                    zf.writestr(f"image_{i:03d}.txt", img["caption"])
    
    # Upload zip to Convex storage
    zip_buffer.seek(0)
    upload_url = await convex.mutation("storage:generateUploadUrl", {})
    await httpx.AsyncClient().put(upload_url, data=zip_buffer.read())
    
    # Get public URL for Replicate
    return await convex.query("storage:getUrl", {"storageId": ...})
```

---

## Fireworks Upload Automation [B2 RESOLVED]

```python
# In Phase 4: Automated Fireworks deployment
import httpx

async def deploy_to_fireworks(lora_url: str, lora_name: str) -> str:
    """Upload trained LoRA to Fireworks for inference.
    
    Uses Fireworks REST API (Python SDK or raw HTTP).
    Returns Fireworks model ID for inference.
    """
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    FIREWORKS_ACCOUNT_ID = os.getenv("FIREWORKS_ACCOUNT_ID")
    
    async with httpx.AsyncClient() as client:
        # 1. Download .safetensors from Replicate
        weights_response = await client.get(lora_url)
        weights_data = weights_response.content
        
        # 2. Create model entry
        create_response = await client.post(
            f"https://api.fireworks.ai/v1/accounts/{FIREWORKS_ACCOUNT_ID}/models",
            headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}"},
            json={
                "displayName": lora_name,
                "kind": "HF_PEFT_ADDON",
                "baseModel": "accounts/fireworks/models/flux-1-dev",
            }
        )
        model_id = create_response.json()["id"]
        
        # 3. Get upload endpoint
        upload_response = await client.post(
            f".../models/{model_id}:getUploadEndpoint",
            json={"adapter_model.safetensors": len(weights_data)}
        )
        signed_url = upload_response.json()["uploadUrls"]["adapter_model.safetensors"]
        
        # 4. Upload weights
        await client.put(signed_url, content=weights_data)
        
        # 5. Validate and wait for READY
        await client.get(f".../models/{model_id}:validateUpload")
        
        # Poll until ready (or use webhook)
        while True:
            status = await client.get(f".../models/{model_id}")
            if status.json()["state"] == "READY":
                break
            await asyncio.sleep(5)
        
        return model_id
```

---

## Proposed Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NOISETT TRAINING PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │ lora.create  │──▶│ lora.upload  │──▶│  lora.train  │──▶│ lora.deploy │  │
│  │              │   │   images     │   │              │   │  (auto)     │  │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CONVEX BACKEND                               │   │
│  │  • loras table (schema above)                                        │   │
│  │  • trainingImages table + file storage                               │   │
│  │  • Real-time progress updates [S6]                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                     │                             │
│         │         ┌───────────────────────────┼─────────────────────────┐   │
│         │         │                           │                         │   │
│         ▼         ▼                           ▼                         │   │
│  ┌──────────────────────┐            ┌──────────────────────┐          │   │
│  │  REPLICATE (Train)    │            │  FIREWORKS (Infer)   │          │   │
│  │  • ostris/flux-lora   │─────────▶ │  • REST API upload   │          │   │
│  │  • Webhook callbacks  │  deploy   │  • ~$0.003/image     │          │   │
│  │  • ~$2/run, 20 min    │           │  • Multi-LoRA serve  │          │   │
│  └──────────────────────┘            └──────────────────────┘          │   │
│                                               │                         │   │
│                                      ┌────────┴────────┐               │   │
│                                      │ asset.generate  │               │   │
│                                      │ --lora          │               │   │
│                                      └─────────────────┘               │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases (Updated)

### Phase 1: Convex Storage Migration
- Deploy Convex schema above
- Create HTTP endpoints: create, get, list, update, delete
- Update `lora.py` commands to use Convex client
- Test with existing CLI commands

### Phase 2: Convex File Storage + Image Validation [S3]
- Implement `generateUploadUrl()` pattern
- **Image validation before upload:**
  - Minimum dimensions: 512x512
  - Maximum file size: 10MB
  - Formats: JPEG, PNG only
  - Return warnings in CommandResult
- Store metadata in `trainingImages` table

### Phase 3: Replicate Training Integration
- Add `replicate` Python package
- **Add webhook endpoint:** `/api/webhooks/replicate/training` [S1]
- Implement zip export workflow (see B4 above)
- **Add cost estimate command:** `lora.estimate` [S2]
  - Calculate based on steps × base rate
  - Show warning before training starts
- Store progress in Convex for SSE reconnection [S6]

### Phase 4: Fireworks LoRA Deployment
- Implement Fireworks REST API upload (see B2 above)
- **Add rollback strategy:** [S5]
  - Store Replicate `.safetensors` URL (valid ~24h)
  - Add `lora.deploy` command for retry
  - Fallback to Replicate inference if Fireworks fails
- Update `asset.generate` to use Fireworks LoRA endpoint

### Phase 5: Convex Auth Integration (Deferred)
- Split into separate proposal per review feedback [O1]
- Port auth pattern from AFD demo when ready

---

## New Commands

| Command | Purpose |
|---------|---------|
| `lora.estimate` [S2] | Show cost estimate before training |
| `lora.deploy` [S5] | Retry Fireworks upload for failed deployment |

---

## Webhook Endpoint [S1]

```python
# src/server/api.py
@app.post("/api/webhooks/replicate/training")
async def replicate_training_webhook(request: Request):
    """Receive Replicate training status updates.
    
    Updates Convex directly instead of polling.
    """
    payload = await request.json()
    training_id = payload["id"]
    status = payload["status"]
    
    # Find LoRA by replicateTrainingId
    lora = await convex.query("loras:byReplicateId", {"id": training_id})
    
    if status == "succeeded":
        output_url = payload["output"]["weights"]
        await convex.mutation("loras:update", {
            "id": lora["_id"],
            "status": "completed",
            "loraUrl": output_url,
            "completedAt": datetime.now().timestamp() * 1000,
        })
        # Trigger Fireworks deployment
        asyncio.create_task(deploy_to_fireworks(output_url, lora["name"]))
        
    elif status == "failed":
        await convex.mutation("loras:update", {
            "id": lora["_id"],
            "status": "failed",
        })
    
    return {"ok": True}
```

---

## Success Criteria (Updated)

- [ ] LoRA projects persist in Convex
- [ ] Training images upload via Convex File Storage with validation [S3]
- [ ] Cost estimate shown before training [S2]
- [ ] `lora.train` triggers real Replicate training (~20 min)
- [ ] Webhook updates Convex in real-time [S1]
- [ ] SSE can reconnect and resume progress [S6]
- [ ] Trained LoRA auto-deploys to Fireworks
- [ ] `lora.deploy` available for retry if deployment fails [S5]
- [ ] `asset.generate --lora` uses Fireworks LoRA inference

---

## Cost Estimate

| Component | Cost |
|-----------|------|
| Replicate training | ~$2.00 per LoRA |
| Fireworks inference (with LoRA) | ~$0.003/image |
| Convex (Starter) | Free + $0.03/GB storage |
| Convex File Bandwidth | $0.30/GB (export for training) |

---

## Risks &amp; Mitigations (Updated)

| Risk | Mitigation |
|------|------------|
| Fireworks upload fails | `lora.deploy` retry + Replicate inference fallback [S5] |
| Training quality issues | Image validation before upload [S3] |
| Convex file limits | Pre-compress images, monitor bandwidth |
| Network disconnection | Progress persisted in Convex, SSE reconnect works [S6] |
| User surprised by cost | Show estimate via `lora.estimate` command [S2] |

---

## Review Feedback Resolution

### Blockers (All Resolved)

| ID | Issue | Resolution |
|----|-------|------------|
| B1 | Replicate training API undefined | Added `trainings.create()` pattern with webhook support |
| B2 | Fireworks upload automation | Added REST API 4-step upload pattern |
| B3 | Convex schema missing | Added full TypeScript schema with indexes |
| B4 | Zip export undefined | Added workflow with async image download |

### Suggestions (All Incorporated)

| ID | Suggestion | Status |
|----|------------|--------|
| S1 | Webhook instead of polling | ✅ Added webhook endpoint |
| S2 | Cost estimation | ✅ Added `lora.estimate` command |
| S3 | Image validation | ✅ Added validation in Phase 2 |
| S4 | Fal.ai fallback | ✅ Noted as alternative provider |
| S5 | Rollback strategy | ✅ Added `lora.deploy` retry |
| S6 | Progress persistence | ✅ Store in Convex for reconnection |

### Out of Scope (Deferred)

- O1: Convex Auth → Separate proposal after Phases 1-4
- O2: Multi-LoRA inference → Future iteration
- O3: SDXL support → FLUX-only for Phase 1
- O4: LoRA versioning → Future iteration
- O5: Auto-captioning → Future iteration
