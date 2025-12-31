# Phase 7: Figma Plugin

**Status:** 🔜 Planned  
**Dependencies:** Phase 4 (Deployment) ✅

---

## Goal

> Bring generation to designers where they work — directly in Figma.

The original strategy emphasized:

> "Figma-specific win: Designers can generate, compare, and insert without leaving their workflow. No copy-paste, no downloads, no context switching."

---

## Why Figma Plugin?

| Web UI                     | Figma Plugin              |
| -------------------------- | ------------------------- |
| Context switch to browser  | In-workflow               |
| Download → Upload to Figma | Insert directly to canvas |
| Separate from design files | Lives with your work      |
| Anyone can use             | Designers' primary tool   |

---

## Core Features (MVP)

### 1. Generate from Panel

```
┌─────────────────────────────────────┐
│  Noisett                        ☰  │
├─────────────────────────────────────┤
│                                     │
│  Asset Type:  [Icons ▼]             │
│                                     │
│  Describe what you need:            │
│  ┌─────────────────────────────┐    │
│  │ cloud computing concept    │    │
│  └─────────────────────────────┘    │
│                                     │
│  Quality:  ○ Draft  ● Standard      │
│                                     │
│  [ Generate 4 ]                     │
│                                     │
├─────────────────────────────────────┤
│  Results:                           │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │     │ │     │ │     │ │     │   │
│  │ ★   │ │     │ │     │ │     │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│                                     │
│  Click image to insert to canvas    │
│                                     │
│  [ Generate More ]                  │
│                                     │
└─────────────────────────────────────┘
```

### 2. Insert to Canvas

Click an image → Inserted as a new frame at cursor position or selection.

### 3. Recent Generations

Quick access to previous generations without re-generating.

---

## User Flow

```
1. Designer opens Noisett panel in Figma
2. Selects asset type (Icons, Product, Logo, Premium)
3. Types simple description
4. Clicks "Generate 4"
5. Waits ~10-20 seconds, sees spinner
6. Views 4 thumbnail results
7. Clicks favorite → Image inserted onto Figma canvas
8. Can click "Generate More" for new variations
9. Recent history available in panel
```

---

## Technical Architecture

### Plugin ↔ Backend

```
┌─────────────────────┐
│   Figma Plugin      │
│   (TypeScript)      │
├─────────────────────┤
│  - UI (HTML/CSS)    │
│  - Figma Plugin API │
│  - Auth storage     │
└──────────┬──────────┘
           │
           │ HTTPS (REST API)
           ▼
┌─────────────────────┐
│   Noisett Backend   │
│   (FastAPI)         │
├─────────────────────┤
│  POST /api/generate │
│  GET /api/jobs/{id} │
│  GET /api/images/   │
└─────────────────────┘
```

### Figma Plugin API Usage

```typescript
// Insert generated image to canvas
const imageBytes = await fetch(imageUrl).then((r) => r.arrayBuffer());
const imageHash = figma.createImage(new Uint8Array(imageBytes)).hash;

const frame = figma.createFrame();
frame.name = "Generated: cloud computing";
frame.resize(1024, 1024);
frame.fills = [
  {
    type: "IMAGE",
    imageHash: imageHash,
    scaleMode: "FILL",
  },
];

// Position at viewport center or selection
const center = figma.viewport.center;
frame.x = center.x - frame.width / 2;
frame.y = center.y - frame.height / 2;

// Select the new frame
figma.currentPage.selection = [frame];
```

---

## Authentication

### Options

1. **Entra ID OAuth** — Corporate SSO, same as web UI
2. **API Key** — Simple, stored in Figma plugin storage
3. **Session Token** — Login once via web, paste token to plugin

**Recommendation:** Start with API key for simplicity. Add OAuth later.

```typescript
// Store API key in Figma's client storage
await figma.clientStorage.setAsync("noisett_api_key", apiKey);

// Retrieve for API calls
const apiKey = await figma.clientStorage.getAsync("noisett_api_key");
```

---

## Plugin Structure

```
figma-plugin/
├── manifest.json          # Figma plugin manifest
├── package.json
├── tsconfig.json
├── src/
│   ├── code.ts            # Main plugin code (Figma API)
│   ├── ui.html            # Plugin UI
│   ├── ui.ts              # UI logic
│   ├── api.ts             # Backend API client
│   └── types.ts           # TypeScript types
└── dist/                  # Built output
```

### manifest.json

```json
{
  "name": "Noisett",
  "id": "noisett-brand-generator",
  "api": "1.0.0",
  "main": "dist/code.js",
  "ui": "dist/ui.html",
  "editorType": ["figma"],
  "networkAccess": {
    "allowedDomains": [
      "https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io"
    ]
  }
}
```

---

## UI Design

### States

**Empty State:**

```
No recent generations.
Enter a prompt above to get started.
```

**Loading State:**

```
Generating... (12s)
[████████░░░░░░░░] 50%
```

**Results State:**

```
4 images • Click to insert
[img] [img] [img] [img]
```

**Error State:**

```
⚠️ Generation failed
API error: Rate limit exceeded
[Try Again]
```

### Styling

Match Figma's design language:

- Font: Inter (Figma's default)
- Colors: Figma's UI colors
- Spacing: 8px grid
- Buttons: Figma-style buttons

---

## Commands (Backend Support)

The existing commands support Figma integration:

```bash
# Generate (already implemented)
POST /api/generate
{
  "prompt": "cloud computing",
  "asset_type": "icons",
  "count": 4
}

# Check status (already implemented)
GET /api/jobs/{job_id}

# Get image (already implemented)
GET /api/images/{filename}
```

No new backend commands needed for MVP.

---

## MVP Scope

### Included

- [x] Generate images from prompt
- [x] Select asset type
- [x] View 4 results
- [x] Insert to canvas on click
- [x] API key auth
- [x] Loading states
- [x] Error handling

### Not Included (v2)

- [ ] OAuth/Entra ID auth
- [ ] Generation history
- [ ] Favorites
- [ ] "More like this" from selection
- [ ] Batch generation
- [ ] Quality presets

---

## Development Setup

### Prerequisites

- Node.js 18+
- Figma Desktop app
- Figma account

### Local Development

```bash
cd figma-plugin
pnpm install
pnpm dev  # Watches and rebuilds

# In Figma Desktop:
# Plugins → Development → Import plugin from manifest
# Select figma-plugin/manifest.json
```

### Building

```bash
pnpm build  # Creates dist/
```

### Publishing

1. Test thoroughly in development mode
2. Create Figma organization account (if needed)
3. Submit via Figma Plugin submission flow
4. Internal distribution via organization

---

## Pydantic Schemas (Backend)

No new schemas needed — existing generate endpoint supports plugin.

---

## TypeScript Types (Plugin)

```typescript
interface GenerateRequest {
  prompt: string;
  asset_type: "icons" | "product" | "logo" | "premium";
  count?: number;
}

interface GenerateResponse {
  success: boolean;
  data?: {
    job_id: string;
  };
  error?: {
    code: string;
    message: string;
  };
}

interface JobStatus {
  success: boolean;
  data?: {
    status: "queued" | "processing" | "complete" | "failed";
    images?: string[];
  };
}

interface PluginSettings {
  api_key: string;
  default_asset_type: string;
  default_count: number;
}
```

---

## Success Criteria

- [ ] Plugin installs and loads in Figma
- [ ] Can enter prompt and generate images
- [ ] Results display in panel
- [ ] Clicking image inserts to canvas
- [ ] Auth persists across sessions
- [ ] Errors shown clearly to user
- [ ] Works with existing backend (no changes)

---

## Timeline Estimate

| Task               | Effort         |
| ------------------ | -------------- |
| Plugin scaffolding | 1 day          |
| UI implementation  | 2-3 days       |
| API integration    | 1 day          |
| Canvas insertion   | 1 day          |
| Auth flow          | 1 day          |
| Polish + testing   | 2 days         |
| **Total**          | **~1.5 weeks** |

---

## Related Documents

- [Original Strategy: Figma Plugin](../Archive/image-generation-strategy.md#frontend-2-figma-plugin)
- [Original Strategy: Multi-Frontend Architecture](../Archive/image-generation-strategy.md#multi-frontend-architecture)
- [Figma Plugin API Docs](https://www.figma.com/plugin-docs/)
