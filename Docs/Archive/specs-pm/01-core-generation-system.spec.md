# Core Generation System

**Status:** Active development

**Target:** January 2026

**Owner:** Jason Falk

---

## Goals

1. Deliver a working end-to-end image generation system trained on brand assets
2. Enable any studio member to generate on-brand illustrations via a web interface
3. Validate the approach before investing in additional features

---

## User Stories

### US-1: Generate an illustration

**As a** studio team member

**I want to** describe an illustration I need and generate options

**So that** I can quickly get on-brand assets without waiting for a designer

**Acceptance Criteria:**

- [ ] User can enter a text description of the desired image
- [ ] User can click "Generate" and see a loading state
- [ ] System generates 4 image variations within 60 seconds
- [ ] User sees all 4 images displayed in a grid

### US-2: Download generated images

**As a** user who has generated images

**I want to** download the images I like

**So that** I can use them in my work

**Acceptance Criteria:**

- [ ] Each generated image has a download button
- [ ] Clicking download saves the full-resolution PNG
- [ ] User can download multiple images from the same generation

### US-3: Regenerate with same prompt

**As a** user who isn't satisfied with the initial results

**I want to** generate more variations without retyping my prompt

**So that** I can quickly iterate until I find something I like

**Acceptance Criteria:**

- [ ] "Generate More" button appears after initial generation
- [ ] Clicking it generates 4 new variations with the same prompt
- [ ] Previous results remain visible (or user can scroll back)

### US-4: Authentication

**As an** admin

**I want** only authorized studio members to access the tool

**So that** we control who can use our compute resources

**Acceptance Criteria:**

- [ ] Users must sign in with Microsoft Entra ID
- [ ] Unauthenticated users are redirected to sign-in
- [ ] Only users in the studio's Azure AD group can access

---

## Functional Requirements

### FR-1: Image Generation

| ID     | Requirement                                                     |
| ------ | --------------------------------------------------------------- |
| FR-1.1 | System accepts text prompts up to 500 characters                |
| FR-1.2 | System generates exactly 4 image variations per request         |
| FR-1.3 | Generated images are 1024×1024 pixels                           |
| FR-1.4 | Generation completes within 60 seconds under normal load        |
| FR-1.5 | System applies brand LoRA automatically (no user configuration) |

### FR-2: User Interface

| ID     | Requirement                                             |
| ------ | ------------------------------------------------------- |
| FR-2.1 | Single-page web application                             |
| FR-2.2 | Text input field for prompt                             |
| FR-2.3 | "Generate" button to initiate generation                |
| FR-2.4 | Loading state with progress indicator during generation |
| FR-2.5 | 2×2 grid display of generated images                    |
| FR-2.6 | Download button on each image                           |
| FR-2.7 | "Generate More" button to create additional variations  |

### FR-3: Authentication & Authorization

| ID     | Requirement                                             |
| ------ | ------------------------------------------------------- |
| FR-3.1 | Microsoft Entra ID (Azure AD) integration               |
| FR-3.2 | Restrict access to specified Azure AD group             |
| FR-3.3 | Session persistence (don't require re-login on refresh) |

---

## Non-Functional Requirements

| ID    | Requirement      | Target                                    |
| ----- | ---------------- | ----------------------------------------- |
| NFR-1 | Availability     | Best-effort (internal tool, no SLA)       |
| NFR-2 | Cold start time  | <60 seconds (acceptable for internal use) |
| NFR-3 | Concurrent users | Support 5 simultaneous generations        |
| NFR-4 | Image storage    | 30-day retention, then auto-delete        |
| NFR-5 | Cost             | <$50/month at expected usage              |

---

## Technical Architecture

### Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Web UI  │────▶│  FastAPI        │────▶│  HiDream Model  │
│   (Static Web   │     │  Backend        │     │  + Brand LoRA   │
│   Apps)         │◀────│  (Container     │     │  (GPU)          │
└─────────────────┘     │  Apps)          │     └─────────────────┘
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Azure Blob     │
                        │  Storage        │
                        └─────────────────┘
```

### API Endpoints

| Method | Endpoint                | Description                               |
| ------ | ----------------------- | ----------------------------------------- |
| POST   | `/generate`             | Submit generation request, returns job_id |
| GET    | `/jobs/{id}`            | Get job status and results                |
| GET    | `/jobs/{id}/images/{n}` | Download specific image                   |

### Data Model

**Job**

- `id`: UUID
- `prompt`: string
- `status`: enum (queued, processing, complete, failed)
- `created_at`: timestamp
- `completed_at`: timestamp (nullable)
- `images`: array of image URLs
- `user_id`: string (from auth)

---

## Out of Scope (MVP)

The following are explicitly **not** included in MVP:

- Multiple asset types (only Product Illustrations)
- Multiple models (only HiDream)
- Quality presets (Draft/Standard/High)
- Generation history beyond current session
- Favorites or saved images
- Figma plugin
- Batch generation
- Image editing or refinement

---

## Dependencies

| Dependency                                  | Owner         | Status        |
| ------------------------------------------- | ------------- | ------------- |
| Azure subscription with GPU quota           | IT/Cloud team | ✅ Available  |
| Training data (30-50 product illustrations) | Design team   | ⏳ Jan 6-10   |
| Azure AD app registration                   | IT            | ⏳ To request |

---

## Open Questions

1. **Who will curate training data?** Need to identify a designer to select 30-50 representative images.
2. **What Azure AD group for access?** Need group name or creation.
3. **Where to host?** Confirm Azure subscription/resource group.

---

## Success Metrics

| Metric                        | Target                         | Measurement                              |
| ----------------------------- | ------------------------------ | ---------------------------------------- |
| Tool produces usable output   | Subjective designer approval   | Designer review of 10 sample generations |
| Team members try the tool     | ≥5 unique users in first month | Auth logs                                |
| Qualitative feedback positive | "Useful" sentiment             | Informal feedback                        |

---

## Timeline

| Week      | Milestone                                      |
| --------- | ---------------------------------------------- |
| Jan 6-10  | Gather training assets, set up Azure resources |
| Jan 13-17 | Train LoRA, build FastAPI backend              |
| Jan 20-24 | Build React web UI, integrate auth             |
| Jan 27-31 | Integration testing, soft launch               |
