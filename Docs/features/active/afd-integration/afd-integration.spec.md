# AFD Integration for Noisett

> **Status:** ACTIVE  
> **Created:** 2026-01-13  
> **Author:** Agent + Jasfalk  
> **Depends On:** [AFD PyPI Publishing](file:///d:/Github/lushly-dev/AFD/docs/features/proposed/afd-pypi-publishing/afd-pypi-publishing.proposal.md)

---

## Summary

Integrate the **existing AFD Python package** (`AFD/python/`) into Noisett, replacing custom types with official AFD types.

---

## Background

**Good news:** AFD already has a complete Python package at `AFD/python/`:
- `CommandResult`, `CommandError`, `success()`, `error()`, `failure()`
- Full metadata: `Source`, `PlanStep`, `Alternative`, `Warning`
- `HandoffResult` for streaming operations
- Bootstrap tools (`afd-help`, `afd-docs`, `afd-schema`)
- FastMCP transport integration

Noisett's current `src/core/result.py` is a subset of AFD's, so migration is straightforward.

---

## Decision: Use AFD Package ✅

~~Vendor patterns~~ → **Install `afd` package** (pending PyPI publishing)

**Interim approach:** Install from local path until PyPI is ready:
```toml
dependencies = [
    "afd @ file:///d:/Github/lushly-dev/AFD/python",
]
```

---

## Implementation Plan

### Phase 1: Add AFD Dependency ✅
- [x] Add `afd>=0.1.0` to `pyproject.toml`
- [x] Run `pip install -e .` to verify

### Phase 2: Migrate Result Types ✅
- [x] Replace `src/core/result.py` imports with `from afd.core import ...`
- [x] Update all command files to use AFD types
- [x] Contributed `suggestions` field to AFD (v0.1.1)
- [x] 100/100 tests passing

### Phase 3: Add Command Taxonomy Tags ✅
- [x] Add `tags` and `mutation` fields to all command modules
- [x] Add bootstrap tools to MCP server (`noisett_help`, `noisett_docs`, `noisett_schema`)

### Phase 4: Handoff Pattern for Training (Deferred)
- [ ] Use `from afd.core.handoff import HandoffResult`
- [ ] Update `lora.train` to return SSE handoff endpoint
- [ ] Add `/training/{id}/events` SSE endpoint to FastAPI

### Phase 5: JTBD Scenarios (Deferred)
- [ ] Create `scenarios/` directory
- [ ] Add workflow scenarios for LoRA and asset generation

### Phase 6: Verification & Docs ✅
- [x] Run 100 existing tests (no regressions)
- [x] Update CHANGELOG.md

---

## File Changes

| Action | File |
|--------|------|
| MODIFY | `pyproject.toml` — add `afd` dependency |
| DELETE | `src/core/result.py` — use AFD types instead |
| MODIFY | `src/commands/*.py` — update imports |
| MODIFY | `src/server/mcp.py` — add bootstrap tools |
| MODIFY | `src/server/api.py` — add training SSE endpoint |
| NEW | `scenarios/*.scenario.yaml` |
| MODIFY | `AGENTS.md`, `CHANGELOG.md` |

---

## Verification Plan

### Automated
```bash
pytest tests/ -v  # 100 tests, expect all pass
```

### Manual
```bash
# CLI smoke test
noisett asset.generate '{"prompt": "test", "asset_type": "icon"}'

# Training handoff (after SSE endpoint)
curl -N http://localhost:8000/training/test-id/events
```

---

## Future Considerations

### Convex Integration

Once AFD integration is complete, consider migrating to Convex for:
- **LoRA job storage** — Replace in-memory `_loras` dict
- **Training progress** — Convex subscriptions instead of SSE polling
- **History/Favorites** — Replace SQLite with Convex + auth
- **Auth** — Convex Auth for user management

This would align with the Myoso local-first architecture pattern.

---

## Related

- [AFD AGENTS.md](file:///d:/Github/lushly-dev/AFD/AGENTS.md)
- [AFD CHANGELOG.md](file:///d:/Github/lushly-dev/AFD/CHANGELOG.md)
- [Noisett AGENTS.md](file:///d:/Github/lushly-dev/noisett/AGENTS.md)
- [AFD PyPI Publishing Proposal](file:///d:/Github/lushly-dev/AFD/docs/features/proposed/afd-pypi-publishing/afd-pypi-publishing.proposal.md)
