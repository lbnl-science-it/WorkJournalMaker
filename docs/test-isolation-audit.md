# Test Isolation Audit — Production Data Corruption Risks

**Original audit:** 2026-04-23
**Re-audit:** 2026-05-08
**Scope:** All files in `tests/` directory (106 .py files)
**Context:** Re-audit after DB relocation (PRs #114, #120, #122) moved default
`DatabaseManager()` path from `./web/journal_index.db` to
`~/Library/Application Support/WorkJournalMaker/journal_index_dev.db`

## Executive Summary

The April 23 audit found 18 DANGEROUS and 13 RISKY files. Since then:
- **7 DANGEROUS files deleted** (test_complete_settings_fix, test_work_week_integration,
  test_error_handling, test_timezone_display_fix, test_timezone_fix, test_logger_fix,
  test_settings_debug)
- **2 RISKY files deleted** (test_path_resolution, test_week_ending_fix)
- **5 DANGEROUS files fixed** (test_settings_di, test_settings_management,
  test_calendar_service, test_calendar_service_simple, test_logger)
- **1 DANGEROUS file fixed** (test_settings_persistence — `TestFixtures.client` now
  uses `isolated_app_client`; all subclasses inherit isolation)
- **1 DANGEROUS file deleted** (test_entry_manager, test_prompt_mismatch)

**Current state:** 2 DANGEROUS test files, 7 debug/validate scripts (DANGEROUS),
9 RISKY files remain.

## How Production Data Gets Corrupted (updated)

```
DatabaseManager()          →  ~/Library/Application Support/WorkJournalMaker/journal_index_dev.db
DatabaseManager(temp_path) →  temp_path              (SAFE)
DatabaseManager(":memory:")→  in-memory SQLite        (SAFE)
```

The DB relocation moved the default path out of the repo, eliminating the risk of
committing a corrupted database. However, tests with `DatabaseManager()` no-arg
still write to the user's app data directory — a side effect that should not survive
a test run.

---

## DANGEROUS Files — Write to Production Data or Infrastructure

### Test Files

| File | Status vs April | Issue |
|------|-----------------|-------|
| `test_dashboard_implementation.py` | UNCHANGED | Live HTTP to `localhost:8000` via `requests.post()` — writes real entries. No skip decorator, only function-level guard |
| `test_ui_functionality.py` | NEW FINDING → RISKY | Playwright tests hit `localhost:8000` — requires live server. Double-guarded: `@pytest.mark.skipif` for Playwright + per-test `pytest.skip` on connection failure. Only runs if both Playwright is installed AND server is live |

### Debug/Validate Scripts (pytest-collectable)

All 7 scripts below are collected by pytest (have `test_` functions or `Test` classes)
and use `DatabaseManager()` with no args, writing to the app data directory:

| File | Issue |
|------|-------|
| `debug_date_display_issues.py` | `DatabaseManager()` + `initialize()` on production path |
| `debug_timezone_issue.py` | `DatabaseManager()` + `initialize()` + writes `timezone_test_data.json` |
| `debug_settings_error.py` | Bare `TestClient(app)` — no DB isolation |
| `debug_journal_access.py` | `DatabaseManager()` + `initialize()` |
| `debug_database_sync.py` | `DatabaseManager()` + `initialize()` (two instances) |
| `debug_date_mapping.py` | `DatabaseManager()` + `initialize()` + reads real worklogs |
| `validate_rollback.py` | Spawns real subprocesses |

---

## RISKY Files — Read Production Data or Fragile Isolation

| File | Status vs April | Issue |
|------|-----------------|-------|
| `test_database_manager_paths.py` | ACCEPTABLE | `DatabaseManager()` no-arg (lines 27, 47, 75-76) — intentionally tests default path resolution. Side effect is `mkdir` on XDG app data dir only (idempotent, no DB file created) |
| `test_executable_integration.py` | UNCHANGED | `DatabaseManager()` no-arg at lines 369, 374, 513, 543 |
| `test_calendar_comprehensive.py` | FIXED | Inline `TestClient(app)` replaced with `isolated_app_client` |
| `test_calendar_api_endpoints.py` | FIXED | `client` fixtures now delegate to `isolated_app_client` |
| `test_calendar_api_performance.py` | FIXED | All 3 `client` fixtures now delegate to `isolated_app_client` |
| `test_summarization_interface_step16.py` | FIXED | `client` fixture now delegates to `isolated_app_client` |
| `test_file_discovery_v2_foundation.py` | UNCHANGED | Reads real `~/Desktop/worklogs/worklogs_2024` |
| `test_file_discovery_v2_integration.py` | UNCHANGED | Reads real `~/Desktop/worklogs/` via live `discover_files()` |
| `test_integration_logging.py` | UNCHANGED | May probe for real AWS credentials |

---

## Files Fixed Since April Audit

The following files were DANGEROUS in April and are now SAFE:

| File | How Fixed |
|------|-----------|
| `test_settings_di.py` | Now uses `isolated_app_client` fixture |
| `test_settings_management.py` | `TestSettingsApi` and `TestEndToEndTests` now use `isolated_app_client`; unit tests use `tempfile.mkdtemp` |
| `test_calendar_service.py` | Now uses `tmp_path` for all DB paths |
| `test_calendar_service_simple.py` | Now uses `tmp_path` for all DB paths |
| `test_logger.py` | Now uses `temp_log_dir` / `tmp_path` for log output |
| `test_work_week_api.py` | Uses `tempfile` + `dependency_overrides` for isolation |
| `test_settings_persistence.py` | `TestFixtures.client` now uses `isolated_app_client`; all subclasses inherit isolation |

---

## Files Deleted Since April Audit

| File | Was |
|------|-----|
| `test_complete_settings_fix.py` | DANGEROUS — `DatabaseManager()` + filesystem writes |
| `test_work_week_integration.py` | DANGEROUS — `DatabaseManager()` + filesystem writes |
| `test_error_handling.py` | DANGEROUS — `DatabaseManager()` in every test class |
| `test_timezone_display_fix.py` | DANGEROUS — `DatabaseManager()` + `initialize()` |
| `test_timezone_fix.py` | DANGEROUS — `DatabaseManager()` + writes artifacts |
| `test_logger_fix.py` | DANGEROUS — `DatabaseManager()` + `initialize()` |
| `test_settings_debug.py` | DANGEROUS — bare `TestClient(app)` |
| `test_entry_manager.py` | DANGEROUS — `save_entry_content()` to real filesystem |
| `test_prompt_mismatch.py` | DANGEROUS — live paid API calls |
| `test_path_resolution.py` | RISKY — `DatabaseManager()` no-arg |
| `test_week_ending_fix.py` | RISKY — reads production worklog files |

---

## Root Causes (updated)

1. **`DatabaseManager()` with no arguments** — Now writes to XDG app data dir instead of
   in-repo file. Lower severity (no commit risk) but still a side effect. Affects 3 test
   files + 5 debug scripts.

2. **`TestClient(app)` without `dependency_overrides`** — Historically 5 files created
   a test client routing through the real app. Most are now fixed via `isolated_app_client`.
   1 debug script (`debug_settings_error.py`) still uses bare `TestClient(app)`.

3. **Live server dependencies** — 2 files (`test_dashboard_implementation.py`,
   `test_ui_functionality.py`) require a running server and hit it with real requests.

4. **Debug scripts in tests/ directory** — 7 scripts with pytest-collectable names are
   not tests but diagnostic tools. They should be excluded from pytest collection or
   moved out of `tests/`.

---

## Recommended Fix Priority

### Immediate (blocks other T1 work)
1. **Exclude debug scripts from pytest collection** — Add `__test__ = False` or move to
   `scripts/` directory. These 7 files are the largest source of side effects.
2. **Fix test_dashboard_implementation.py** — Convert to `TestClient(app)` with isolation,
   or add proper `@pytest.mark.skip`/marker.

### Next (complete T1 gate)
3. **Fix test_database_manager_paths.py** — Provide explicit temp paths instead of no-arg.

### Low priority (read-only, acceptable risk)
6. **test_file_discovery_v2_foundation.py** and **test_file_discovery_v2_integration.py** —
   Read-only access to real worklogs. Risk: test failure if files don't exist, not corruption.
7. **test_integration_logging.py** — AWS credential probing, no writes.
