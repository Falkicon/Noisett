# Director Mode Specification Review

**Reviewed:** 2026-01-14
**Spec:** director-mode.spec.md
**Reviewer:** Claude Code

---

## VERDICT: APPROVED WITH MINOR REVISIONS

The specification is implementation-ready with a clear task breakdown and solid architecture. The concerns from the proposal review have been addressed. A few refinements would strengthen testability and reduce implementation risk.

---

## STRENGTHS

### 1. Addressed All Proposal Review Concerns
The spec successfully resolves every concern raised in the proposal review:
- **Asset Type lifecycle:** Clearly defined as global, soft-delete via `isActive: false`, orphaned generations are OK
- **Auth placeholder contract:** Documented as `localStorage` + URL param (`?director=true`)
- **Migration path:** Explicitly stated as greenfield with no migration needed
- **Open Questions table:** All decisions documented and justified

### 2. Well-Defined Data Model
The Convex schema is concrete and complete:
- `assetTypes` table with proper indexing (`by_active`)
- `generations` table with indexes for favorites and chronological access
- References to existing `loras` table via `loraId` foreign key
- `modelSettings: v.any()` provides flexibility for different model parameters

### 3. Excellent Task Breakdown
The wave-based GitHub issues structure is exemplary:
- **Wave 1 (Backend):** No dependencies, can start immediately
- **Wave 2 (Director UI):** Depends only on Wave 1
- **Wave 3 (User UI):** Parallelizable with Wave 2
- **Wave 4 (Polish):** Final integration
- Dependencies explicitly listed per task
- Estimates are conservative and realistic (total ~19h)

### 4. Aligns With Existing Architecture
The spec builds on existing patterns in the codebase:
- HTTP routes follow the same pattern as `convex/http.ts` (e.g., `/api/loras/*`)
- API endpoint design is RESTful and consistent
- Vanilla JS frontend approach matches existing `app/app.js`
- No framework changes or breaking modifications required

### 5. Model Registry Design
The `models.json` approach is pragmatic:
- Extensible without code changes
- Auto-generates settings forms from schema
- Single source of truth for model capabilities

---

## CONCERNS

### 1. Missing Dynamic Form Schema Definition
Task #7 references `dynamic-form.js` that renders inputs from model schema, but `models.json` structure isn't fully specified. The spec mentions "See implementation_plan.md" but this file isn't in the repo.

**Recommendation:** Add a concrete example of `models.json` schema:
```json
{
  "replicate:flux-dev-lora": {
    "name": "FLUX Dev (LoRA)",
    "supportsLora": true,
    "settings": {
      "num_inference_steps": { "type": "range", "min": 1, "max": 50, "default": 28 },
      "guidance_scale": { "type": "range", "min": 1, "max": 20, "default": 3.5 }
    }
  }
}
```

### 2. Verification Plan Lacks Automated Coverage
The testing plan is mostly manual browser testing. Given that Noisett already has 100 passing tests, the spec should include automated test requirements.

**Recommendation:** Add to Verification Plan:
```
### Automated (pytest)
- [ ] Asset Types CRUD operations via API
- [ ] Generations CRUD with favorite toggle
- [ ] Model registry loader returns valid JSON
- [ ] Combined prompt builder: "{pre} {user} {post}" concatenation
```

### 3. Combined Prompt Edge Cases Not Specified
Section 3.2 shows `[pre-prompt] [editable textarea] [post-prompt]` but doesn't specify:
- What if pre/post are empty?
- Maximum lengths?
- How whitespace/newlines are handled in concatenation?

**Recommendation:** Add a "Combined Prompt Rules" subsection:
- Empty pre/post: omit entirely (no leading/trailing space)
- Concatenation: `"{pre} {user} {post}".strip()`
- Display: Show pre/post as grayed-out labels even when empty

### 4. API Endpoint Design Inconsistency
The spec shows REST-style routes (`GET/POST/PUT/DELETE /api/asset-types/:id`) but existing `convex/http.ts` uses action-style routes (`/api/loras/create`, `/api/loras/list`).

**Recommendation:** Align with existing pattern:
| Spec Route | Aligned Route |
|------------|---------------|
| `GET /api/asset-types` | `GET /api/asset-types/list` |
| `POST /api/asset-types` | `POST /api/asset-types/create` |
| `PUT /api/asset-types/:id` | `POST /api/asset-types/update` |
| `DELETE /api/asset-types/:id` | `DELETE /api/asset-types/delete?id=X` |

### 5. No Error Handling Specification
The spec doesn't define error responses or validation behavior:
- What happens if Asset Type name is empty?
- What if a referenced LoRA is deleted?
- How should the UI handle API failures?

**Recommendation:** Add error handling section or defer to existing API patterns (which return `{ success: false, error: "message" }`).

---

## RECOMMENDATIONS

### High Priority (Block Implementation)

1. **Define `models.json` schema** - Task #2 and #7 depend on this. Add a concrete example to the spec.

2. **Add automated test requirements** - At minimum: API endpoint tests, model registry loader test, prompt concatenation unit test.

### Medium Priority (Address During Implementation)

3. **Align API route naming** with existing `convex/http.ts` patterns for consistency.

4. **Document combined prompt concatenation rules** to prevent inconsistent implementations.

5. **Add error state handling** - Either document expected behavior or explicitly defer to existing patterns.

### Low Priority (Nice to Have)

6. **Consider adding a "Quick Start" section** showing the end-to-end flow: Director creates Asset Type -> User generates with it.

7. **Add a diagram** showing the relationship between Asset Types, Generations, LoRAs, and Models.

---

## TASK BREAKDOWN ASSESSMENT

| Wave | Tasks | Parallelizable? | Risk Level |
|------|-------|-----------------|------------|
| 1 | #1-5 (Backend) | #1, #2 can run in parallel | Low - follows existing patterns |
| 2 | #6-9 (Director UI) | #6 first, then #7-9 in parallel | Medium - new UI code |
| 3 | #10-13 (User UI) | #10 first, then #11-13 | Low - refactoring existing UI |
| 4 | #14-16 (Polish) | Sequential | Low - minor additions |

**Critical Path:** #1 -> #4 -> #6 -> #7 -> #11 -> #12

**Estimated Total:** ~19 hours (conservative)

---

## TESTING PLAN ASSESSMENT

### Current Plan
- Convex schema deployment verification
- API JSON structure validation
- 5 manual browser test scenarios

### Gaps
- No unit tests for prompt concatenation
- No integration tests for Asset Type -> Generation flow
- No edge case testing (empty states, error states)

### Recommended Additions
```
### Unit Tests (pytest)
- test_combined_prompt_builder()
- test_model_registry_loader()
- test_asset_type_validation()

### Integration Tests
- test_director_creates_asset_type_user_generates()
- test_generation_with_deleted_asset_type()

### E2E Tests (manual or Playwright)
- Full Director -> User flow
- History pagination with 50+ items
- Favorite/unfavorite toggle
```

---

## FINAL NOTES

The specification is solid and demonstrates good engineering discipline. The wave-based task breakdown enables parallel work and clear progress tracking. Addressing the high-priority recommendations (models.json schema definition, automated tests) before starting implementation will reduce rework.

**Next Step:** Create GitHub issues from the Task Breakdown table, incorporating the recommendations above.
