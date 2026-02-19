# Improvement Metaplan

Overall strategy for working through `improvements.md`. Each cluster is
a cohesive unit of work executed via `/plan-gh` → `/do-gh-issue` → PR.

## Workflow Per Cluster

```
/plan-gh on cluster
  → creates GitHub issues with TDD implementation plans
  → /do-gh-issue to execute each issue
  → commit frequently throughout
  → PR for review
  → merge
  → repeat for next cluster
```

## Cluster Dependency Graph

```
A (quick fixes)          F (CLI cleanup)
  │                        │
  ▼                        ▼
B (import/type cleanup)  (independent, do anytime after A)
  │
  ├──────────┐
  ▼           ▼
D (pkg       C (LLM consolidation)
  structure)   │
  │            │
  ▼            ▼
E (web app   (needs B done first for clean
  fixes)      base class extraction)
```

**Execution order:** A → B → D → C → E → F
(F is independent and can be done anytime after A)

## Clusters

### Cluster A: Quick Fixes — COMPLETE
**Status:** All 5 issues (#41-#45) implemented and closed.
**Items:** #12, #15, #20, #21, #22 from improvements.md
**Scope:** Fix broken logging, hardcoded WebSocket URL, remove tracked
build artifacts, delete empty file, remove debug artifacts.
**Risk:** None. No behavioral changes to production logic.

### Cluster B: Import / Type Cleanup — COMPLETE
**Status:** All 4 issues (#46-#49) implemented.
**Items:** #1, #3, #7, #10 from improvements.md
**Scope:**
- Remove duplicate `AnalysisResult`/`APIStats` from `llm_client.py`
- Fix `summary_generator.py` imports to use `llm_data_structures.py`
- Remove dead `llm_client.py` module (or extract only what's still needed)
- Remove duplicate `rate_limit_delay` config field
**Risk:** Medium. Touches import graph used by CLI pipeline. Existing tests
should catch regressions.
**Design decisions needed:** Protocol/ABC vs duck typing for LLM client interface.

### Cluster C: LLM Client Consolidation — COMPLETE
**Status:** All 4 issues (#56-#59) implemented. PR #61 merged.
**Items:** #2, #6, #8, #9 from improvements.md
**Scope:**
- Extract shared code from 2 LLM clients into `BaseLLMClient`
- Add CBORG as tertiary fallback provider (OpenAI-compatible API)
- Add provider fallback logic to `UnifiedLLMClient` (GCP → AWS → CBORG)
- Add test coverage for `unified_llm_client.py` fallback behavior
- Wire fallback into CLI with user-visible notifications
**Risk:** High. Core API integration layer. TDD is critical.
**Design decisions (resolved):**
- Provider fallback UX: user-visible notification on every transition
- CBORG: tertiary/deep-backup provider (GCP → AWS → CBORG)
- Fallback notification via injectable callback

### Cluster D: Package Structure — COMPLETE
**Status:** All 4 issues (#51-#54) implemented. All sys.path hacks removed.
**Items:** #13, #19 from improvements.md
**Scope:**
- Add `pyproject.toml` (flat layout) to make root importable
- Remove all 84 `sys.path.append`/`sys.path.insert` calls from 83 files
**Risk:** Medium. Affects every import in the project. Must verify all
tests pass after restructuring.
**Design decision:** Flat layout with `pyproject.toml` at root (no file moves).

### Cluster E: Web App Fixes
**Status:** Planned. Issues #62-#63 created. Ready for implementation.
**Items:** #14, #17 from improvements.md
**Scope:**
- Refactor `web/api/settings.py` dependency injection to use `app.state`
  singletons instead of module-level globals (only file with this pattern)
- Add ABOUTME comments to all 27 `web/` Python files
**Risk:** Low-medium. DI change is confined to one API module; all other
modules already use the correct pattern.

### Cluster F: CLI Cleanup
**Status:** Not yet planned. Independent of B-E.
**Items:** #4, #5, #11, #18 from improvements.md
**Scope:**
- Fix provider-specific output in `work_journal_summarizer.py`
- Decompose 400-line `main()` into phase functions
- Remove mock-detection logic from `file_discovery.py`
- Remove migration scaffolding from `file_discovery.py`
**Risk:** Medium. `main()` decomposition is the largest change and needs
careful test coverage to ensure phase ordering is preserved.

## Progress Tracking

| Cluster | Items | Status | Issues | PR |
|---------|-------|--------|--------|----|
| A       | #12,15,20,21,22 | Complete | #41-#45 | — |
| B       | #1,3,7,10 | Complete | #46-#49 | — |
| C       | #2,6,8,9 | Complete | #56-#59 | #61 |
| D       | #13,19 | Complete | #51-#54 | — |
| E       | #14,17 | Planned | #62-#63 | — |
| F       | #4,5,11,18 | Not started | — | — |
