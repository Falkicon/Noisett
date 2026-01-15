# Director Mode Specification

**Status:** READY  
**Proposal:** [director-mode.proposal.md](./director-mode.proposal.md)  
**Review:** [director-mode.proposal.review.md](./director-mode.proposal.review.md)

---

## Overview

Separate Noisett UI into Director (configuration) and User (generation) modes. Directors configure Asset Types; users pick Asset Types and generate.

## Implementation Plan

### Phase 1: Data Model & Backend

#### 1.1 Convex Schema (`schema.ts`)

**AssetTypes table:**
```typescript
assetTypes: defineTable({
  name: v.string(),
  description: v.optional(v.string()),
  prePrompt: v.string(),
  postPrompt: v.string(),
  model: v.string(),                    // "replicate:flux-dev-lora"
  modelSettings: v.any(),               // Model-specific params
  loraId: v.optional(v.id("loras")),
  qualityPreset: v.optional(v.string()),
  isActive: v.boolean(),
  createdAt: v.number(),
}).index("by_active", ["isActive"])
```

**Generations table:**
```typescript
generations: defineTable({
  assetTypeId: v.id("assetTypes"),
  userPrompt: v.string(),
  combinedPrompt: v.string(),
  images: v.array(v.object({
    url: v.string(),
    width: v.number(),
    height: v.number(),
    seed: v.optional(v.number()),
  })),
  isFavorite: v.boolean(),
  createdAt: v.number(),
}).index("by_favorite", ["isFavorite"])
  .index("by_created", ["createdAt"])
```

**Lifecycle rules:**
- Asset Types are global (no user ownership for now)
- Deleting an Asset Type sets `isActive: false` (soft delete)
- Generations keep `assetTypeId` reference (orphaned is OK)

#### 1.2 Model Registry (`src/ml/models.json`)

JSON config defining model capabilities. Extensible without code changes:

```json
{
  "replicate:flux-dev-lora": {
    "name": "FLUX Dev (LoRA)",
    "provider": "replicate",
    "replicateModel": "black-forest-labs/flux-dev-lora",
    "capabilities": {
      "supportsLora": true,
      "maxImages": 4
    },
    "settings": [
      {"key": "num_inference_steps", "label": "Steps", "type": "range", "min": 10, "max": 50, "default": 28},
      {"key": "guidance_scale", "label": "Guidance", "type": "range", "min": 1, "max": 10, "step": 0.5, "default": 3.5},
      {"key": "aspect_ratio", "label": "Aspect Ratio", "type": "select", "options": ["1:1", "16:9", "9:16"], "default": "1:1"}
    ]
  }
}
```

**To add a new model:** Add an entry with capabilities and settings schema. The frontend auto-generates forms.

#### 1.3 API Endpoints (Aligned with existing patterns)

| Route | Purpose |
|-------|---------|
| `GET /api/models/list` | List available models with settings |
| `POST /api/asset-types/create` | Create Asset Type |
| `GET /api/asset-types/list` | List active Asset Types |
| `GET /api/asset-types/get?id=X` | Get single Asset Type |
| `POST /api/asset-types/update` | Update Asset Type |
| `DELETE /api/asset-types/delete?id=X` | Soft-delete Asset Type |
| `POST /api/generations/create` | Create generation record |
| `GET /api/generations/list` | List generations (supports `?favorite=true`) |
| `POST /api/generations/toggle-favorite` | Toggle favorite |
| `DELETE /api/generations/delete?id=X` | Hard delete generation |

**Error Responses:** Follow existing pattern `{ success: false, error: "message" }`

---

### Phase 2: Director Mode UI

#### 2.1 Director Page Layout
- Left sidebar: Asset Types list with "New" button
- Main panel: Asset Type editor form
- Tab: "LoRAs" (existing functionality)

#### 2.2 Dynamic Settings Form
- `app/components/dynamic-form.js` renders inputs from model schema
- Supports: range, select, checkbox, number input types

#### 2.3 LoRA Picker
- Dropdown of LoRAs with status "completed" or "deployed"
- Only shown when selected model has `supportsLora: true`

---

### Phase 3: User Mode UI

#### 3.1 History Sidebar
- Left column with thumbnails + prompts
- Actions: favorite toggle, delete, regenerate
- Favorites filter at top
- Loads on page init, updates after each generation

#### 3.2 Combined Prompt Builder

**Display:** `[pre-prompt] [editable textarea] [post-prompt]`
- Pre/post shown as grayed-out labels (visible even when empty)
- Editable middle portion is what user types

**Concatenation Rules:**
- Empty pre/post: omit entirely (no leading/trailing space)
- Formula: `"{pre} {user} {post}".strip()`
- Validation: userPrompt required, min 1 char, max 500 chars

#### 3.3 Simplified Controls
- Asset Type dropdown (populated from API)
- Quality selector (if Asset Type allows choice)
- Generate button

---

### Phase 4: Polish

#### 4.1 Auth Placeholder
- `localStorage.getItem('noisett_isDirector') === 'true'`
- Set via URL param: `?director=true` saves to localStorage
- Director nav link shown when flag is true

#### 4.2 Migration Note
- **Greenfield**: No existing generations table, no migration needed
- Existing hardcoded Asset Types become seeded rows

---

## Task Breakdown (GitHub Issues)

### Wave 1: Backend (No Dependencies)

| # | Title | Estimate | Dependencies |
|---|-------|----------|--------------|
| 1 | Add assetTypes and generations tables to Convex schema | 1h | - |
| 2 | Create models.json registry with FLUX dev-lora entry | 1h | - |
| 3 | Add registry.py loader and GET /api/models endpoint | 1h | #2 |
| 4 | Add Convex HTTP routes for Asset Types CRUD | 2h | #1 |
| 5 | Add Convex HTTP routes for Generations CRUD | 2h | #1 |

### Wave 2: Director UI (Depends on Wave 1)

| # | Title | Estimate | Dependencies |
|---|-------|----------|--------------|
| 6 | Create director.html + director.js with sidebar layout | 2h | #4 |
| 7 | Build dynamic-form.js component from schema | 2h | #3, #6 |
| 8 | Integrate LoRA picker in Asset Type editor | 1h | #6, #7 |
| 9 | Move LoRA management tab to Director mode | 1h | #6 |

### Wave 3: User UI (Depends on Wave 1)

| # | Title | Estimate | Dependencies |
|---|-------|----------|--------------|
| 10 | Refactor index.html with history sidebar layout | 2h | #5 |
| 11 | Build combined prompt builder component | 1h | #4, #10 |
| 12 | Connect generation to Asset Type settings | 2h | #4, #5, #11 |
| 13 | Add history actions (favorite, delete, regenerate) | 1h | #10 |

### Wave 4: Polish (Depends on Waves 2 & 3)

| # | Title | Estimate | Dependencies |
|---|-------|----------|--------------|
| 14 | Implement auth placeholder (localStorage + URL param) | 30m | #6 |
| 15 | Seed default Asset Types on first run | 30m | #4 |
| 16 | End-to-end testing and bug fixes | 2h | All |

---

## Verification Plan

### Automated (pytest)
- [ ] `test_model_registry_loader()` - loads models.json, returns valid structure
- [ ] `test_combined_prompt_builder()` - "{pre} {user} {post}" concatenation with edge cases
- [ ] `test_asset_type_crud()` - create, read, update, soft-delete via API
- [ ] `test_generation_crud()` - create, list, favorite toggle, delete
- [ ] `test_generation_with_orphaned_asset_type()` - handles deleted Asset Type gracefully

### Manual Browser Testing
1. Director: Create Asset Type with custom pre/post prompt → verify saves
2. Director: Select model → verify settings form updates dynamically
3. Director: Select LoRA → verify only shown when model supports it
4. User: Select Asset Type → verify combined prompt preview
5. User: Generate → verify image appears in history
6. User: Favorite/delete/regenerate → verify actions work
7. Edge case: Empty pre/post prompt → verify no extra whitespace

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Asset Type ownership? | Global for now |
| Delete behavior? | Soft delete (isActive: false) |
| Auth mechanism? | localStorage + URL param |
| Migration? | Greenfield, no migration |
