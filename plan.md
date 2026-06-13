# Plan: Fix Information Disclosure Vulnerability (Chainlink #17 / GH#96)

## Context

Multiple API endpoints leak internal details through raw exception strings in HTTP responses, filesystem paths in health checks, and LLM configuration in diagnostic endpoints. This is OWASP A05:2021 (Security Misconfiguration). Attackers can use leaked paths, provider names, and DB errors for reconnaissance.

**Design Decisions:**
- **Inline generic strings** for `HTTPException.detail` (matching existing safe pattern in `web/api/entries.py`) — no utility function needed for these
- **One small utility** `sanitize_error_message()` for the DB-stored `error_message` column read in two places
- **Health endpoint stays public** but stripped of internal detail; `/config` and `/metrics` stay admin-gated
- **Sync error_message sanitized on both read AND write** — defense in depth
- **`bulk_update` ValueError block** — replace `str(ve)` with static message; ConnectionError and TimeoutError blocks already safe

---

## Phase 1: Create `web/utils/error_utils.py`

**Why:** The sync `error_message` column is read in two places (`get_sync_status()` and `GET /api/sync/history`). A tiny shared function avoids duplication.

**New file:** `web/utils/error_utils.py`
- `sanitize_error_message(raw: str | None, *, generic: str = "An error occurred") -> str | None`
- Returns `None` when `raw is None`, otherwise returns `generic`

**Test file:** `tests/test_error_utils.py`
- `test_sanitize_none_returns_none`
- `test_sanitize_non_none_returns_generic`
- `test_sanitize_custom_generic`
- `test_sanitize_empty_string_returns_generic`

```text
Write failing tests for a new utility function `sanitize_error_message` in `web/utils/error_utils.py`.

The function signature: `sanitize_error_message(raw: str | None, *, generic: str = "An error occurred") -> str | None`
- Returns None when raw is None
- Returns the generic message for any non-None input (including empty string)
- Accepts a custom generic keyword argument

Create `tests/test_error_utils.py` with four test cases covering: None input, non-None input,
custom generic kwarg, and empty string. Use plain pytest (no async needed).
Run the tests to confirm they fail. Then create `web/utils/error_utils.py` with the ABOUTME header
and the function implementation. Run tests again to confirm they pass.
Update `web/utils/__init__.py` to re-export `sanitize_error_message`.
```

---

## Phase 2: Fix `web/api/health.py` (unauthenticated endpoint info leak)

**Why:** `GET /api/health/` has no auth and exposes `base_path`, `database_path`, `llm_provider`.

**Changes to `web/api/health.py`:**
- Strip `components` dict to status-only for each component:
  - `"database"` → `{"status": db_health["status"]}`
  - `"filesystem"` → `{"status": "healthy" if fs_accessible else "unhealthy"}`
  - `"configuration"` → `{"status": "healthy" if config else "unhealthy"}`
- `/api/health/config` and `/api/health/metrics` — leave as-is (admin-gated)

**Test file:** `tests/test_health_disclosure.py`
- Assert `GET /api/health/` response contains no `base_path`, `database_path`, or `llm_provider` anywhere in JSON
- Assert required fields `["status", "service", "version", "timestamp"]` still present

```text
Write failing tests in `tests/test_health_disclosure.py` for the public health endpoint.

Use the `isolated_app_client` fixture from conftest.py. Write tests that:
1. GET /api/health/ and assert "base_path" does NOT appear anywhere in response JSON (use json.dumps and string search)
2. GET /api/health/ and assert "database_path" does NOT appear anywhere in response JSON
3. GET /api/health/ and assert "llm_provider" does NOT appear anywhere in response JSON
4. GET /api/health/ and assert required fields ["status", "service", "version", "timestamp"] ARE present
5. GET /api/health/ and assert each component in "components" only has a "status" key

Run tests to confirm they fail. Then modify `web/api/health.py` lines 40-57:
- Change "database" component to: {"status": db_health["status"]}
- Change "filesystem" component to: {"status": "healthy" if fs_accessible else "unhealthy"}
- Change "configuration" component to: {"status": "healthy" if config else "unhealthy"}
Run tests to confirm they pass. Run the existing health tests to confirm no regressions.
```

---

## Phase 3: Fix `web/database.py` (health_check and get_database_stats)

**Why:** `health_check()` returns `database_path` and `str(e)`. `get_database_stats()` returns `str(e)`.

**Changes to `web/database.py`:**
- `health_check()` healthy branch (line ~514): remove `"database_path"` key
- `health_check()` unhealthy branch (line ~521): remove `"error"` and `"database_path"` keys
- `get_database_stats()` error fallback (line ~485): remove `"error"` key

**Test file:** `tests/test_database_disclosure.py`
- Async tests on `DatabaseManager` directly with temp DB
- Assert healthy response has no `database_path`
- Assert unhealthy response has no `database_path` or `error`
- Assert `get_database_stats()` error fallback has no `error`

```text
Write failing async tests in `tests/test_database_disclosure.py` for DatabaseManager methods.

Use pytest-asyncio. Create a temporary DatabaseManager with a temp directory DB path.
Initialize it, then test:
1. `health_check()` healthy response does NOT contain "database_path" key
2. `health_check()` healthy response does NOT contain "error" key
3. `health_check()` response DOES contain "status" and "entry_count"
4. `get_database_stats()` returns dict without "error" key (patch engine to raise to trigger error path)

Run tests to confirm they fail. Then modify `web/database.py`:
- health_check() healthy branch: remove "database_path": self.database_path
- health_check() unhealthy branch: return {"status": "unhealthy"} only (remove "error" and "database_path")
- get_database_stats() error fallback: remove "error": str(e) from the return dict
Run tests to confirm they pass.
Check existing tests in test_work_week_database.py and test_step5_sync_implementation.py for
any assertions on "database_path" and update them if needed.
```

---

## Phase 4: Fix `web/api/settings.py` (10+ endpoints with str(e))

**Why:** Every except block interpolates `str(e)` into HTTPException detail.

**Changes to `web/api/settings.py`:**
- All `detail=f"Failed to ...: {str(e)}"` → `detail="Failed to ..."`
- Settings health check unhealthy return: remove `"error": str(e)` key
- `bulk_update` ValueError block line ~427: `'message': str(ve)` → `'message': 'Validation failed'`
- ValueError handlers in `update_setting`, `reset_setting`, `import_settings`, `update_work_week`: `detail=str(e)` → static messages

**Test file:** `tests/test_settings_disclosure.py`

```text
Write failing tests in `tests/test_settings_disclosure.py` for settings API error responses.

Use `isolated_app_client` fixture. Use unittest.mock.patch to make service methods raise
exceptions with a sentinel string "SENTINEL_LEAK_TEST". Then assert the sentinel does NOT
appear in the HTTP response body. Test cases:

1. Patch settings_service.get_all_settings to raise Exception("SENTINEL_LEAK_TEST").
   GET /api/settings/ should return 500 with detail that does NOT contain "SENTINEL_LEAK_TEST".
2. Patch settings_service.get_setting to raise Exception("SENTINEL_LEAK_TEST").
   GET /api/settings/ui.theme should return 500 without the sentinel.
3. Patch settings_service.update_setting to raise ValueError("SENTINEL_LEAK_TEST").
   PUT /api/settings/ui.theme should return 400 without the sentinel.
4. Patch to trigger the settings health check error path — assert no "error" key with raw string.
5. Patch bulk_update_settings to raise ValueError("SENTINEL_LEAK_TEST").
   POST /api/settings/bulk-update should return 400 without the sentinel.

Run tests to confirm they fail. Then modify web/api/settings.py:
- Replace all `detail=f"Failed to ...: {str(e)}"` with `detail="Failed to ..."`
- Settings health unhealthy return: {"status": "unhealthy", "database_connected": False}
- bulk_update ValueError: 'message': 'Validation failed' (not str(ve))
- update_setting ValueError: detail="Invalid setting value"
- reset_setting ValueError: detail="Cannot reset setting"
- import_settings ValueError: detail="Invalid import data"
- update_work_week ValueError: detail="Invalid work week configuration"
Run tests to confirm they pass. Run existing settings tests for regressions.
```

---

## Phase 5: Fix `web/api/sync.py` + `web/services/sync_service.py`

**Why:** All sync endpoints leak `str(e)`. Stored `error_message` creates persistent disclosure.

**Changes to `web/api/sync.py`:**
- All 11 `detail=f"Failed to ...: {str(e)}"` → `detail="Failed to ..."`
- `GET /api/sync/history` line ~359: `"error_message": record.error_message` → `"error_message": sanitize_error_message(record.error_message, generic="Sync failed")`
- Add `IncrementalSyncRequest` Pydantic model for `since_days` validation (ge=1, le=365)

**Changes to `web/services/sync_service.py`:**
- `get_sync_status()` line ~536: `"error_message": sync.error_message` → `"error_message": sanitize_error_message(sync.error_message, generic="Sync failed")`
- Lines 158, 226, 289: `_record_sync_failure(sync_id, str(e))` → `_record_sync_failure(sync_id, "Sync failed")`

**Test file:** `tests/test_sync_disclosure.py`

```text
Write failing tests in `tests/test_sync_disclosure.py` for sync API error responses.

Use `isolated_app_client` fixture. Test cases:

1. Patch sync_service.get_sync_status to raise Exception("SENTINEL_LEAK_TEST").
   GET /api/sync/status should return 500 without the sentinel.
2. GET /api/sync/history — if any records have error_message, it should be "Sync failed" not raw text.
3. POST /api/sync/incremental with {"since_days": -1} should return 422 (validation error).
4. POST /api/sync/incremental with {"since_days": 999} should return 422.
5. POST /api/sync/incremental with {"since_days": 7} should succeed (return 200).

Run tests to confirm they fail. Then:
1. In web/api/sync.py: strip str(e) from all HTTPException details.
2. In web/api/sync.py: import sanitize_error_message and use it on error_message in history endpoint.
3. In web/api/sync.py: add IncrementalSyncRequest model, refactor trigger_incremental_sync to use it.
4. In web/services/sync_service.py: import sanitize_error_message, use in get_sync_status().
5. In web/services/sync_service.py: change _record_sync_failure calls to pass "Sync failed" instead of str(e).
Run tests to confirm they pass. Run existing sync tests for regressions.
```

---

## Phase 6: Final Verification

```text
Run the full test suite to verify no regressions:
  pytest -v

Run a targeted grep to confirm no remaining str(e) in HTTP response details:
  grep -rn 'detail=.*str(e)' web/api/
  grep -rn '"error".*str(e)' web/database.py

Verify the health endpoint manually if possible:
  # Should show only status fields, no paths or provider info
  curl http://localhost:8000/api/health/
```

---

## Files Modified

| File | Change |
|------|--------|
| `web/utils/error_utils.py` | NEW — sanitize_error_message utility |
| `web/utils/__init__.py` | Add re-export |
| `web/api/health.py` | Strip sensitive fields from public endpoint |
| `web/api/settings.py` | Remove str(e) from all HTTPException details |
| `web/api/sync.py` | Remove str(e), add input validation model, sanitize error_message |
| `web/database.py` | Remove database_path and str(e) from health/stats responses |
| `web/services/sync_service.py` | Sanitize error_message on read + write |
| `tests/test_error_utils.py` | NEW |
| `tests/test_health_disclosure.py` | NEW |
| `tests/test_database_disclosure.py` | NEW |
| `tests/test_settings_disclosure.py` | NEW |
| `tests/test_sync_disclosure.py` | NEW |
