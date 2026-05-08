# ABOUTME: Shared pytest fixtures for the web API test suite.
# ABOUTME: Provides isolated_app_client that redirects file and DB writes to tmp_path.

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from web.app import app
from web.database import DatabaseManager
from file_discovery import FileDiscovery


@pytest.fixture
def isolated_app_client(tmp_path):
    """
    A TestClient that redirects all entry_manager file writes to tmp_path
    and all database writes to a temporary SQLite database.

    Patches app.state services after the app lifespan startup so that:
    1. FileDiscovery writes to tmp_path instead of ~/Desktop/worklogs/
    2. All services use a temp database instead of web/journal_index.db

    WARNING: This fixture mutates module-level singletons (app.state services)
    and restores them on teardown. It is not compatible with pytest-xdist parallel
    execution, which runs tests in separate workers sharing the same process state.
    """
    with TestClient(app) as client:
        em = app.state.entry_manager

        # Save originals for restoration
        orig_file_discovery = em.file_discovery
        orig_base_path = em._current_base_path
        orig_settings_cache = em._settings_cache
        orig_settings_cache_expiry = em._settings_cache_expiry

        # Redirect file discovery to tmp_path
        em.file_discovery = FileDiscovery(str(tmp_path))
        em._current_base_path = str(tmp_path)

        # Pin settings cache so _get_current_settings() never re-reads from DB
        em._settings_cache = {
            'base_path': str(tmp_path),
            'output_path': str(tmp_path / 'output'),
        }
        em._settings_cache_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        # --- Database isolation ---
        temp_db = DatabaseManager(str(tmp_path / "test_journal_index.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        # Swap db_manager on every service that holds one (introspection-based
        # so new services are picked up automatically).
        orig_db_managers = {}
        for name, svc in app.state._state.items():
            if name != 'db_manager' and hasattr(svc, 'db_manager'):
                orig_db_managers[name] = svc.db_manager
                svc.db_manager = temp_db

        orig_app_db = app.state.db_manager
        app.state.db_manager = temp_db

        yield client

        # Restore originals so the module-level singletons aren't permanently mutated
        em.file_discovery = orig_file_discovery
        em._current_base_path = orig_base_path
        em._settings_cache = orig_settings_cache
        em._settings_cache_expiry = orig_settings_cache_expiry

        for name in orig_db_managers:
            svc = getattr(app.state, name, None)
            if svc is not None:
                svc.db_manager = orig_db_managers[name]
        app.state.db_manager = orig_app_db

        if temp_db.engine:
            loop.run_until_complete(temp_db.engine.dispose())
        loop.close()
