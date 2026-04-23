# Design: Replace Save/Swap/Restore Test Isolation with FastAPI Dependency Overrides

**Issue:** #112
**Date:** 2026-04-23
**Status:** Approved

## Problem

The `isolated_app_client` fixture in `tests/conftest.py` isolates tests from production state by saving original `db_manager` references on 6 services, swapping them with a temp DB, then restoring on teardown. This pattern is fragile:

- Every new service must be manually added to the swap list
- The `scheduler` service is already missing from the swap list (isolation gap)
- Mutates module-level singletons, incompatible with `pytest-xdist`
- Restoration depends on fixture teardown ordering

## Approach

Use FastAPI's built-in `dependency_overrides` to replace the database dependency at test time. This is idiomatic FastAPI and provides a single override point.

## Design

### 1. New `get_db_manager` Dependency

**File:** `web/dependencies.py` (new)

A single dependency function that all endpoints use to obtain the database manager:

```python
def get_db_manager(request: Request) -> DatabaseManager:
    return request.app.state.db_manager
```

This mirrors the existing pattern used by `get_entry_manager`, `get_calendar_service`, etc. in the API modules.

### 2. Endpoint Changes

Three endpoints currently access `db_manager` via inline `request.app.state.db_manager` instead of using a dependency. These switch to `Depends(get_db_manager)`:

- `web/api/health.py` — `health_check` (line 28) and `system_metrics` (line 90)
- `web/api/entries.py` — `get_database_stats` (line 281, inline access alongside existing `Depends(get_entry_manager)`)

### 3. Test Fixture Rewrite

The `isolated_app_client` fixture replaces save/swap/restore with:

1. Create a temp `DatabaseManager` pointing at `tmp_path/test_journal_index.db`
2. Set `app.dependency_overrides[get_db_manager] = lambda: temp_db` for endpoint-level DB access
3. Reconstruct all services (including `scheduler`) with the temp DB and assign to `app.state` for service-internal DB access
4. On teardown: clear `app.dependency_overrides`, restore original `app.state` services, dispose temp DB

File discovery isolation (`entry_manager` path/cache swaps) remains unchanged — separate concern.

### 4. Scope Boundaries

**Changed files:**
- `web/dependencies.py` — new file, `get_db_manager` function
- `web/api/health.py` — switch to `Depends(get_db_manager)`
- `web/api/entries.py` — switch to `Depends(get_db_manager)` in `get_database_stats`
- `tests/conftest.py` — rewrite fixture

**Unchanged:**
- `web/app.py` — lifespan, startup, `web_app` singleton
- `web/database.py` — module-level `db_manager` singleton
- `BaseService` — constructor injection pattern
- Existing service dependency functions (`get_entry_manager`, etc.)
- Business logic and test assertions

## Testing Strategy

- All existing tests pass unchanged (fixture yields same `client` interface)
- Add test verifying `dependency_overrides` correctly routes to temp DB
- Verify `scheduler` service is now isolated (previously missed)

## Known Out-of-Scope

The `entry_manager` file discovery isolation (swapping `file_discovery`, `_current_base_path`, `_settings_cache`, `_settings_cache_expiry`) uses the same fragile save/swap/restore pattern. This is a separate concern to be addressed in a follow-up issue.
