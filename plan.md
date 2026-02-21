# Fix Pre-existing Test Failures — Issue #60 Plan

**Issue:** [#60](https://github.com/lbnl-science-it/WorkJournalMaker/issues/60)
**Branch:** `fix/issue-60-test-failures`
**Baseline:** 54 failed + 18 errors = 72 broken tests across 11 files (in scope)
**Full suite baseline:** 169 failed, 1349 passed, 27 errors

---

## Phase 1: Async Fixture Decorator Fixes

**Goal:** Fix the 37 failures + 18 errors caused by `@pytest.fixture` on `async def` functions.
**Risk:** Low — mechanical decorator swaps.
**Scope:** 7 test files, ~26 async fixtures to swap.

### Step 1.1: Fix work_week async test fixtures — [#73](https://github.com/lbnl-science-it/WorkJournalMaker/issues/73)

**Files:** `tests/test_work_week_compatibility.py`, `tests/test_work_week_database_sync.py`, `tests/test_work_week_integration.py`, `tests/test_work_week_performance.py`
**What:** Replace `@pytest.fixture` with `@pytest_asyncio.fixture` on all async fixtures. Add `import pytest_asyncio` where missing.
**Verification:** Run these 4 files — failures should drop significantly.

```text
Fix async fixture decorators in the work week test files for issue #60.

In pytest-asyncio strict mode, async fixtures must use @pytest_asyncio.fixture
instead of @pytest.fixture, otherwise sync test functions receive coroutine
objects instead of resolved values.

Files to fix:
1. tests/test_work_week_compatibility.py — 2 async fixtures need decorator swap, add import pytest_asyncio
2. tests/test_work_week_database_sync.py — 5 async fixtures need decorator swap, add import pytest_asyncio
3. tests/test_work_week_integration.py — check for async fixtures, add import pytest_asyncio if needed
4. tests/test_work_week_performance.py — 2 async fixtures need decorator swap (pytest_asyncio already imported)

For each file:
1. Find all fixtures defined with `@pytest.fixture` and `async def`
2. Replace `@pytest.fixture` with `@pytest_asyncio.fixture` on those fixtures
3. Add `import pytest_asyncio` at the top if not already present
4. Do NOT change any test logic, assertions, or non-fixture code

After fixes, run:
  pytest tests/test_work_week_compatibility.py tests/test_work_week_database_sync.py \
    tests/test_work_week_integration.py tests/test_work_week_performance.py --tb=short -q

Commit: "Fix async fixture decorators in work week tests (#60, step 1.1)"
```

### Step 1.2: Fix calendar async test fixtures — [#74](https://github.com/lbnl-science-it/WorkJournalMaker/issues/74)

**Files:** `tests/test_calendar_interface_step14.py`, `tests/test_calendar_service_integration.py`
**What:** Same decorator swap pattern. These files also have setup/teardown errors (Category 3) that should resolve.
**Verification:** Run these 2 files — expect errors to resolve.

```text
Fix async fixture decorators in the calendar test files for issue #60.

Same root cause as step 1.1: async fixtures using @pytest.fixture instead of
@pytest_asyncio.fixture in strict mode.

Files to fix:
1. tests/test_calendar_interface_step14.py — 5 async fixtures need decorator swap, add import pytest_asyncio
2. tests/test_calendar_service_integration.py — 7 async fixtures need decorator swap, add import pytest_asyncio

For each file:
1. Find all fixtures defined with `@pytest.fixture` and `async def`
2. Replace `@pytest.fixture` with `@pytest_asyncio.fixture` on those fixtures
3. Add `import pytest_asyncio` at the top if not already present
4. Do NOT change any test logic, assertions, or non-fixture code

After fixes, run:
  pytest tests/test_calendar_interface_step14.py tests/test_calendar_service_integration.py --tb=short -q

Commit: "Fix async fixture decorators in calendar tests (#60, step 1.2)"
```

### Step 1.3: Fix web integration async test fixtures — [#75](https://github.com/lbnl-science-it/WorkJournalMaker/issues/75)

**Files:** `tests/test_web_integration.py`
**What:** Same decorator swap pattern. 5 async fixtures + setup/teardown errors.
**Verification:** Run this file — expect errors to resolve.

```text
Fix async fixture decorators in the web integration test file for issue #60.

Same root cause as steps 1.1 and 1.2.

File to fix:
1. tests/test_web_integration.py — 5 async fixtures need decorator swap, add import pytest_asyncio

Steps:
1. Find all fixtures defined with `@pytest.fixture` and `async def`
2. Replace `@pytest.fixture` with `@pytest_asyncio.fixture` on those fixtures
3. Add `import pytest_asyncio` at the top if not already present
4. Do NOT change any test logic, assertions, or non-fixture code

After fixes, run:
  pytest tests/test_web_integration.py --tb=short -q

Commit: "Fix async fixture decorators in web integration tests (#60, step 1.3)"
```

### Step 1.4: Phase 1 verification and decision gate

**What:** Run all 7 files together. Record results. Decide whether Phase 2 is worth pursuing.

```text
Run the full Phase 1 verification for issue #60.

Run all 7 async-fixture-affected files together:
  pytest tests/test_work_week_compatibility.py tests/test_work_week_database_sync.py \
    tests/test_work_week_integration.py tests/test_work_week_performance.py \
    tests/test_calendar_interface_step14.py tests/test_calendar_service_integration.py \
    tests/test_web_integration.py --tb=short -q

Baseline was: 37 failed + 18 errors = 55 broken tests.
Expected: Most or all should now pass.

Record the results. This is a DECISION GATE:
- If most tests pass: the test authors got the logic right, just the decorators
  wrong. Phase 2 contract fixes are likely worth doing.
- If most tests STILL FAIL with new errors: the tests were poorly written
  end-to-end. Phase 2 should be reconsidered — deleting and rewriting may be
  more appropriate than patching.

Do NOT change production code. Only fix test wiring issues.

Commit: "Verify Phase 1 async fixture fixes (#60, step 1.4)" (if any additional fixes needed)
```

---

## Decision Gate: Evaluate Phase 2

**After Phase 1 completes, answer these questions:**

1. How many of the 55 broken tests now pass?
2. Of those that still fail, are the failures shallow (assertion tweaks) or deep (fundamentally wrong test design)?
3. Is the signal-to-noise improvement from Phase 1 alone sufficient?

**If >80% pass:** Proceed with Phase 2 — the tests have value, just wiring issues.
**If 50-80% pass:** Selectively fix the passing-adjacent tests, delete the rest.
**If <50% pass:** Close the Phase 2 issues. The tests need rewriting, not patching. File a separate issue for writing proper tests from scratch.

---

## Phase 2: Test-Code Contract Mismatch Fixes (GATED — pending Phase 1 results)

Issues created but not yet approved for implementation:
- [#76](https://github.com/lbnl-science-it/WorkJournalMaker/issues/76) — WorkWeekConfig validation test contracts (11 failures)
- [#77](https://github.com/lbnl-science-it/WorkJournalMaker/issues/77) — Work week settings service test contract (1 failure)
- [#78](https://github.com/lbnl-science-it/WorkJournalMaker/issues/78) — Build config test contracts (2 failures)
- [#79](https://github.com/lbnl-science-it/WorkJournalMaker/issues/79) — Settings persistence test setup (6 failures)
- [#80](https://github.com/lbnl-science-it/WorkJournalMaker/issues/80) — Full scope verification

See full prompts and details for these steps in the
[spec](implementation_plans/fix_issue_60_spec.md) and the GitHub issues above.
These will be revisited after the decision gate.
