# DB Relocation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the production SQLite database out of the source tree to OS-standard data directories, with separate dev/prod filenames, simplified path resolution, and one-time migration.

**Architecture:** `runtime_detector.get_app_data_dir()` becomes the single source of truth for platform paths (no more CWD in dev mode). `DatabaseManager` path resolution is reduced from ~19 methods to 2. A one-time migration copies the existing DB on first startup.

**Tech Stack:** Python 3.8+, SQLAlchemy async, pathlib, shutil, pytest

---

### Task 1: Update runtime_detector.py — dev mode uses OS-standard dirs

`runtime_detector.get_app_data_dir()` currently returns `Path.cwd()` in dev mode. This is the root cause of the CWD-dependent duplicate DB bug. All three directory functions (`get_app_data_dir`, `get_app_config_dir`, `get_app_log_dir`) need the same fix.

**Files:**
- Modify: `desktop/runtime_detector.py:38-70` (get_app_data_dir), `:73-102` (get_app_config_dir), `:105-133` (get_app_log_dir)
- Test: `tests/test_runtime_detector.py`

- [ ] **Step 1: Write failing tests for new dev-mode behavior**

In `tests/test_runtime_detector.py`, update the existing dev-mode tests to expect OS-standard paths instead of `Path.cwd()`. Add platform-specific dev-mode tests.

```python
# In class TestRuntimeDetector, replace test_get_app_data_dir_development_mode:

def test_get_app_data_dir_development_mode(self):
    """Test app data directory in development mode uses OS-standard path."""
    result = get_app_data_dir()
    # Should NOT be CWD — should be OS-standard
    self.assertNotEqual(result, Path.cwd())
    # On macOS (Darwin), should be ~/Library/Application Support/WorkJournalMaker
    expected = Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
    self.assertEqual(result, expected)

# Also update test_get_runtime_info_development_mode:

def test_get_runtime_info_development_mode(self):
    """Test runtime info in development mode."""
    info = get_runtime_info()
    
    self.assertFalse(info['is_frozen'])
    self.assertEqual(info['mode'], 'development')
    self.assertEqual(info['platform'], 'Darwin')  # On macOS
    self.assertIsNone(info['executable_dir'])
    self.assertIsNone(info['meipass'])
    # Should use OS-standard dir, not CWD
    expected_data_dir = str(Path.home() / "Library" / "Application Support" / "WorkJournalMaker")
    self.assertEqual(info['app_data_dir'], expected_data_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv exec pytest tests/test_runtime_detector.py::TestRuntimeDetector::test_get_app_data_dir_development_mode tests/test_runtime_detector.py::TestRuntimeDetector::test_get_runtime_info_development_mode -v`
Expected: FAIL — currently returns `Path.cwd()`

- [ ] **Step 3: Update runtime_detector.py to use OS-standard dirs in dev mode**

In `desktop/runtime_detector.py`, change all three functions to use OS-standard dirs regardless of frozen state. The `else` branch for each function currently returns CWD-based paths — change them to match the frozen branch.

```python
def get_app_data_dir() -> Path:
    """
    Get platform-specific application data directory.
    
    Returns the same OS-standard location in both desktop and development mode.
    The frozen/dev distinction is handled downstream via filename (e.g. _dev.db suffix).
    
    Returns:
        Path: Application data directory
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "WorkJournalMaker"
        else:
            return Path.home() / "AppData" / "Local" / "WorkJournalMaker"
    else:  # Linux and other Unix-like systems
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / "WorkJournalMaker"
        else:
            return Path.home() / ".local" / "share" / "WorkJournalMaker"


def get_app_config_dir() -> Path:
    """
    Get platform-specific application configuration directory.
    
    Returns:
        Path: Application configuration directory
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Preferences" / "WorkJournalMaker"
    elif system == "Windows":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "WorkJournalMaker"
        else:
            return Path.home() / "AppData" / "Roaming" / "WorkJournalMaker"
    else:  # Linux and other Unix-like systems
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            return Path(xdg_config_home) / "WorkJournalMaker"
        else:
            return Path.home() / ".config" / "WorkJournalMaker"


def get_app_log_dir() -> Path:
    """
    Get platform-specific application log directory.
    
    Returns:
        Path: Application log directory
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Logs" / "WorkJournalMaker"
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "WorkJournalMaker" / "Logs"
        else:
            return Path.home() / "AppData" / "Local" / "WorkJournalMaker" / "Logs"
    else:  # Linux and other Unix-like systems
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            return Path(xdg_data_home) / "WorkJournalMaker" / "logs"
        else:
            return Path.home() / ".local" / "share" / "WorkJournalMaker" / "logs"
```

The `is_frozen_executable()` check is removed from these three functions. It remains available as a standalone function for other uses (e.g., filename selection in database.py).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pyenv exec pytest tests/test_runtime_detector.py -v`
Expected: All tests PASS. The frozen-mode tests should still pass since the platform logic is the same.

- [ ] **Step 5: Commit**

```bash
git add desktop/runtime_detector.py tests/test_runtime_detector.py
git commit -m "fix: runtime_detector uses OS-standard dirs in dev mode (#114)

Root cause fix for CWD-dependent duplicate DB bug. All three
directory functions now return the same OS-standard paths
regardless of frozen/dev mode."
```

---

### Task 2: Rewrite database.py path resolution

Replace the ~19 fallback/error/validation methods with two simple methods: `_get_default_database_path()` and `_resolve_explicit_path()`. The `__init__` method uses these instead of the removed cascade.

**Files:**
- Modify: `web/database.py:107-1226`
- Test: `tests/test_database_manager_paths.py`

- [ ] **Step 1: Write failing tests for new path resolution behavior**

Rewrite `tests/test_database_manager_paths.py` to test the new behavior. The key change: dev mode defaults to `<OS_DATA_DIR>/WorkJournalMaker/journal_index_dev.db`, not `CWD/web/journal_index.db`.

```python
# ABOUTME: Tests for database manager path resolution
# ABOUTME: Validates proper database location based on runtime environment

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import tempfile
import shutil
import platform

from web.database import DatabaseManager


class TestDatabaseManagerPaths(unittest.TestCase):
    """Test database path resolution based on runtime environment."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_development_mode_path(self):
        """Test database path in development mode uses OS-standard dir with _dev suffix."""
        db_manager = DatabaseManager()
        
        # Should use OS-standard dir with _dev suffix, NOT CWD
        actual_path = Path(db_manager.database_path)
        self.assertEqual(actual_path.name, "journal_index_dev.db")
        # Should be in OS-standard data dir
        if platform.system() == "Darwin":
            expected_dir = Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
        else:
            expected_dir = Path.home() / ".local" / "share" / "WorkJournalMaker"
        self.assertEqual(actual_path.parent, expected_dir)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    @patch('desktop.runtime_detector.Path.home')
    def test_desktop_mode_path_macos(self, mock_home, mock_system):
        """Test database path in desktop mode on macOS uses prod filename."""
        mock_home.return_value = self.temp_dir
        
        import sys
        modules_to_clear = [mod for mod in sys.modules.keys() if 'runtime_detector' in mod]
        for mod in modules_to_clear:
            del sys.modules[mod]
        
        db_manager = DatabaseManager()
        
        expected_path = self.temp_dir / "Library" / "Application Support" / "WorkJournalMaker" / "journal_index.db"
        actual_path = Path(db_manager.database_path)
        
        self.assertEqual(actual_path, expected_path)
        self.assertTrue(expected_path.parent.exists())
    
    def test_explicit_path_override(self):
        """Test that explicit path overrides automatic detection."""
        custom_path = str(self.temp_dir / "custom_journal.db")
        
        db_manager = DatabaseManager(database_path=custom_path)
        
        self.assertEqual(db_manager.database_path, custom_path)
    
    def test_explicit_tilde_path_expansion(self):
        """Test that tilde paths are expanded."""
        db_manager = DatabaseManager(database_path="~/test_journal.db")
        
        actual_path = Path(db_manager.database_path)
        self.assertTrue(actual_path.is_absolute())
        self.assertNotIn("~", str(actual_path))
    
    def test_directory_creation(self):
        """Test that database directory is created during initialization."""
        test_db_path = self.temp_dir / "subdir" / "test.db"
        
        self.assertFalse(test_db_path.parent.exists())
        
        db_manager = DatabaseManager(database_path=str(test_db_path))
        
        self.assertTrue(test_db_path.parent.exists())
    
    def test_path_resolution_consistent(self):
        """Test that path resolution is consistent across multiple calls."""
        db_manager1 = DatabaseManager()
        db_manager2 = DatabaseManager()
        
        self.assertEqual(db_manager1.database_path, db_manager2.database_path)
    
    def test_removed_methods_do_not_exist(self):
        """Test that removed fallback methods are no longer on DatabaseManager."""
        db_manager = DatabaseManager(database_path=str(self.temp_dir / "test.db"))
        
        removed_methods = [
            '_get_user_data_directory',
            '_get_fallback_database_path',
            '_resolve_path_executable_safe',
            '_is_windows_absolute_path',
            '_ensure_directory_exists',
            '_resolve_path_with_fallback',
            '_handle_permission_error',
            '_handle_readonly_filesystem',
            '_create_fallback_directory',
            '_generate_fallback_guidance',
            '_resolve_with_multiple_fallbacks',
            '_get_recovery_guidance',
            '_create_detailed_error',
            '_track_configuration_source',
            '_aggregate_configuration_errors',
            '_validate_database_path',
            '_raise_path_conflict_error',
            '_create_path_error',
            '_validate_path_characters',
        ]
        for method_name in removed_methods:
            self.assertFalse(
                hasattr(db_manager, method_name),
                f"Method {method_name} should have been removed"
            )


class TestDatabaseManagerInitialization(unittest.TestCase):
    """Test database manager initialization."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_db_path = self.temp_dir / "test_journal.db"
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_database_manager_initialization(self):
        """Test that DatabaseManager initializes without errors."""
        db_manager = DatabaseManager(database_path=str(self.test_db_path))
        
        self.assertEqual(db_manager.database_path, str(self.test_db_path))
        self.assertIsNone(db_manager.engine)
        self.assertIsNone(db_manager.SessionLocal)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv exec pytest tests/test_database_manager_paths.py -v`
Expected: FAIL — `test_development_mode_path` fails (still returns CWD-based path), `test_removed_methods_do_not_exist` fails (methods still exist)

- [ ] **Step 3: Rewrite DatabaseManager path resolution in database.py**

Replace the `__init__`, `_get_default_database_path`, and all fallback methods (lines 107-1226) with the simplified version. Keep everything above line 107 (models, indexes) and the global `db_manager` at line 1226 unchanged.

```python
class DatabaseManager:
    """Manages database operations and migrations."""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
            self.database_path = self._get_default_database_path()
        else:
            self.database_path = self._resolve_explicit_path(database_path)
        self.engine = None
        self.SessionLocal = None
        
    def _get_default_database_path(self) -> str:
        """
        Get the default database path in the OS-standard data directory.
        
        Uses journal_index.db for frozen (desktop) mode and
        journal_index_dev.db for development mode.
        
        Returns:
            str: Path to the database file
        """
        from desktop.runtime_detector import get_app_data_dir, is_frozen_executable
        
        data_dir = get_app_data_dir()
        filename = "journal_index.db" if is_frozen_executable() else "journal_index_dev.db"
        db_path = data_dir / filename
        
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)
    
    def _resolve_explicit_path(self, path: str) -> str:
        """
        Resolve an explicitly provided database path.
        
        Handles tilde expansion and relative path resolution. Creates
        the parent directory. Falls back to the default path if directory
        creation fails.
        
        Args:
            path: Database path to resolve
            
        Returns:
            str: Resolved absolute path to database file
        """
        path_obj = Path(path)
        
        if path.startswith('~'):
            resolved = path_obj.expanduser()
        elif path_obj.is_absolute():
            resolved = path_obj
        else:
            resolved = (Path(__file__).parent.parent / path_obj).resolve()
        
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            import logging
            logging.getLogger(__name__).warning(
                "Cannot create directory %s, falling back to default path", resolved.parent
            )
            return self._get_default_database_path()
        
        return str(resolved)
```

Remove all methods from line ~154 through line ~1223 (everything between `_resolve_explicit_path` and `initialize`). Keep `initialize`, `_initialize_default_settings`, `_initialize_default_work_week_settings`, `_parse_setting_value`, `get_setting`, `set_setting`, `get_all_settings`, `get_database_stats`, `get_session`, `health_check`, and all `work_week_*` methods and `migrate_week_ending_dates`, `validate_week_ending_dates_integrity`.

The methods to remove are:
- `_get_default_database_path` (old version — replaced above)
- `_resolve_path_executable_safe`
- `_is_windows_absolute_path`
- `_ensure_directory_exists`
- `_get_user_data_directory`
- `_get_fallback_database_path`
- `_validate_database_path`
- `_raise_path_conflict_error`
- `_create_path_error`
- `_validate_path_characters`
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `pyenv exec pytest tests/test_database_manager_paths.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add web/database.py tests/test_database_manager_paths.py
git commit -m "refactor: simplify DatabaseManager path resolution (#114)

Replace ~19 fallback/error methods (~350 lines) with two methods:
_get_default_database_path and _resolve_explicit_path. Dev mode
uses journal_index_dev.db suffix to isolate from production."
```

---

### Task 3: Delete obsolete test files for removed methods

`tests/test_error_handling.py` (20 tests) and `tests/test_path_resolution.py` (29 tests) exclusively test the methods we just removed. These files should be deleted entirely.

Additionally, `tests/test_executable_integration.py` has 2 tests referencing `_get_fallback_database_path` and 2 tests referencing `_is_windows_absolute_path` that need to be removed.

**Files:**
- Delete: `tests/test_error_handling.py`
- Delete: `tests/test_path_resolution.py`
- Modify: `tests/test_executable_integration.py` (remove tests referencing deleted methods)

- [ ] **Step 1: Identify tests to remove in test_executable_integration.py**

Run: `pyenv exec grep -n "_get_fallback_database_path\|_is_windows_absolute_path\|_resolve_path_executable_safe\|_get_user_data_directory" tests/test_executable_integration.py`

Find the test functions containing these references and note their line ranges.

- [ ] **Step 2: Delete the two obsolete test files**

```bash
git rm tests/test_error_handling.py tests/test_path_resolution.py
```

- [ ] **Step 3: Remove individual tests from test_executable_integration.py**

Remove test functions that reference deleted methods:
- Any test calling `_get_fallback_database_path`
- Any test calling `_is_windows_absolute_path`

Keep all other tests in that file intact.

- [ ] **Step 4: Run remaining tests to verify nothing is broken**

Run: `pyenv exec pytest tests/test_executable_integration.py tests/test_database_manager_paths.py tests/test_runtime_detector.py -v`
Expected: All PASS (no references to deleted methods)

- [ ] **Step 5: Commit**

```bash
git add -A tests/test_error_handling.py tests/test_path_resolution.py tests/test_executable_integration.py
git commit -m "test: remove tests for deleted fallback methods (#114)

Delete test_error_handling.py and test_path_resolution.py (49 tests
for 19 removed methods). Remove individual tests from
test_executable_integration.py that reference deleted methods."
```

---

### Task 4: Add one-time migration logic

When `DatabaseManager.initialize()` runs and the target DB doesn't exist, check for the old `web/journal_index.db` and copy it to the new location.

**Files:**
- Modify: `web/database.py` (add migration to `initialize()`)
- Test: `tests/test_database_manager_paths.py` (add migration tests)

- [ ] **Step 1: Write failing tests for migration**

Add to `tests/test_database_manager_paths.py`:

```python
import asyncio
import sqlite3


class TestDatabaseMigration(unittest.TestCase):
    """Test one-time migration from old source-tree DB location."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.target_db = self.temp_dir / "target" / "journal_index_dev.db"
        self.old_db = self.temp_dir / "project" / "web" / "journal_index.db"
    
    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_old_db(self):
        """Create a minimal old-format DB with a marker table."""
        self.old_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.old_db))
        conn.execute("CREATE TABLE migration_marker (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO migration_marker VALUES (42)")
        conn.commit()
        conn.close()
    
    def test_migrate_copies_old_db_to_new_location(self):
        """Test that initialize copies old DB when target doesn't exist."""
        self._create_old_db()
        
        db_manager = DatabaseManager(database_path=str(self.target_db))
        asyncio.run(db_manager.initialize(old_db_path=str(self.old_db)))
        
        # Target should exist and contain the marker
        self.assertTrue(self.target_db.exists())
        conn = sqlite3.connect(str(self.target_db))
        row = conn.execute("SELECT id FROM migration_marker").fetchone()
        conn.close()
        self.assertEqual(row[0], 42)
    
    def test_migrate_does_not_overwrite_existing_target(self):
        """Test that migration is skipped when target already exists."""
        self._create_old_db()
        
        # Create target with different content
        self.target_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.target_db))
        conn.execute("CREATE TABLE existing_marker (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO existing_marker VALUES (99)")
        conn.commit()
        conn.close()
        
        db_manager = DatabaseManager(database_path=str(self.target_db))
        asyncio.run(db_manager.initialize(old_db_path=str(self.old_db)))
        
        # Target should still have existing content, not the old DB's content
        conn = sqlite3.connect(str(self.target_db))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        self.assertIn("existing_marker", tables)
    
    def test_migrate_handles_missing_old_db(self):
        """Test that initialize works when old DB doesn't exist."""
        db_manager = DatabaseManager(database_path=str(self.target_db))
        # Should not raise — just creates fresh DB
        asyncio.run(db_manager.initialize(old_db_path=str(self.old_db)))
        
        self.assertTrue(self.target_db.exists())
    
    def test_old_db_not_deleted_after_migration(self):
        """Test that old DB file is preserved after migration."""
        self._create_old_db()
        
        db_manager = DatabaseManager(database_path=str(self.target_db))
        asyncio.run(db_manager.initialize(old_db_path=str(self.old_db)))
        
        # Old DB should still exist
        self.assertTrue(self.old_db.exists())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv exec pytest tests/test_database_manager_paths.py::TestDatabaseMigration -v`
Expected: FAIL — `initialize()` doesn't accept `old_db_path` yet

- [ ] **Step 3: Add migration logic to DatabaseManager.initialize()**

In `web/database.py`, modify `initialize()`:

```python
async def initialize(self, old_db_path: Optional[str] = None):
    """Initialize database with proper async setup.
    
    Args:
        old_db_path: Path to old source-tree DB for one-time migration.
            If provided and target doesn't exist, copies old DB first.
    """
    db_file = Path(self.database_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # One-time migration from old source-tree location
    if old_db_path and not db_file.exists():
        old_file = Path(old_db_path)
        if old_file.exists():
            import shutil
            import logging
            shutil.copy2(str(old_file), str(db_file))
            logging.getLogger(__name__).info(
                "Migrated database from %s to %s", old_file, db_file
            )
    
    self.engine = create_async_engine(
        f"sqlite+aiosqlite:///{self.database_path}",
        echo=False,
        pool_pre_ping=True
    )
    self.SessionLocal = async_sessionmaker(
        self.engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # Create tables
    async with self.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize default settings
    await self._initialize_default_settings()
    
    # Initialize default work week settings
    await self._initialize_default_work_week_settings()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pyenv exec pytest tests/test_database_manager_paths.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add web/database.py tests/test_database_manager_paths.py
git commit -m "feat: add one-time DB migration from source tree (#114)

DatabaseManager.initialize() accepts old_db_path parameter. If
target doesn't exist but old source-tree DB does, copies it.
Old file is preserved for manual verification."
```

---

### Task 5: Wire migration into app startup

The `web/app.py` startup needs to pass the old DB path so migration happens automatically on first run after the update.

**Files:**
- Modify: `web/app.py:50,71`

- [ ] **Step 1: Update web/app.py startup to pass old_db_path**

In `web/app.py`, modify the `startup()` method to pass the old DB location:

```python
# In WorkJournalWebApp.startup(), change line 71 from:
#     await self.db_manager.initialize()
# to:
            old_db_path = str(Path(__file__).parent / "journal_index.db")
            await self.db_manager.initialize(old_db_path=old_db_path)
```

This resolves `web/journal_index.db` relative to `web/app.py`'s location (which is in `web/`), so it finds the old DB regardless of CWD.

- [ ] **Step 2: Verify the app starts correctly**

Run: `pyenv exec python -c "from web.app import web_app; print('Import OK, db_path:', web_app.db_manager.database_path)"`
Expected: Should print the new OS-standard path with `_dev` suffix.

- [ ] **Step 3: Commit**

```bash
git add web/app.py
git commit -m "feat: wire DB migration into web app startup (#114)

Passes old source-tree DB path to initialize() so migration
happens automatically on first run."
```

---

### Task 6: Update migration script hardcoded path

`web/migrations/001_add_work_week_settings.py` hardcodes `web/journal_index.db` as the default. Update it to use `DatabaseManager`'s path resolution.

**Files:**
- Modify: `web/migrations/001_add_work_week_settings.py:27,178`

- [ ] **Step 1: Update migration script default path**

In `web/migrations/001_add_work_week_settings.py`:

```python
# Line 27 — change the default from hardcoded path to None and resolve via DatabaseManager:
class WorkWeekMigration:
    """Handle work week settings migration."""
    
    def __init__(self, database_path: str = None):
        if database_path is None:
            from web.database import DatabaseManager
            dm = DatabaseManager()
            self.database_path = dm.database_path
        else:
            self.database_path = database_path
        self.engine = None
        self.SessionLocal = None
```

```python
# Line 178 — update the argparse default:
    parser.add_argument("--database", default=None,
                       help="Database file path (defaults to OS-standard location)")
```

- [ ] **Step 2: Verify migration script imports correctly**

Run: `pyenv exec python -c "from web.migrations import __init__; print('OK')" 2>&1 || pyenv exec python -c "from web.migrations.add_work_week_settings_001 import WorkWeekMigration; print('OK')" 2>&1 || echo "Check import path"`

If this doesn't work due to module naming, try:
Run: `pyenv exec python -c "import importlib; mod = importlib.import_module('web.migrations.001_add_work_week_settings'); print('Default path:', mod.WorkWeekMigration().database_path)"`

- [ ] **Step 3: Commit**

```bash
git add web/migrations/001_add_work_week_settings.py
git commit -m "fix: migration script uses DatabaseManager for default path (#114)

Replace hardcoded 'web/journal_index.db' default with
DatabaseManager path resolution."
```

---

### Task 7: Rename stale duplicate and open cleanup issue

Rename the stale duplicate DB and open a GitHub issue to delete it after migration is verified.

**Files:**
- Rename: `web/web/journal_index.db` → `web/web/journal_index.db.stale`

- [ ] **Step 1: Rename the stale duplicate**

```bash
mv web/web/journal_index.db web/web/journal_index.db.stale
```

- [ ] **Step 2: Open GitHub issue for cleanup**

```bash
gh issue create \
  --title "Clean up stale DB files after migration verification" \
  --body "After verifying the DB relocation from #114 works correctly:

1. Delete \`web/web/journal_index.db.stale\` (renamed duplicate, untouched since 2026-02-16)
2. Delete \`web/journal_index.db\` (old source-tree location, preserved for rollback)
3. Consider removing \`web/web/\` directory if empty after cleanup

**Verification checklist:**
- [ ] Web app starts and loads data from new OS-standard location
- [ ] Settings and sync history are preserved
- [ ] Calendar view shows correct entries
- [ ] No \`journal_index.db\` in source tree needed

Ref: #114" \
  --label "cleanup"
```

- [ ] **Step 3: Commit the rename**

```bash
git add -A web/web/
git commit -m "chore: rename stale duplicate DB for cleanup (#114)

web/web/journal_index.db → web/web/journal_index.db.stale
Cleanup tracked in separate issue."
```

---

### Task 8: Full integration test run

Run the complete test suite to verify nothing is broken by the changes.

**Files:**
- None (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `pyenv exec pytest -x -v --timeout=30 2>&1 | tail -30`
Expected: No new failures introduced. The baseline is ~100 failures / 6 errors (pre-existing). We should see fewer failures since we deleted `test_error_handling.py` (20 tests) and `test_path_resolution.py` (29 tests) which were testing removed code.

- [ ] **Step 2: Compare failure count against baseline**

The previous baseline was 140F/18E before the DB-adjacent fix sprint, then 100F/6E after. We removed 49 tests for deleted methods plus a few from `test_executable_integration.py`. The new failure count should be approximately 100F minus any that were in the deleted files, minus any that were previously failing due to the old path resolution.

Run: `pyenv exec pytest --timeout=30 2>&1 | grep -E "passed|failed|error"`

- [ ] **Step 3: Verify the web app starts and serves the dashboard**

Run: `cd /Users/TYFong/code/WorkJournalMaker && pyenv exec python -c "
from web.database import DatabaseManager
dm = DatabaseManager()
print(f'DB path: {dm.database_path}')
from pathlib import Path
print(f'Exists: {Path(dm.database_path).exists()}')
print(f'Parent exists: {Path(dm.database_path).parent.exists()}')
"`

Expected: Path is `~/Library/Application Support/WorkJournalMaker/journal_index_dev.db` and parent directory exists.
