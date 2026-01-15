# Director Mode Proposal Review

**Reviewed:** 2026-01-14
**Proposal:** director-mode.proposal.md
**Reviewer:** Claude Code

---

## VERDICT: APPROVED

The proposal is well-structured, addresses a real user need, and aligns with Noisett's AFD architecture. Proceed to specification phase.

---

## STRENGTHS

1. **Clear problem/solution framing** - The two problems (complexity for end users, no brand governance) are concrete and the Director/User mode split directly addresses both.

2. **Good separation of concerns** - Directors handle configuration complexity; users get a simplified interface. This is a sound UX pattern.

3. **Extensibility via JSON config** - The modular model registry approach (`models.json`) is pragmatic. Adding new Replicate models without code changes is a significant maintainability win.

4. **Sensible phasing** - Backend-first (Phase 1) → Director UI (Phase 2) → User UI (Phase 3) → Polish (Phase 4) is the correct order. Each phase delivers value and reduces risk.

5. **Scoped appropriately** - Explicitly marking auth, multi-tenancy, and billing as out of scope keeps the proposal focused.

6. **Open questions resolved** - All three open questions have decisions documented, showing the proposal has matured.

---

## CONCERNS

1. **Asset Type data model is underspecified** - The proposal mentions what an Asset Type bundles (prompts, model, LoRA, quality) but doesn't clarify:
   - Are Asset Types global or per-user/per-team?
   - Can they be soft-deleted or archived?
   - What happens to generations when their Asset Type is deleted?

2. **"isDirector flag" is vague** - The auth placeholder in Phase 4 could become a security risk if not carefully designed. Even a placeholder needs clear semantics (where is it stored? how is it set?).

3. **No migration path mentioned** - If existing users have generations, how do those map to the new schema? Even acknowledging "no migration needed" would be helpful.

4. **Local file references in References section** - The `file:///` URLs are machine-specific and won't work for other contributors.

---

## RECOMMENDATIONS

1. **Clarify Asset Type lifecycle in the spec** - Define ownership, deletion behavior, and whether Asset Types can be duplicated/cloned.

2. **Document the auth placeholder contract** - Even if fake, specify where `isDirector` comes from (localStorage? URL param? hardcoded?) so it can be swapped later.

3. **Add a "Migration/Compatibility" section to the spec** - State explicitly whether existing data needs migration or if this is greenfield.

4. **Replace local file:// references** - Use relative paths or remove if the referenced docs aren't in the repo.

5. **Consider adding a wireframe or mockup reference** - Visual aids would help validate the UX assumptions before implementation.

---

**Next Step:** Proceed to detailed specification (director-mode.spec.md) incorporating the recommendations above.
