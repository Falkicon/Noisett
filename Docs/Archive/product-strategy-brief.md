# Product Strategy Brief

**Project:** Brand Asset Generator

**Author:** Jason Falk

**Date:** December 2025

**Status:** Seeking approval for MVP development

---

## Executive Summary

We propose building an internal tool that generates on-brand illustrations and icons using AI, trained on our existing design assets. This replaces the current manual workflow where designers create each asset from scratch or adapt existing ones.

**What we're asking for:**

- Approval to build an MVP in January 2026
- ~$20/month in Azure compute costs
- Engineering team consideration for long-term ownership if MVP succeeds

---

## Problem Statement

Our design studio currently creates brand illustrations manually. When teams need new assets:

- Designers spend time on repetitive work (similar illustrations, icon variants)
- Turnaround can be slow when designers are at capacity
- Consistency varies depending on which designer creates the asset

This isn't a crisis — our current process works. But there's an opportunity to give designers a tool that handles routine generation, freeing them for higher-value creative work.

---

## Proposed Solution

Build an internal web tool where anyone in the studio can:

1. Describe the asset they need in plain language
2. Select the asset type (icon, product illustration, etc.)
3. Generate multiple options in ~30 seconds
4. Download and use directly, or hand off to a designer for refinement

The AI is trained on our existing brand assets, so outputs match our style without manual guidance.

---

## Why Now

- **Technology maturity:** Open-source image generation models (HiDream, FLUX) now produce quality suitable for production use
- **Low barrier:** We can self-host on Azure with minimal ongoing cost
- **Low risk:** MVP can be built by one person in one month; easy to abandon if it doesn't work

---

## Scope

### MVP (January 2026)

| Included                               | Not Included         |
| -------------------------------------- | -------------------- |
| Web UI with basic generation           | Figma plugin         |
| One asset type (Product Illustrations) | Multiple asset types |
| One AI model (HiDream)                 | Model comparison     |
| Download generated images              | History, favorites   |
| Entra ID authentication                | Public access        |

### Future (If MVP Succeeds)

- Additional asset types: Icons, Logo Illustrations, Premium Illustrations
- Figma plugin for in-workflow generation
- Multiple models for quality comparison

---

## Costs

### Development

| Item               | Cost                                    |
| ------------------ | --------------------------------------- |
| MVP build          | ~4 weeks of Jason's time                |
| Training data prep | ~1 day (designer time to select assets) |

### Ongoing (Monthly)

| Item                | Est. Cost      | Notes                                     |
| ------------------- | -------------- | ----------------------------------------- |
| Azure compute (GPU) | $5-20          | Scale-to-zero; pay only during generation |
| Storage             | <$5            | Model weights, generated images           |
| **Total**           | **~$20/month** | At 10-100 images/month usage              |

No licensing fees required — we're using Apache 2.0 licensed models.

---

## Risks & Mitigations

| Risk                            | Likelihood | Mitigation                                                   |
| ------------------------------- | ---------- | ------------------------------------------------------------ |
| Output quality doesn't meet bar | Medium     | Start with one asset type; gather feedback before expanding  |
| Low adoption                    | Medium     | Build Figma plugin in v2 to meet designers where they work   |
| Model licensing changes         | Low        | Using Apache 2.0 model (HiDream); no commercial restrictions |
| Training data insufficient      | Low        | We have extensive existing brand assets to train on          |

---

## Success Criteria

We'll consider the MVP successful if:

- [ ] Tool produces usable outputs (designer approval on sample set)
- [ ] At least 5 team members try it in the first month
- [ ] Qualitative feedback is positive ("this is useful" vs "this isn't worth the effort")

We're explicitly **not** committing to:

- Time savings metrics (hard to measure accurately)
- Adoption targets (team is small, usage will be intermittent)
- Quality comparisons to manual work (apples to oranges)

---

## Timeline

| Milestone                  | Target          |
| -------------------------- | --------------- |
| Gather training assets     | Jan 6-10, 2026  |
| Train model, build backend | Jan 13-17, 2026 |
| Build web UI               | Jan 20-24, 2026 |
| Testing & soft launch      | Jan 27-31, 2026 |

---

## Team

| Role                   | Person                             |
| ---------------------- | ---------------------------------- |
| MVP development        | Jason Falk                         |
| Training data curation | TBD (designer)                     |
| Long-term ownership    | Engineering team (if MVP succeeds) |

---

## Decision Requested

**Approve** Jason to proceed with MVP development starting January 6, 2026.

If the MVP demonstrates value, we'll return with a proposal for v2 features and potential Engineering team handoff.
