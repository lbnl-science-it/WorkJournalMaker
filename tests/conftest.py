# ABOUTME: Shared pytest fixtures for the web API test suite.
# ABOUTME: Provides isolated_app_client that redirects all file writes to tmp_path.

import pytest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from web.app import app
from file_discovery import FileDiscovery


@pytest.fixture
def isolated_app_client(tmp_path):
    """
    A TestClient that redirects all entry_manager file writes to tmp_path.

    Patches app.state.entry_manager after the app lifespan startup so that
    FileDiscovery writes to tmp_path instead of ~/Desktop/worklogs/.
    The settings cache is pinned to prevent re-initialization from DB or config.

    WARNING: This fixture mutates a module-level singleton (app.state.entry_manager)
    and restores it on teardown. It is not compatible with pytest-xdist parallel
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

        yield client

        # Restore originals so the module-level singleton isn't permanently mutated
        em.file_discovery = orig_file_discovery
        em._current_base_path = orig_base_path
        em._settings_cache = orig_settings_cache
        em._settings_cache_expiry = orig_settings_cache_expiry
