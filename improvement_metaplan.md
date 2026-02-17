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

### Cluster B: Import / Type Cleanup — PLANNED
**Status:** GitHub issues #46-#49 created. `plan.md` and `todo.md` updated.
**Items:** #1, #3, #7, #10 from improvements.md
**Scope:**
- Remove duplicate `AnalysisResult`/`APIStats` from `llm_client.py`
- Fix `summary_generator.py` imports to use `llm_data_structures.py`
- Remove dead `llm_client.py` module (or extract only what's still needed)
- Remove duplicate `rate_limit_delay` config field
**Risk:** Medium. Touches import graph used by CLI pipeline. Existing tests
should catch regressions.
**Design decisions needed:** Protocol/ABC vs duck typing for LLM client interface.

### Cluster C: LLM Client Consolidation
**Status:** Not yet planned. Depends on Cluster B.
**Items:** #2, #6, #8, #9 from improvements.md
**Scope:**
- Extract shared code from 3 LLM clients into `BaseLLMClient`
- Add provider fallback logic to `UnifiedLLMClient`
- Add test coverage for `unified_llm_client.py`
- Decide on CBORG provider (keep/drop from spec)
**Risk:** High. Core API integration layer. TDD is critical.
**Design decisions needed:**
- Provider fallback UX (silent retry vs user-visible?)
- CBORG: still wanted or formally dropped?

### Cluster D: Package Structure
**Status:** Not yet planned. Benefits from Cluster B being done first.
**Items:** #13, #19 from improvements.md
**Scope:**
- Add `pyproject.toml` or equivalent to make root importable
- Remove all 18 `sys.path.append` calls from `web/` modules
**Risk:** Medium. Affects every import in the project. Must verify all
tests pass after restructuring.
**Design decisions needed:** `pyproject.toml` at root vs `src/` layout.

### Cluster E: Web App Fixes
**Status:** Not yet planned. Benefits from Cluster D (clean imports).
**Items:** #14, #17 from improvements.md
**Scope:**
- Refactor FastAPI dependency injection to use `app.state` singletons
  instead of module-level globals
- Add ABOUTME comments to all 27 `web/` Python files
**Risk:** Low-medium. Dependency injection change affects request lifecycle.

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
| B       | #1,3,7,10 | Planned | #46-#49 | — |
| C       | #2,6,8,9 | Not started | — | — |
| D       | #13,19 | Not started | — | — |
| E       | #14,17 | Not started | — | — |
| F       | #4,5,11,18 | Not started | — | — |
