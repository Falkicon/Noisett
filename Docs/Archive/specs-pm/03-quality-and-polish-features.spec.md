# v2.1: Quality & Polish Features

**Status:** Future (post v2.0)

**Target:** February-March 2026

**Dependency:** v2.0 Multi-Model complete

---

## Goals

1. Give users control over generation quality vs. speed tradeoff
2. Enable users to track and revisit previous generations
3. Improve output quality through post-processing

---

## User Stories

### US-1: Choose quality preset

**As a** user

**I want to** choose between fast/draft and slow/high-quality generation

**So that** I can iterate quickly during ideation and get polished output for final use

**Acceptance Criteria:**

- [ ]  Quality selector with 3-4 options
- [ ]  Each preset shows estimated generation time
- [ ]  Higher quality uses more inference steps and optional upscaling

### US-2: View generation history

**As a** user

**I want to** see my previous generations

**So that** I can revisit and download images I generated earlier

**Acceptance Criteria:**

- [ ]  History sidebar or tab showing past generations
- [ ]  Each entry shows prompt, thumbnail, timestamp
- [ ]  Clicking an entry shows full results
- [ ]  History persists across sessions (stored server-side)

### US-3: Save favorites

**As a** user

**I want to** mark images as favorites

**So that** I can quickly find my best generations later

**Acceptance Criteria:**

- [ ]  Star/heart button on each generated image
- [ ]  Favorites section in history view
- [ ]  Favorites persist across sessions

### US-4: Batch generation

**As a** user who needs multiple assets

**I want to** queue several prompts at once

**So that** I don't have to wait and submit one at a time

**Acceptance Criteria:**

- [ ]  Multi-line prompt input or "Add another" button
- [ ]  Queue shows pending prompts and progress
- [ ]  All results downloadable as ZIP

---

## Functional Requirements

### FR-1: Quality Presets

| Preset | Steps | Upscale | Est. Time | Use Case |
| --- | --- | --- | --- | --- |
| Draft | 15 | No | ~10 sec | Quick ideation |
| Standard | 28 | No | ~25 sec | Most use cases |
| High | 40 | 2× | ~45 sec | Final assets |
| Ultra | 50 | 4× + refiner | ~90 sec | Hero images, print |

### FR-2: History

| ID | Requirement |
| --- | --- |
| FR-2.1 | Store generation history per user |
| FR-2.2 | Retain history for 90 days |
| FR-2.3 | Display last 50 generations in sidebar |
| FR-2.4 | Support search/filter by prompt text |
| FR-2.5 | Allow deletion of history items |

### FR-3: Favorites

| ID | Requirement |
| --- | --- |
| FR-3.1 | Toggle favorite status on any generated image |
| FR-3.2 | Favorites view shows all starred images |
| FR-3.3 | Favorites have no auto-expiration (persist until removed) |

### FR-4: Batch Generation

| ID | Requirement |
| --- | --- |
| FR-4.1 | Accept up to 10 prompts in a single batch |
| FR-4.2 | Process prompts sequentially (not parallel) to manage GPU |
| FR-4.3 | Show progress as each prompt completes |
| FR-4.4 | "Download All" button exports ZIP of all results |

---

## Technical Notes

### Database Schema Additions

```
User
  - id
  - email
  - created_at

Generation (expand from Job)
  - id
  - user_id (FK)
  - prompt
  - asset_type
  - model
  - quality_preset
  - status
  - created_at
  - images[]

Favorite
  - id
  - user_id (FK)
  - generation_id (FK)
  - image_index
  - created_at
```

### Storage Considerations

- History requires persistent storage of generated images
- Estimate: 100 images/user × 100 users × 1MB = 10GB
- Use Azure Blob with lifecycle policy for auto-cleanup

---

## Dependencies

| Dependency | Notes |
| --- | --- |
| v2.0 complete | Build on expanded model/asset support |
| Database (Postgres or Cosmos) | For history, favorites storage |
| Expanded blob storage | For persistent image retention |

---

## Out of Scope (v2.1)

- IP-Adapter (reference image input) → Consider for v2.3
- ControlNet (sketch-to-image) → Consider for v2.3
- Real-time collaboration → Not planned