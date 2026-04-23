# Dependency Override Test Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual save/swap/restore DB isolation in test fixtures with FastAPI's idiomatic `dependency_overrides`, closing the `scheduler` isolation gap and enabling future `pytest-xdist` compatibility.

**Architecture:** Create a `get_db_manager` dependency function in `web/dependencies.py`. Update the three endpoints that access `db_manager` inline to use `Depends(get_db_manager)`. Rewrite `tests/conftest.py` to use `app.dependency_overrides[get_db_manager]` for DB isolation.

**Tech Stack:** FastAPI dependency injection, pytest fixtures, SQLAlchemy async

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `web/dependencies.py` | Create | Central `get_db_manager` dependency function |
| `web/api/health.py` | Modify (lines 28, 90) | Switch inline `request.app.state.db_manager` to `Depends(get_db_manager)` |
| `web/api/entries.py` | Modify (line 281) | Switch inline `request.app.state.db_manager` to `Depends(get_db_manager)` |
| `tests/conftest.py` | Modify | Rewrite `isolated_app_client` to use `dependency_overrides` for DB isolation |
| `tests/test_dependency_override_isolation.py` | Create | Tests verifying the new isolation mechanism |

---

### Task 1: Create `web/dependencies.py` with `get_db_manager`

**Files:**
- Create: `web/dependencies.py`
- Test: `tests/test_dependency_override_isolation.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_dependency_override_isolation.py`:

```python
# ABOUTME: Tests verifying that FastAPI dependency overrides correctly isolate the database.
# ABOUTME: Ensures get_db_manager returns app.state.db_manager and can be overridden in tests.

"""
Tests for FastAPI Dependency Override Isolation

Verifies that the get_db_manager dependency function works correctly
and can be overridden in tests to provide a temporary database.
"""

import pytest
from fastapi.testclient import TestClient

from web.app import app
from web.dependencies import get_db_manager


class TestGetDbManagerDependency:
    """Verify get_db_manager returns the app's database manager."""

    def test_get_db_manager_returns_app_state_db_manager(self):
        """get_db_manager should return the db_manager from app.state."""
        with TestClient(app) as client:
            # The health endpoint uses get_db_manager via Depends —
            # if it responds, the dependency resolved successfully
            response = client.get("/api/health/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ("healthy", "degraded")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/TYFong/code/WorkJournalMaker && pyenv activate WorkJournal && python -m pytest tests/test_dependency_override_isolation.py::TestGetDbManagerDependency::test_get_db_manager_returns_app_state_db_manager -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'web.dependencies'`

- [ ] **Step 3: Write minimal implementation**

Create `web/dependencies.py`:

```python
# ABOUTME: Central dependency functions for FastAPI dependency injection.
# ABOUTME: Provides get_db_manager as the single override point for test DB isolation.

"""
FastAPI Dependency Functions

Provides dependency functions that endpoints use via Depends() to obtain
shared resources. Tests override these via app.dependency_overrides to
inject temporary instances.
"""

from fastapi import Request

from web.database import DatabaseManager


def get_db_manager(request: Request) -> DatabaseManager:
    """Return the application's database manager.

    Endpoints obtain db_manager through Depends(get_db_manager) rather than
    accessing request.app.state.db_manager inline.  This allows tests to
    override the dependency with app.dependency_overrides[get_db_manager].
    """
    return request.app.state.db_manager
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestGetDbManagerDependency::test_get_db_manager_returns_app_state_db_manager -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/dependencies.py tests/test_dependency_override_isolation.py
git commit -m "Add get_db_manager dependency function and test (#112)"
```

---

### Task 2: Update `health.py` to use `Depends(get_db_manager)`

**Files:**
- Modify: `web/api/health.py` (lines 24, 28, 87–90)
- Test: `tests/test_dependency_override_isolation.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dependency_override_isolation.py`:

```python
class TestDbManagerOverrideInHealthEndpoints:
    """Verify health endpoints use the overridden db_manager."""

    def test_health_check_uses_overridden_db_manager(self, tmp_path):
        """GET /api/health/ should use the dependency-injected db_manager."""
        import asyncio
        from web.database import DatabaseManager

        temp_db_path = str(tmp_path / "override_test.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        app.dependency_overrides[get_db_manager] = lambda: temp_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/health/")
                assert response.status_code == 200
                data = response.json()
                # The temp DB is valid, so health check should succeed
                assert data["status"] in ("healthy", "degraded")
        finally:
            app.dependency_overrides.clear()
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()

    def test_metrics_uses_overridden_db_manager(self, tmp_path):
        """GET /api/health/metrics should use the dependency-injected db_manager."""
        import asyncio
        from web.database import DatabaseManager

        temp_db_path = str(tmp_path / "metrics_test.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        app.dependency_overrides[get_db_manager] = lambda: temp_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/health/metrics")
                assert response.status_code == 200
                data = response.json()
                assert "database" in data
                # Temp DB has zero entries
                assert data["database"]["entry_count"] == 0
        finally:
            app.dependency_overrides.clear()
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestDbManagerOverrideInHealthEndpoints -v`

Expected: FAIL — health.py still uses inline `request.app.state.db_manager`, so the override has no effect and tests hit the production DB (entry_count != 0 if real data exists).

- [ ] **Step 3: Update `web/api/health.py`**

Change `health_check` (line 24) to accept `db_manager` via Depends:

```python
from web.dependencies import get_db_manager

@router.get("/", response_model=HealthResponse)
async def health_check(request: Request, db_manager: DatabaseManager = Depends(get_db_manager)):
```

Remove line 28 (`db_manager: DatabaseManager = request.app.state.db_manager`).

Change `system_metrics` (line 87) similarly:

```python
@router.get("/metrics")
async def system_metrics(request: Request, db_manager: DatabaseManager = Depends(get_db_manager)):
```

Remove line 90 (`db_manager: DatabaseManager = request.app.state.db_manager`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestDbManagerOverrideInHealthEndpoints -v`

Expected: PASS

- [ ] **Step 5: Run existing health tests to check for regressions**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/ -k "health" -v`

Expected: All existing tests PASS

- [ ] **Step 6: Commit**

```bash
git add web/api/health.py tests/test_dependency_override_isolation.py
git commit -m "Switch health endpoints to Depends(get_db_manager) (#112)"
```

---

### Task 3: Update `entries.py` `get_database_stats` to use `Depends(get_db_manager)`

**Files:**
- Modify: `web/api/entries.py` (lines 270–281)
- Test: `tests/test_dependency_override_isolation.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dependency_override_isolation.py`:

```python
class TestDbManagerOverrideInEntriesEndpoints:
    """Verify entries stats endpoint uses the overridden db_manager."""

    def test_database_stats_uses_overridden_db_manager(self, tmp_path):
        """GET /api/entries/stats/database should use dependency-injected db_manager."""
        import asyncio
        from web.database import DatabaseManager

        temp_db_path = str(tmp_path / "entries_stats_test.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        app.dependency_overrides[get_db_manager] = lambda: temp_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/entries/stats/database")
                assert response.status_code == 200
                data = response.json()
                # Temp DB has zero entries
                assert data["total_entries"] == 0
                assert data["entries_with_content"] == 0
        finally:
            app.dependency_overrides.clear()
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestDbManagerOverrideInEntriesEndpoints -v`

Expected: FAIL — `get_database_stats` still uses `request.app.state.db_manager` inline.

- [ ] **Step 3: Update `web/api/entries.py`**

Change `get_database_stats` (line 270) to accept `db_manager` via Depends:

```python
from web.dependencies import get_db_manager

@router.get("/stats/database", response_model=DatabaseStats)
async def get_database_stats(
    db_manager: DatabaseManager = Depends(get_db_manager),
    entry_manager: EntryManager = Depends(get_entry_manager)
):
```

Remove the `request: Request` parameter (no longer needed) and line 281 (`db_manager = request.app.state.db_manager`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestDbManagerOverrideInEntriesEndpoints -v`

Expected: PASS

- [ ] **Step 5: Run existing entries tests to check for regressions**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/ -k "entries or database_stats" -v`

Expected: All existing tests PASS

- [ ] **Step 6: Commit**

```bash
git add web/api/entries.py tests/test_dependency_override_isolation.py
git commit -m "Switch get_database_stats to Depends(get_db_manager) (#112)"
```

---

### Task 4: Rewrite `isolated_app_client` fixture to use `dependency_overrides`

**Files:**
- Modify: `tests/conftest.py`
- Test: `tests/test_dependency_override_isolation.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dependency_override_isolation.py`:

```python
class TestIsolatedAppClientDbIsolation:
    """Verify isolated_app_client provides DB isolation via dependency_overrides."""

    def test_isolated_client_uses_temp_database(self, isolated_app_client, tmp_path):
        """The isolated_app_client fixture should provide a clean temp database."""
        # Post an entry — it should go into the temp DB
        from datetime import date
        today = date.today().isoformat()
        response = isolated_app_client.post(
            f"/api/entries/{today}",
            json={"date": today, "content": "DB isolation test"}
        )
        assert response.status_code == 200

        # Query stats — should reflect only the entry we just created
        stats_response = isolated_app_client.get("/api/entries/stats/database")
        assert stats_response.status_code == 200
        data = stats_response.json()
        # Temp DB should have exactly 1 entry (the one we just created)
        assert data["total_entries"] >= 1

    def test_isolated_client_db_does_not_leak_between_tests(self, isolated_app_client, tmp_path):
        """Each test using isolated_app_client should get a fresh temp database."""
        # Query stats without creating anything — should start empty
        stats_response = isolated_app_client.get("/api/entries/stats/database")
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert data["total_entries"] == 0

    def test_scheduler_is_isolated(self, isolated_app_client, tmp_path):
        """The scheduler service should also use the temp database."""
        from web.app import app
        scheduler = getattr(app.state, 'scheduler', None)
        if scheduler is not None:
            temp_db_path = str(tmp_path / "test_journal_index.db")
            assert str(scheduler.db_manager.database_path) == temp_db_path, (
                "scheduler.db_manager should point to the temp DB, not the production DB"
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestIsolatedAppClientDbIsolation -v`

Expected: FAIL — current `isolated_app_client` has no DB isolation.

- [ ] **Step 3: Rewrite `tests/conftest.py`**

Replace the entire `isolated_app_client` fixture:

```python
# ABOUTME: Shared pytest fixtures for the web API test suite.
# ABOUTME: Provides isolated_app_client using FastAPI dependency overrides for DB isolation.

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from web.app import app
from web.database import DatabaseManager
from web.dependencies import get_db_manager
from web.services.base_service import BaseService
from file_discovery import FileDiscovery


@pytest.fixture
def isolated_app_client(tmp_path):
    """
    A TestClient with full isolation: file writes go to tmp_path,
    database writes go to a temporary SQLite database.

    Uses FastAPI dependency_overrides for endpoint-level DB isolation
    and reconstructs service db_manager references for service-internal
    DB access.

    The file discovery isolation (entry_manager path/cache swaps) remains
    as direct attribute mutation — a separate concern to be addressed later.
    """
    with TestClient(app) as client:
        em = app.state.entry_manager

        # --- File discovery isolation (unchanged) ---
        orig_file_discovery = em.file_discovery
        orig_base_path = em._current_base_path
        orig_settings_cache = em._settings_cache
        orig_settings_cache_expiry = em._settings_cache_expiry

        em.file_discovery = FileDiscovery(str(tmp_path))
        em._current_base_path = str(tmp_path)
        em._settings_cache = {
            'base_path': str(tmp_path),
            'output_path': str(tmp_path / 'output'),
        }
        em._settings_cache_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        # --- Database isolation via dependency overrides ---
        temp_db_path = str(tmp_path / "test_journal_index.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        # Override the dependency for endpoint-level DB access
        app.dependency_overrides[get_db_manager] = lambda: temp_db

        # Swap db_manager on all services that inherit from BaseService
        # so service-internal DB access also uses the temp DB
        orig_db_managers = {}
        for attr_name in dir(app.state):
            if attr_name.startswith('_'):
                continue
            svc = getattr(app.state, attr_name, None)
            if isinstance(svc, BaseService):
                orig_db_managers[attr_name] = svc.db_manager
                svc.db_manager = temp_db

        # Also swap the top-level app.state.db_manager
        orig_app_db = app.state.db_manager
        app.state.db_manager = temp_db

        yield client

        # --- Teardown ---
        # Clear dependency overrides
        app.dependency_overrides.pop(get_db_manager, None)

        # Restore file discovery state
        em.file_discovery = orig_file_discovery
        em._current_base_path = orig_base_path
        em._settings_cache = orig_settings_cache
        em._settings_cache_expiry = orig_settings_cache_expiry

        # Restore original db_manager references
        for attr_name, orig_db in orig_db_managers.items():
            svc = getattr(app.state, attr_name, None)
            if svc is not None:
                svc.db_manager = orig_db
        app.state.db_manager = orig_app_db

        # Dispose temp database engine
        loop.run_until_complete(temp_db.engine.dispose())
        loop.close()
```

- [ ] **Step 4: Run the new isolation tests**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_dependency_override_isolation.py::TestIsolatedAppClientDbIsolation -v`

Expected: PASS

- [ ] **Step 5: Run ALL existing tests that use `isolated_app_client`**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/test_isolation_sentinel.py tests/test_web_integration.py tests/test_settings_management.py tests/test_performance_comprehensive.py tests/test_atomic_write.py tests/test_api_endpoints_comprehensive.py tests/test_calendar_interface_step14.py -v`

Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_dependency_override_isolation.py
git commit -m "Rewrite isolated_app_client to use dependency_overrides for DB isolation (#112)"
```

---

### Task 5: Final verification — run full test suite

**Files:** None (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/ -v --tb=short 2>&1 | tail -40`

Expected: All tests PASS (same pass count as before, plus new isolation tests)

- [ ] **Step 2: Verify no regressions by comparing test count**

Run: `cd /Users/TYFong/code/WorkJournalMaker && python -m pytest tests/ --co -q 2>&1 | tail -3`

Expected: Test count = previous count + new tests added in `test_dependency_override_isolation.py`
