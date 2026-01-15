# Director Mode Proposal

**Status:** READY

## Problem Statement

Noisett currently has a flat UI where all users configure generation parameters (model, LoRA, prompts) directly. This creates two problems:

1. **Complexity for end users** - They must understand model differences, LoRA selection, and prompt engineering
2. **No brand governance** - No way to enforce consistent styles/prompts across a team

## Proposed Solution

Split the UI into two modes:

### Director Mode (Admin)
Configure "Asset Types" that bundle together:
- Pre/post prompt templates (auto-added around user input)
- Image model with locked settings
- LoRA binding (if model supports)
- Quality preset (optional lock)

### User Mode (Everyone)
Simplified generation flow:
- Pick an Asset Type (pre-configured by Director)
- Enter only the editable prompt portion
- See combined prompt preview: `[pre] [your text] [post]`
- History sidebar with favorites, delete, regenerate

### Modular Model Registry
JSON config (`models.json`) for easy extension:
- Add new Replicate models by adding a JSON entry
- Auto-generate settings forms from schema
- No code changes needed for new models

## NOT IN SCOPE (Do Not Critique)

- Detailed implementation specifics (that's for the spec)
- Authentication system (placeholder for now)
- Multi-tenant/team features
- Billing/quotas

## Phasing

**Phase 1: Data Model & Backend**
- Convex schema: `assetTypes`, `generations` tables
- Model registry JSON + Python loader
- API endpoints for CRUD

**Phase 2: Director Mode UI**
- Separate `director.html` page
- Asset Type editor with dynamic model settings form
- LoRA picker integration

**Phase 3: User Mode UI**
- History sidebar layout
- Combined prompt builder
- Simplified generation flow

**Phase 4: Polish**
- Auth placeholder (isDirector flag)
- Responsive layout
- End-to-end testing

## Open Questions

- [x] Model settings: Auto-detect or hardcode? → **JSON config, easily extensible**
- [x] Quality: User selectable? → **Can be locked per Asset Type**
- [x] History storage: Convex or local? → **Convex (persistent)**

## References

- [Implementation Plan](file:///C:/Users/jasfalk/.gemini/antigravity/brain/65f48ce9-67b9-4596-8160-df29f5287212/implementation_plan.md)
- [AFD Forge Pattern](file:///d:/Github/lushly-dev/AFD/demos/todo/) - Sidebar + main panel layout reference
