# Fix Pre-existing Test Failures — Issue #60 Specification

**Issue:** [#60](https://github.com/lbnl-science-it/WorkJournalMaker/issues/60)
**Scope:** 11 test files, ~130 failures + ~18 errors on `main`
**Out of scope:** `test_local_build.py` (39 failures) — separate issue

## Problem Statement

157 test failures and 18 errors exist on `main` across 11 test files. These failures pre-date the Cluster A-F metaplan work and are unrelated to recent feature development. The tested code (WorkWeekService, CalendarService, EntryManager, etc.) is real and actively used — the tests themselves have wiring issues.

## Root Cause Categories

### Category 1: Async Fixture Decorator Misuse (~100+ failures)

**Files affected:**
- `tests/test_work_week_compatibility.py` (~20 failures)
- `tests/test_work_week_database_sync.py` (~12 failures)
- `tests/test_work_week_integration.py` (1 failure)
- `tests/test_work_week_performance.py` (~5 failures + 4 errors)
- `tests/test_calendar_interface_step14.py` (1 failure + 6 errors)
- `tests/test_calendar_service_integration.py` (~3 errors)
- `tests/test_web_integration.py` (1 failure + 5 errors)

**Root cause:** Tests use `@pytest.fixture` with `async def`, but `pytest-asyncio` in strict mode requires `@pytest_asyncio.fixture`. Sync test functions receive coroutine objects instead of resolved values, causing `TypeError: 'async_generator' object is not subscriptable`.

**Fix:** Replace `@pytest.fixture` with `@pytest_asyncio.fixture` on all async fixture functions in affected files. Add `import pytest_asyncio` where missing.

### Category 2: Test-Code Contract Mismatches (~15 failures)

**Files affected:**
- `tests/test_work_week_service.py` (~10 failures)
- `tests/test_work_week_settings_service.py` (1 failure)
- `tests/test_build_config.py` (2 failures)
- `tests/test_settings_persistence.py` (3 failures)

**Root cause:** Tests construct invalid `WorkWeekConfig` objects expecting to test validation logic, but `__post_init__` raises `ValueError` before the validation method under test is reached. Similarly, `validate_config()` raises `BuildConfigError` instead of returning `False` as tests expect.

**Fix approach — evaluate both sides:**
1. Examine whether `__post_init__` validation is architecturally appropriate or if validation should live in a separate method that tests can call independently.
2. If `__post_init__` validation is correct: restructure tests to use `pytest.raises` for constructor validation, testing at the right layer.
3. If validation should be separated: refactor the production code and update tests accordingly.
4. For `validate_config()`: determine if raising vs returning `False` is the correct behavior, then align tests.

### Category 3: Async Test Runner Setup/Teardown Errors (~18 errors)

**Files affected:** Same as Category 1 (calendar, web integration tests).

**Root cause:** Database setup fixtures fail during async collection, preventing test execution.

**Fix:** Expected to resolve automatically once Category 1 fixtures are corrected.

## Implementation Plan

### Phase 1: Async Fixture Fixes (Category 1 + Category 3)

1. Identify all async fixtures using `@pytest.fixture` in the 7 affected files
2. Replace with `@pytest_asyncio.fixture`
3. Add `import pytest_asyncio` where missing
4. Run full test suite — verify Category 1 and Category 3 failures resolve
5. **Commit:** "Fix async fixture decorators in work week, calendar, and web tests (#60)"

### Phase 2: Contract Mismatch Fixes (Category 2)

1. Read `WorkWeekConfig.__post_init__` and the failing tests to understand the contract gap
2. Evaluate whether `__post_init__` validation is the right design:
   - If yes: update tests to use `pytest.raises` at constructor level
   - If no: refactor validation into a separate callable method
3. Fix `validate_config()` / `BuildConfigError` test expectations
4. Fix `test_settings_persistence.py` database setup issues
5. Run full test suite — verify Category 2 failures resolve
6. **Commit:** "Fix test-code contract mismatches in validation tests (#60)"

### Phase 3: Verification and Cleanup

1. Run full test suite — confirm all #60 scope tests pass or are justified `xfail`
2. If any tests cover genuinely unimplemented functionality, mark `@pytest.mark.xfail(reason="...")` with a clear reason
3. **Commit:** "Mark unimplemented feature tests as xfail (#60)" (if applicable)
4. Update issue #60 with results

## Success Criteria

- All tests in the 11 files listed in #60 either **pass** or are marked `xfail` with justification
- No test deletions without explicit approval
- No production code changes unless the Category 2 evaluation determines `__post_init__` validation should be restructured
- Full test suite run shows improvement from current baseline (169 failed → target: <40 remaining from out-of-scope `test_local_build.py`)

## Verification Commands

```bash
# Run just the #60 scope
pytest tests/test_work_week_service.py tests/test_work_week_compatibility.py \
  tests/test_work_week_database_sync.py tests/test_work_week_integration.py \
  tests/test_work_week_performance.py tests/test_work_week_settings_service.py \
  tests/test_calendar_interface_step14.py tests/test_calendar_service_integration.py \
  tests/test_web_integration.py tests/test_build_config.py \
  tests/test_settings_persistence.py --tb=short -q

# Full suite baseline comparison
pytest -v --tb=line 2>&1 | tail -5
```
