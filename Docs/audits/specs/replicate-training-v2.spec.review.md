# Spec Review (v2): Replicate LoRA Training Integration

**Spec:** `docs/features/active/replicate-training/replicate-training.spec.md`
**Reviewer:** Claude (Opus 4.5)
**Review Date:** 2026-01-13
**Review Type:** Second Pass - Blocker Resolution Verification
**Focus:** Implementation readiness, previous blocker resolutions, remaining gaps

---

## PREVIOUS BLOCKERS STATUS

| ID | Issue | Status | Notes |
|----|-------|--------|-------|
| B1 | Webhook signature verification | **RESOLVED** | HMAC-SHA256 code added to Phase 3.4 |
| B2 | Convex HTTP Actions not specified | **RESOLVED** | `convex/http.ts` added in Phase 1.2 |
| B3 | Deployment failure handling | **RESOLVED** | `deployment_pending`/`deployment_failed` status + retry logic |
| B4 | Zip storage ID capture | **RESOLVED** | Response parsing added in Phase 3.2 |

All four previous blockers have been properly addressed with concrete implementation details.

---

## BLOCKERS

*None identified.*

The spec is now implementation-ready. All critical paths have defined behavior.

---

## SUGGESTIONS

### S1: Python LoraStatus Enum Needs Update

**Location:** `src/core/types.py:191-199`

**Observation:** The current Python `LoraStatus` enum does not include the new statuses introduced in the Convex schema:
- `deployment_pending`
- `deployment_failed`
- `deployed`

**Current code:**
```python
class LoraStatus(str, Enum):
    CREATED = "created"
    UPLOADING = "uploading"
    READY_TO_TRAIN = "ready_to_train"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
```

**Recommendation:** Add to Phase 1.5 "Update LoRA Commands":
```
- [ ] Update LoraStatus enum with new statuses (deployment_pending, deployment_failed, deployed)
```

---

### S2: Add `lora.redeploy` Command

**Location:** Phase 4.4 `lora.deploy`

**Observation:** The `lora.deploy` command handles retry for failed deployments, but naming is confusing. Users might expect `lora.deploy` to be the initial deployment (which is automatic), not a retry operation.

**Recommendation:** Rename to `lora.redeploy` or add explicit documentation:
```python
async def deploy(input: DeployLoraInput) -> CommandResult:
    """Retry Fireworks deployment for a failed LoRA.

    Only needed if automatic deployment after training failed.
    Use lora.status to check if deployment_failed.
    """
```

---

### S3: Define Convex Auth Strategy for HTTP Actions

**Location:** Phase 1.2 `convex/http.ts`

**Observation:** The HTTP routes shown don't include authentication headers. While the spec notes "Specify auth header handling for HTTP Actions" was addressed, the actual auth pattern isn't shown.

**Recommendation:** Add auth pattern to http.ts example:
```typescript
http.route({
  path: "/api/loras/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    // Validate internal API key (not user auth - that's Phase 5)
    const apiKey = request.headers.get("X-API-Key");
    if (apiKey !== process.env.INTERNAL_API_KEY) {
      return new Response("Unauthorized", { status: 401 });
    }
    // ... rest of handler
  }),
});
```

---

### S4: Add `lora.estimate` Input Schema

**Location:** Phase 3.7

**Observation:** `lora.estimate` is mentioned but no input/output schema defined. What inputs does it need?

**Recommendation:** Add to spec:
```python
class EstimateInput(BaseModel):
    lora_id: str  # OR
    steps: int = 1000
    base_model: BaseModelType = "flux"

class EstimateOutput(BaseModel):
    estimated_cost_usd: float
    estimated_time_minutes: int
    steps: int
```

---

### S5: SSE Event ID Format

**Location:** Phase 3.6

**Observation:** Spec mentions sequential IDs for SSE reconnection but doesn't define the format. Should align with EventSource `id` field expectations.

**Recommendation:** Define format explicitly:
```python
# SSE event format
yield {
    "id": f"{lora_id}:{step}",  # Composite ID for reconnection
    "event": "progress",
    "data": json.dumps({...}),
}
```

---

### S6: Clarify Zip Cleanup Timing

**Location:** Phase 3.2

**Observation:** Temp file cleanup is shown with `finally` block, but the uploaded zip in Convex storage also needs cleanup after Replicate downloads it.

**Recommendation:** Add to `lora.cleanup` tasks:
```
- [ ] Delete zip files from Convex storage after Replicate confirms download
- [ ] Add TTL or cleanup trigger for uploaded zips (24h max retention)
```

---

### S7: Missing `sd35` in Convex Schema BaseModel Union

**Location:** Phase 1.1 Schema

**Observation:** Convex schema shows:
```typescript
baseModel: v.union(v.literal("flux"), v.literal("sd35"), v.literal("sdxl"))
```

But `BaseModelType` enum in Python only has `FLUX` and `SDXL`. This inconsistency could cause validation issues.

**Recommendation:** Either:
- Remove `sd35` from Convex schema (current Python state)
- Or add `SD35 = "sd35"` to Python `BaseModelType` enum

---

## OUT OF SCOPE

### O1: Convex Deployment Strategy

Not specified: Does the team use a shared Convex project or separate dev/prod? This affects how schema migrations are handled.

**Recommendation:** Document in deployment guide, not spec.

---

### O2: Fireworks Model Naming Collision

If multiple users train LoRAs with similar names, Fireworks model `displayName` could collide. Not blocking but worth considering.

**Recommendation:** Future enhancement - prefix with user ID or add unique suffix.

---

### O3: Webhook Retry Policy on Network Failure

Replicate's webhook retry behavior when our endpoint is unreachable isn't specified. Relying on Replicate's built-in retry.

**Recommendation:** Document Replicate's retry policy in runbook.

---

## IMPLEMENTATION READINESS CHECKLIST

| Area | Ready? | Notes |
|------|--------|-------|
| Schema Definition | ✅ | Complete with error fields |
| API Contracts | ✅ | HTTP routes defined |
| Security (Webhooks) | ✅ | HMAC verification implemented |
| Error Handling | ✅ | Intermediate states + retry logic |
| Testing Plan | ✅ | Unit, integration, error cases covered |
| Environment Variables | ✅ | All 5 required vars documented |
| Dependencies | ✅ | `replicate>=1.0.0` specified |
| Phase Dependencies | ✅ | Explicit dependency notes added |

---

## SUMMARY

| Category | Count |
|----------|-------|
| Previous Blockers Resolved | 4/4 |
| New Blockers | 0 |
| Suggestions | 7 |
| Out of Scope | 3 |

**Overall Assessment:** The spec is **IMPLEMENTATION READY**. All previous blockers have been comprehensively addressed with concrete code examples. The remaining suggestions are minor clarifications and consistency fixes that can be addressed during implementation.

**Recommendation:** Proceed with implementation starting from Phase 1. Address S1 (Python enum update) and S7 (BaseModel consistency) early in Phase 1.5 to avoid type mismatches.
