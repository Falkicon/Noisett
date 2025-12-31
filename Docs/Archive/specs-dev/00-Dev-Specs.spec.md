# Dev Specs

Developer specifications and implementation plan for the Brand Asset Generator. This document provides everything needed to build the system.

---

## Spec Index

[Architecture & System Design](Architecture%20&%20System%20Design%2068064eb08d024d40b22083f1faf1877d.md)

[API Specification](API%20Specification%208b58daec7a9c40b1925becfcbbf9fadc.md)

[Frontend Implementation](Frontend%20Implementation%208e84dab011c8403ba498f33d0c5ddc36.md)

[ML Pipeline & Model Integration](ML%20Pipeline%20&%20Model%20Integration%20e5ae7b02cfe8425ba0b8a5b59f8a0f2b.md)

[Infrastructure & Deployment](Infrastructure%20&%20Deployment%205d8b23ccf4da4400aa8fcc0170b06fd6.md)

[Development Environment Setup](Development%20Environment%20Setup%2080aedf279be646ec91ae75347573daac.md)

---

## Tech Stack Summary

| Layer | Technology | Rationale |
| --- | --- | --- |
| Frontend | React 18 + TypeScript | Type safety, modern tooling, team familiarity |
| Backend | FastAPI (Python 3.11) | Async support, ML ecosystem compatibility |
| ML Runtime | PyTorch + Diffusers | HuggingFace ecosystem, LoRA support |
| Auth | Microsoft Entra ID (MSAL) | Corporate SSO requirement |
| Storage | Azure Blob Storage | Cost-effective, CDN integration |
| Compute | Azure Container Apps (GPU) | Serverless scaling, cost optimization |
| Database | SQLite (MVP) → PostgreSQL (v2) | Simple start, scale when needed |

---

## Implementation Phases

### Phase 1: MVP (January 2026)

- Single model (HiDream-I1)
- Single asset type (Product Illustrations)
- Core generation API
- Basic web UI
- Azure AD authentication

### Phase 2: Multi-Model (February 2026)

- Add FLUX, SD 3.5 models
- 4 asset types with dedicated LoRAs
- Model selection UI
- Licensing warnings

### Phase 3: Quality & Polish (February-March 2026)

- Quality presets
- Generation history
- Favorites
- Batch generation
- PostgreSQL migration

### Phase 4: Figma Plugin (March 2026)

- Figma plugin TypeScript codebase
- Device code auth flow
- Canvas integration

---

## Related Documents

- [PM Specs](https://www.notion.so/PM-Specs-2d779be0f2c5801aacd0dc2b62a52471?pvs=21) — Functional requirements and user stories
- [Design Specs](https://www.notion.so/Design-Specs-2d779be0f2c580f28d79c687a3a2ae9d?pvs=21) — UI specifications and design tokens
- [Image generation strategy](https://www.notion.so/Image-generation-strategy-2d779be0f2c5801999d0da7ec96575de?pvs=21) — Research and technical strategy