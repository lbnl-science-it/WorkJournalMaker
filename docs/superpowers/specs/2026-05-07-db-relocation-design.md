# Design: Move Production Database Out of Source Tree

**Issue:** #114
**Date:** 2026-05-07
**Status:** Draft

## Problem

The production SQLite database (`journal_index.db`) lives inside the source tree at `web/journal_index.db`. A stale duplicate exists at `web/web/journal_index.db` (438KB, untouched since 2026-02-16), created because `runtime_detector.get_app_data_dir()` returns `Path.cwd()` in dev mode — making the DB path CWD-dependent.

This causes: accidental commits, test contamination risk (prior incident: April 2026 worklog corruption), deployment ambiguity, and backup complexity.

## Decisions

1. **OS-standard paths** for the default DB location on all platforms.
2. **Separate dev/prod filenames** (`journal_index_dev.db` vs `journal_index.db`) in the same OS-standard directory. Dev work must not be able to nuke production data.
3. **Aggressive simplification** of the fallback cascade — ~15 methods / ~350 lines replaced by 2 methods.
4. **Migrate** the active DB to the new location on first startup; do not delete the source.
5. **Rename** the stale duplicate; open issue to delete after migration is verified.

## Architecture

### Default DB Paths

| Mode | Platform | Path |
|------|----------|------|
| Desktop (frozen) | macOS | `~/Library/Application Support/WorkJournalMaker/journal_index.db` |
| Desktop (frozen) | Linux | `~/.local/share/WorkJournalMaker/journal_index.db` |
| Desktop (frozen) | Windows | `%LOCALAPPDATA%/WorkJournalMaker/journal_index.db` |
| Development | macOS | `~/Library/Application Support/WorkJournalMaker/journal_index_dev.db` |
| Development | Linux | `~/.local/share/WorkJournalMaker/journal_index_dev.db` |
| Development | Windows | `%LOCALAPPDATA%/WorkJournalMaker/journal_index_dev.db` |

### Path Resolution (DatabaseManager.__init__)

```
if explicit path provided:
    expand tilde, resolve relative paths against executable dir (frozen) or Path(__file__).parent (dev)
    create parent directory
    if directory creation fails → fall back to OS-standard data dir with warning
    return resolved path
else:
    call runtime_detector.get_app_data_dir()
    append "journal_index.db" (frozen) or "journal_index_dev.db" (dev)
    create directory
    return path
```

Two failures = hard error. No emergency temp dirs, no silent `/tmp` stashing.

### runtime_detector.py Changes

`get_app_data_dir()` currently returns `Path.cwd()` in dev mode. Change it to return the OS-standard directory in all modes. Same change for `get_app_config_dir()` and `get_app_log_dir()` for consistency.

This is the root cause fix for the CWD-dependent duplicate DB bug.

### database.py Simplification

**Keep:**
- `DatabaseManager.__init__` (modified)
- `_get_default_database_path` (rewritten — calls runtime_detector, appends filename)
- New `_resolve_explicit_path(path)` — tilde expansion, relative resolution, directory creation, one fallback

**Remove (~15 methods, ~350 lines):**
- `_get_user_data_directory` (duplicates runtime_detector logic)
- `_get_fallback_database_path`
- `_resolve_path_executable_safe`
- `_is_windows_absolute_path`
- `_ensure_directory_exists`
- `_resolve_path_with_fallback`
- `_handle_permission_error`
- `_handle_readonly_filesystem`
- `_create_fallback_directory`
- `_generate_fallback_guidance`
- `_resolve_with_multiple_fallbacks`
- `_get_recovery_guidance`
- `_create_detailed_error`
- `_track_configuration_source`
- `_aggregate_configuration_errors`
- `_validate_database_path`
- `_raise_path_conflict_error`
- `_create_path_error`
- `_validate_path_characters`

### One-Time Migration

On first startup after the change, `DatabaseManager.initialize()` checks:
1. Does the new OS-standard DB path exist? If yes, use it (no migration needed).
2. Does `web/journal_index.db` exist relative to the project? If yes, copy it to the new location and log the migration.
3. Otherwise, create a fresh DB at the new location.

The source file (`web/journal_index.db`) is NOT deleted automatically. The user verifies the migration worked before cleaning up.

### Stale Duplicate Cleanup

- Rename `web/web/journal_index.db` → `web/web/journal_index.db.stale` in this branch.
- Open a GitHub issue to delete it after migration is verified.

### Migration Script Update

`web/migrations/001_add_work_week_settings.py` hardcodes `web/journal_index.db` as a default. Update it to use the same path resolution as `DatabaseManager`.

## Test Impact

- Tests already use explicit temp DB paths via `DatabaseManager(db_path)` — no changes needed for path resolution.
- Tests that mock `runtime_detector` or reference removed fallback methods need updates.
- Tests that reference `_get_user_data_directory` or the removed methods need updates to match the simplified API.

## .gitignore

Already has `*.db` and `web/journal_index.db`. No changes needed.

## Out of Scope

- Database schema changes
- Changing the DB engine (SQLite stays)
- Multi-user / multi-instance support
- Automated cleanup of the old `web/journal_index.db` after migration
