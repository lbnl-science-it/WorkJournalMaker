# Plan: Fix Test Suite Data Corruption of Real Worklog Files

## Context

**Problem**: Five test files use `TestClient(app)` and POST/PUT to `/api/entries/` endpoints, which calls `entry_manager.save_entry_content()` — writing directly to `~/Desktop/worklogs/`. There is no test isolation: no `conftest.py`, no temp directory override, no DI container. This has destroyed 19 of 21 April 2026 worklog files with synthetic test data like `"File system performance test entry N"`.

**Why it's urgent**: Tests run programmatically during agentic development. Any `pytest` invocation that includes these files silently corrupts real journal data.

**Root cause**: `entry_manager.save_entry_content()` resolves `base_path` from config (default `~/Desktop/worklogs/`), and no test fixture overrides this. The write uses `aiofiles.open(path, 'w')` with no backup.

---

## Meta-Plan: 5 Sequential Phases

Each phase will get its own detailed sub-plan at execution time. Phases 1-2 are quick. Phases 3-4 are the core fix. Phase 5 is defense-in-depth.

**Status tracking**: Mark each phase `[x]` when complete.

---

### Phase 1: Immediate Safety — Block Dangerous Tests
- [ ] Complete

**Goal**: Prevent data corruption on the next `pytest` run.

**Approach**: Add a module-level `pytest.skip()` guard to each dangerous file, gated on env var `WJM_TEST_ISOLATION_ENABLED`. Two lines, fully reversible.

**Files to modify** (add guard after docstring, before imports):
1. `tests/test_performance_comprehensive.py`
2. `tests/test_api_endpoints_comprehensive.py`
3. `tests/test_web_integration.py`
4. `tests/test_calendar_interface_step14.py`
5. `tests/test_settings_management.py`

**Verify**: `pytest tests/test_performance_comprehensive.py -v` -> all SKIPPED.

---

### Phase 2: Data Recovery Investigation
- [ ] Complete

**Goal**: Recover corrupted April 2026 files if possible.

**Approach** (manual, read-only):
- Check iCloud Drive sync history (if `~/Desktop` is synced, older file versions may exist)
- Check `~/.Trash/` for worklog files
- Check Time Machine external volumes (`tmutil listbackups`)
- Check `~/Library/Autosave Information/` for cached versions

**Note**: The SQLite database (`journal_index.db`) stores metadata only, not content. The application has backup settings defined in `SettingsService` but the backup feature was **never implemented** -- no `.bak` files exist.

---

### Phase 3: Test Isolation Infrastructure — `conftest.py`
- [ ] Complete

**Goal**: Create a shared fixture that redirects all API writes to `tmp_path`.

**Key architectural insight**: The interception point is `app.state.entry_manager` after `TestClient(app)` triggers the lifespan startup. This is the established pattern -- `test_calendar_api_endpoints.py` already does `patch.object(app.state, 'calendar_service', ...)` safely.

**Create**: `tests/conftest.py` with an `isolated_app_client` fixture that:
1. Creates `TestClient(app)` (triggers startup, populates `app.state`)
2. Replaces `app.state.entry_manager.file_discovery` -> `FileDiscovery(str(tmp_path))`
3. Sets `app.state.entry_manager._current_base_path` -> `str(tmp_path)`
4. Pins `app.state.entry_manager._settings_cache` -> `{'base_path': str(tmp_path), 'output_path': str(tmp_path / 'output')}`
5. Pins `app.state.entry_manager._settings_cache_expiry` -> far future (prevents DB re-query)
6. Yields the client

**Why this works**: `_ensure_file_discovery_initialized()` only re-creates `FileDiscovery` when `_current_base_path != current_settings['base_path']`. By setting both AND pinning the cache, re-initialization never triggers.

**Also create**: `tests/test_isolation_sentinel.py` -- a verification test that POSTs via `isolated_app_client`, then asserts the file landed in `tmp_path` and `~/Desktop/worklogs/` was NOT touched.

**Verify**: Sentinel test passes. No new files in `~/Desktop/worklogs/`.

---

### Phase 4: Fix All 5 Dangerous Test Files
- [ ] Complete

**Goal**: Replace broken fixtures with `isolated_app_client`, remove Phase 1 skip guards, set `WJM_TEST_ISOLATION_ENABLED=1`.

**File-by-file scope**:

| File | Fix |
|---|---|
| `test_performance_comprehensive.py` | Replace `client` fixture -> `isolated_app_client` |
| `test_api_endpoints_comprehensive.py` | Replace `client` fixture -> `isolated_app_client` |
| `test_web_integration.py` | Replace `test_client` -> `isolated_app_client` AND fix `sample_entries` fixture (it constructs its own `FileDiscovery` from real config, bypassing `app.state`) |
| `test_calendar_interface_step14.py` | Fix `TestCalendarIntegration.test_client` -> `isolated_app_client`; fix `TestCalendarInterface.test_client` (its `CONFIG_PATH` env var has no effect) |
| `test_settings_management.py` | Fix `TestSettingsAPI.client` -> `isolated_app_client` (DB mutation isolation) |

**Hardest file**: `test_web_integration.py` -- has TWO independent write paths (API client + `sample_entries` fixture that directly instantiates `FileDiscovery` from `ConfigManager()`). Both must redirect to `tmp_path`.

**Verify**: All 5 files pass with `WJM_TEST_ISOLATION_ENABLED=1`. No new files in `~/Desktop/worklogs/`.

---

### Phase 5: Defense in Depth — Atomic Writes
- [ ] Complete

**Goal**: Even if isolation fails in the future, prevent silent data destruction.

**File to modify**: `web/services/entry_manager.py`, method `save_entry_content()` (line 174)

**Change**: Replace direct `aiofiles.open(path, 'w')` with atomic write-then-rename:
```python
tmp_file = file_path.with_suffix('.tmp')
async with aiofiles.open(tmp_file, 'w') as f:
    await f.write(content)
os.rename(tmp_file, file_path)  # atomic on POSIX same-filesystem
```

**Why atomic write, not .bak**: Atomic write prevents partial-write corruption (crash during write). A `.bak` mechanism is a separate feature (backup system) and per YAGNI should not be conflated with this fix.

**Verify**: TDD -- write test for atomicity first, then implement.

---

## Dangerous Test Files — Full Audit Results

| File | Verdict | Risk |
|---|---|---|
| `test_performance_comprehensive.py` | **DANGEROUS** | 20+ file writes via API |
| `test_api_endpoints_comprehensive.py` | **DANGEROUS** | CRUD writes via API |
| `test_web_integration.py` | **DANGEROUS** | API writes + direct FileDiscovery writes |
| `test_calendar_interface_step14.py` | **DANGEROUS** | API writes (TestCalendarIntegration) |
| `test_settings_management.py` | **DB-CORRUPTING** | Mutates real settings database |
| `test_settings_di.py` | DB-MUTATING | Writes to real settings DB (low risk) |
| `test_settings_persistence.py` | DB-MUTATING | Writes to real settings DB (low risk) |
| `test_summarization_api.py` | SAFE | Uses isolated FastAPI() instance |
| `test_websocket_summarization.py` | SAFE | Uses isolated FastAPI() instance |
| `test_work_week_api.py` | SAFE | Uses temp SQLite DB |
| `test_calendar_api_endpoints.py` | SAFE | Mocked via patch.object |
| `test_calendar_api_performance.py` | SAFE | Mocked via patch.object |
| All others | SAFE | GET-only or no TestClient |

## Key Files for Implementation

- `tests/conftest.py` -- CREATE (core isolation fixture)
- `tests/test_isolation_sentinel.py` -- CREATE (verification)
- `web/services/entry_manager.py:174` -- MODIFY (atomic write)
- `web/services/entry_manager.py:80-106` -- READ-REF (cache interception points)
- `web/app.py` -- READ-REF (app.state assignment)
- 5 dangerous test files -- MODIFY (fix fixtures)

## Dependency Chain for `base_path` (Reference)

```
config.yaml (or WJS_BASE_PATH env var)
  -> ConfigManager._load_config()
    -> AppConfig.processing.base_path  (str, default "~/Desktop/worklogs/")
      -> WorkJournalWebApp.startup()
        -> EntryManager.__init__(config, ...)
          -> self._original_config = config
          -> [lazy] _ensure_file_discovery_initialized()
            -> _get_current_settings()
              -> DB WebSettings['filesystem.base_path']  <-- wins if set
              -> config.processing.base_path             <-- fallback
            -> FileDiscovery(current_base_path)
              -> self.base_path = Path(base_path).expanduser()
                -> _construct_file_path()
                  -> aiofiles.open(path, 'w')  <-- FILE WRITE
```
