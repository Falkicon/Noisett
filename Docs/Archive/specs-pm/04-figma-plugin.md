# v2.2: Figma Plugin

**Status:** Future (post v2.1)

**Target:** March 2026

**Dependency:** v2.1 Quality & Polish complete

---

## Goals

1. Bring asset generation into designers' existing workflow
2. Eliminate context-switching between generation tool and design tool
3. Enable direct insertion of generated assets onto Figma canvas

---

## User Stories

### US-1: Generate from Figma

**As a** designer working in Figma

**I want to** generate assets without leaving Figma

**So that** I can stay in my workflow

**Acceptance Criteria:**

- [ ]  Figma plugin panel accessible from Plugins menu
- [ ]  Same prompt input and generate flow as web app
- [ ]  Results displayed in plugin panel

### US-2: Insert to canvas

**As a** designer who has generated an image

**I want to** click to insert it directly onto my canvas

**So that** I don't have to download and re-import

**Acceptance Criteria:**

- [ ]  Each result thumbnail has "Insert" button
- [ ]  Clicking insert places image at current selection or center of viewport
- [ ]  Image is inserted as a Figma image fill or image node

### US-3: Quick regenerate

**As a** designer iterating on an asset

**I want to** quickly generate more variations

**So that** I can find the right one without retyping

**Acceptance Criteria:**

- [ ]  "More" button generates 4 new variations
- [ ]  Previous results remain accessible (scroll or tabs)

### US-4: Access history in Figma

**As a** designer

**I want to** see my recent generations in the plugin

**So that** I can re-use something I generated earlier

**Acceptance Criteria:**

- [ ]  "Recent" tab shows last 20 generations
- [ ]  Can insert any historical image to canvas
- [ ]  Synced with web app history

---

## Functional Requirements

### FR-1: Plugin Core

| ID | Requirement |
| --- | --- |
| FR-1.1 | Figma plugin manifest and TypeScript codebase |
| FR-1.2 | Plugin panel UI (300px width standard) |
| FR-1.3 | Prompt input, asset type selector, generate button |
| FR-1.4 | Loading state during generation |
| FR-1.5 | 2×2 thumbnail grid for results |

### FR-2: Authentication

| ID | Requirement |
| --- | --- |
| FR-2.1 | OAuth flow with same Entra ID as web app |
| FR-2.2 | Token stored securely in Figma client storage |
| FR-2.3 | "Sign in" button if not authenticated |
| FR-2.4 | Session persists across Figma restarts |

### FR-3: Canvas Integration

| ID | Requirement |
| --- | --- |
| FR-3.1 | Insert image as Figma Image node |
| FR-3.2 | Image inserted at current selection position, or canvas center if no selection |
| FR-3.3 | Inserted image is 1024×1024 (or asset type default) |
| FR-3.4 | Option to insert as image fill on selected shape |

### FR-4: History Integration

| ID | Requirement |
| --- | --- |
| FR-4.1 | Fetch history from same API as web app |
| FR-4.2 | Display recent generations in "History" tab |
| FR-4.3 | Allow insert from history |

---

## UI Wireframe

```
┌─────────────────────────────────────┐
│  Brand Asset Generator        [×]  │
├─────────────────────────────────────┤
│  [Generate]  [History]  [Settings]  │
├─────────────────────────────────────┤
│                                     │
│  Asset Type:                        │
│  ┌─────────────────────────────┐   │
│  │ Product Illustrations    ▼  │   │
│  └─────────────────────────────┘   │
│                                     │
│  Describe your asset:               │
│  ┌─────────────────────────────┐   │
│  │ A person working on a      │   │
│  │ laptop with floating       │   │
│  │ design elements            │   │
│  └─────────────────────────────┘   │
│                                     │
│  Quality: ○ Draft  ● Std  ○ High   │
│                                     │
│  [ Generate (4 images) ]            │
│                                     │
├─────────────────────────────────────┤
│  Results:                           │
│  ┌───────┐ ┌───────┐               │
│  │       │ │       │               │
│  │  img  │ │  img  │               │
│  │ [Ins] │ │ [Ins] │               │
│  └───────┘ └───────┘               │
│  ┌───────┐ ┌───────┐               │
│  │       │ │       │               │
│  │  img  │ │  img  │               │
│  │ [Ins] │ │ [Ins] │               │
│  └───────┘ └───────┘               │
│                                     │
│  [ Generate More ]                  │
│                                     │
└─────────────────────────────────────┘
```

---

## Technical Notes

### Figma Plugin Development

- TypeScript + Figma Plugin API
- Use `figma.createImage()` for image insertion
- HTTP requests to existing FastAPI backend
- Same REST API as web app (no new endpoints needed)

### Authentication Challenge

- Figma plugins can't do standard OAuth redirect flow
- Options:
    1. Open browser for auth, callback to plugin via deep link
    2. Device code flow (user enters code on web)
    3. API key per user (less secure but simpler)
- Recommend: Device code flow for security

### Figma Plugin Distribution

- Internal only: Use Figma Organization's private plugins
- No public marketplace listing needed

---

## Dependencies

| Dependency | Notes |
| --- | --- |
| v2.1 complete | Need history API |
| Figma Organization account | For private plugin distribution |
| Device code flow in auth | New auth flow implementation |

---

## Out of Scope (v2.2)

- Figma design system sync
- Component replacement
- Batch generation in plugin
- Offline support