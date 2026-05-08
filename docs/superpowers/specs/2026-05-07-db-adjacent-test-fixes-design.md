# DB-Adjacent Test Fixes Design Spec

**Date:** 2026-05-07
**Goal:** Fix ~52 failing tests + errors in 7 DB-adjacent test files to establish a reliable signal before refactoring `database.py` for issue #114 (move production DB out of source tree).

## Context

The test suite has 140 failures + 18 errors across 29 files. Most are pre-existing stale tests, not regressions. This spec targets only the DB-adjacent subset — tests that exercise `database.py`, `CalendarService`, `WorkWeekService`, settings persistence, and DB sync — because those are the tests that must be green before we can safely refactor the database path resolution.

## Root Causes

### Cluster A: Async Fixture Misuse (~22 tests)
Tests do `service, db_manager = await setup_service` but `setup_service` is a `@pytest_asyncio.fixture` that `yield`s a tuple. The fixture is already resolved by pytest — the `await` is applied to the tuple itself, causing `TypeError: object tuple can't be used in 'await' expression`.

**Fix:** Remove `await` from fixture unpacking lines.

### Cluster C: Mock Target / Validation Drift (~30 tests)
Production code was refactored but test mock paths and assertions weren't updated:
- `web.api.settings.logger` no longer exists at module level
- `WorkWeekConfig.__post_init__` now validates day ranges (1-7), so constructing invalid configs for testing `_perform_comprehensive_validation` crashes before reaching the method under test
- Various `patch()` targets reference moved or renamed attributes

**Fix:** Update mock paths to current production code. For validation tests, either wrap construction in `pytest.raises` or bypass `__post_init__` when testing downstream validation logic.

## Files In Scope

| File | Failures | Errors | Primary Cause |
|------|----------|--------|---------------|
| `test_calendar_service.py` | 12 | 0 | Cluster A (stale `await`) |
| `test_calendar_service_integration.py` | 8 | 3 | Cluster C (mock setup) |
| `test_work_week_service.py` | 11 | 0 | Cluster C (validation drift) |
| `test_work_week_database_sync.py` | 5 | 0 | Cluster C (mock target drift) |
| `test_settings_persistence.py` | 3 | 0 | Cluster A/C mix |
| `test_settings_api_logging.py` | 0 | 9 | Cluster C (missing `logger` attr) |
| `test_db_sync_integration.py` | 1 | 0 | Cluster C (mock target drift) |
| **Total** | **40** | **12** | |

## Files NOT In Scope

- `test_file_discovery.py` — tests removed method `_calculate_week_ending`; not DB-adjacent
- `test_work_week_compatibility.py` — tests wrong `discover_files()` signature; FileDiscovery drift
- `test_local_build.py`, `test_build_config.py` — PyInstaller build system never completed
- `test_ui_functionality.py` — requires Playwright browser
- All other passing or non-DB test files

## Fix Strategy Per File

### 1. test_calendar_service.py
- Remove `await` from all `setup_service` and `real_service` unpacking lines
- Verify tests pass after the mechanical fix

### 2. test_calendar_service_integration.py
- Investigate fixture chain for `TestCalendarServiceEdgeCases` (3 errors)
- Verify mock `get_session` usage matches current `CalendarService` internals
- Fix mock setup to match current DB session pattern

### 3. test_work_week_service.py
- For tests that construct `WorkWeekConfig` with invalid values (start_day=0, etc.): the test intent is to verify `_perform_comprehensive_validation` handles bad input. Since `__post_init__` now rejects these at construction, update tests to expect `ValueError` at construction OR bypass `__post_init__` using `object.__new__()` + manual field assignment where the test specifically targets the validation method.
- Fix mock targets for async methods that were renamed

### 4. test_work_week_database_sync.py
- Read current `entry_manager.py` and `work_week_service.py` to find correct patch paths
- Update `patch()` calls to match current attribute locations

### 5. test_settings_persistence.py
- Replace `DatabaseManager()` no-arg construction with `tmp_path`-based paths
- Fix API error handling test assertions

### 6. test_settings_api_logging.py
- Find where logging now lives in `web/api/settings.py`
- Update fixture `patch_settings_module` to patch the correct logger attribute

### 7. test_db_sync_integration.py
- Identify and fix the single broken mock target

## Success Criteria

- All 7 files pass (0 failures, 0 errors)
- No changes to production code
- Each file committed individually after confirming green

## What This Enables

With these tests green, we have reliable coverage of `database.py`, `CalendarService`, `WorkWeekService`, settings persistence, and DB sync. This gives us a trustworthy regression signal for issue #114 (moving the production DB out of the source tree).
