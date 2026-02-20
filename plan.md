# Cluster E: Web App Fixes — Implementation Plan

**Source:** `improvements.md` items #14, #17
**Branch:** `improvements/cluster-e-web-app-fixes`

## Analysis

### Item #14: Refactor Settings API Dependency Injection

`web/api/settings.py` is the **only** API module that uses module-level globals
for dependency injection. The other 5 API modules (`calendar.py`, `entries.py`,
`sync.py`, `summarization.py`, `health.py`) already use the correct
`request.app.state` pattern.

The current `settings.py` pattern:
```python
config_manager = None
config = None
logger = None
db_manager = None

async def get_settings_service() -> SettingsService:
    global config_manager, config, logger, db_manager
    if config_manager is None:
        config_manager = ConfigManager()       # Creates DUPLICATE instance
        config = config_manager.get_config()
        logger = JournalSummarizerLogger(...)  # Creates DUPLICATE instance
        db_manager = DatabaseManager()         # Creates DUPLICATE instance
    ...
```

**Problems:**
1. Creates duplicate `ConfigManager`, logger, and `DatabaseManager` — separate
   from the ones already initialized in `app.state` via lifespan
2. Not thread-safe (globals + lazy init)
3. Module-level `logger` variable used directly in endpoint handlers for error
   logging — this logger may differ from `app.state.logger`

**Fix:** Replace `get_settings_service()` with a dependency that reads from
`request.app.state`, matching the pattern used by every other API module.
Remove the 4 module-level globals. Update error logging in endpoint handlers
to use the injected service's logger (via `BaseService.logger`).

### Item #17: Add ABOUTME Comments

27 Python files under `web/` lack the required `ABOUTME` comments. Every other
package in the project has them. This is a mechanical, zero-risk change.

## Steps

### Step 1: Refactor `settings.py` dependency injection

Replace the module-level globals pattern with `request.app.state` access,
matching the established pattern in all other API modules.

**Scope:**
- Add `SettingsService` initialization to `WorkJournalWebApp.startup()` and
  store it on `app.state.settings_service` in the lifespan
- Replace `get_settings_service()` in `settings.py` with a synchronous
  `request.app.state`-based dependency (matching `calendar.py` pattern)
- Remove the 4 module-level globals (`config_manager`, `config`, `logger`,
  `db_manager`)
- Remove the `ConfigManager` and `JournalSummarizerLogger` imports that are
  only needed for the globals pattern
- Replace all `if logger: logger.logger.error(...)` patterns in endpoint
  handlers with `settings_service.logger.logger.error(...)` since the service
  always has a logger via `BaseService`
- Add/update tests to verify the new DI works

**Files:**
- `web/app.py` (modify — add settings_service to startup + lifespan)
- `web/api/settings.py` (modify — replace globals with app.state dependency)
- `tests/test_settings_di.py` (new — test the DI refactor)

```text
Implement Step 1 of the Cluster E plan (Web App Fixes).

Refactor `web/api/settings.py` to use `request.app.state` for dependency
injection instead of module-level globals. This matches the pattern already
used by all other API modules (calendar.py, entries.py, sync.py, etc.).

1. Update `web/app.py`:
   - Import `SettingsService` from `web.services.settings_service`
   - In `WorkJournalWebApp.startup()`, after initializing db_manager, create:
     `self.settings_service = SettingsService(self.config, self.logger, self.db_manager)`
   - In `lifespan()`, add: `app.state.settings_service = web_app.settings_service`

2. Update `web/api/settings.py`:
   - Remove the 4 module-level globals: `config_manager`, `config`, `logger`,
     `db_manager`
   - Remove the `ConfigManager` and `JournalSummarizerLogger` imports (no longer
     needed at module level)
   - Replace `get_settings_service()` with:
     ```python
     def get_settings_service(request: Request) -> SettingsService:
         """Dependency to get SettingsService from app state."""
         return request.app.state.settings_service
     ```
   - For all endpoint handlers that reference the module-level `logger`,
     replace `if logger: logger.logger.error(...)` with
     `settings_service.logger.logger.error(...)` — the settings_service is
     already injected via `Depends(get_settings_service)` and always has a
     logger through BaseService inheritance.
   - Remove the unused `from web.database import DatabaseManager` import

3. Write tests in `tests/test_settings_di.py`:
   - Test that `get_settings_service()` returns the service from `app.state`
   - Test that settings endpoints work with the new DI (using TestClient)
   - Test that no module-level globals remain in settings.py
   - Verify the settings service uses the SAME logger/config/db_manager
     instances as the rest of the app (not duplicates)

TDD: Write failing tests first, then implement the changes, then verify.

Use the pyenv WorkJournal virtual environment for running tests.
```

---

### Step 2: Add ABOUTME comments to all web/ Python files

Add the required 2-line `ABOUTME` header to all 27 Python files under `web/`.

**Scope:**
- Add `# ABOUTME:` comments as the first lines of each file (before the
  existing module docstring)
- Each comment describes the file's purpose concisely

**Files:** All 27 `.py` files under `web/`:
- `web/__init__.py`
- `web/app.py`
- `web/database.py`
- `web/middleware.py`
- `web/api/__init__.py`
- `web/api/calendar.py`
- `web/api/entries.py`
- `web/api/health.py`
- `web/api/settings.py`
- `web/api/summarization.py`
- `web/api/sync.py`
- `web/models/__init__.py`
- `web/models/journal.py`
- `web/models/responses.py`
- `web/models/settings.py`
- `web/services/__init__.py`
- `web/services/base_service.py`
- `web/services/calendar_service.py`
- `web/services/entry_manager.py`
- `web/services/scheduler.py`
- `web/services/settings_service.py`
- `web/services/sync_service.py`
- `web/services/web_summarizer.py`
- `web/services/work_week_service.py`
- `web/utils/__init__.py`
- `web/utils/timezone_utils.py`
- `web/migrations/001_add_work_week_settings.py`

```text
Implement Step 2 of the Cluster E plan.

Add ABOUTME comments to all 27 Python files under `web/`. Per project
standards (CLAUDE.md), all code files must start with a brief 2-line comment
explaining what the file does, with each line starting with "ABOUTME: ".

The ABOUTME lines should be placed as the VERY FIRST lines of the file,
BEFORE any existing module docstring or imports.

For `__init__.py` files that are empty or minimal, a single ABOUTME line
describing the package is sufficient.

After adding all comments, run a verification:
  grep -rL "ABOUTME" web/ --include="*.py"
This should return no results (every .py file has ABOUTME).

Also run the full test suite to confirm nothing is broken by the comment
additions.

Use the pyenv WorkJournal virtual environment for running tests.
```

---

## Dependency Graph

```
Step 1 (Settings DI refactor)
    │
    ▼
Step 2 (ABOUTME comments — includes updating settings.py header)
```

Step 2 depends on Step 1 only to avoid merge conflicts in `settings.py`.
Both steps are low-to-medium risk.
