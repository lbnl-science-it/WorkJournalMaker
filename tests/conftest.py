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
    and swaps service db_manager references for service-internal
    DB access.

    File discovery isolation (entry_manager path/cache swaps) uses direct
    attribute mutation, which is a separate mechanism from the DB isolation.
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
        try:
            loop.run_until_complete(temp_db.initialize())
        except Exception:
            loop.close()
            raise

        # Override the dependency for endpoint-level DB access
        app.dependency_overrides[get_db_manager] = lambda: temp_db

        # Swap db_manager on all services that have one, using _state dict for
        # reliable enumeration (dir() does not enumerate Starlette State attributes).
        orig_db_managers = {}
        for attr_name, svc in app.state._state.items():
            if isinstance(svc, BaseService) and hasattr(svc, 'db_manager'):
                orig_db_managers[attr_name] = svc.db_manager
                svc.db_manager = temp_db

        # Swap scheduler.sync_service.db_manager separately
        # because SyncScheduler does not inherit from BaseService.
        scheduler = getattr(app.state, 'scheduler', None)
        orig_scheduler_sync_service_db = None
        if scheduler is not None:
            orig_scheduler_sync_service_db = scheduler.sync_service.db_manager
            scheduler.sync_service.db_manager = temp_db

        # Also swap sync_service.db_manager (DatabaseSyncService doesn't inherit BaseService)
        sync_service = getattr(app.state, 'sync_service', None)
        orig_sync_service_db = None
        if sync_service is not None and hasattr(sync_service, 'db_manager'):
            orig_sync_service_db = sync_service.db_manager
            sync_service.db_manager = temp_db

        # Also swap the top-level app.state.db_manager
        orig_app_db = app.state.db_manager
        app.state.db_manager = temp_db

        try:
            yield client
        finally:
            # --- Teardown ---
            # Clear dependency overrides
            app.dependency_overrides.pop(get_db_manager, None)

            # Restore file discovery state
            em.file_discovery = orig_file_discovery
            em._current_base_path = orig_base_path
            em._settings_cache = orig_settings_cache
            em._settings_cache_expiry = orig_settings_cache_expiry

            # Restore original db_manager references on BaseService instances
            for attr_name, orig_db in orig_db_managers.items():
                svc = app.state._state.get(attr_name)
                if svc is not None:
                    svc.db_manager = orig_db

            # Restore scheduler references
            if scheduler is not None:
                scheduler.sync_service.db_manager = orig_scheduler_sync_service_db

            # Restore sync_service.db_manager
            if sync_service is not None and orig_sync_service_db is not None:
                sync_service.db_manager = orig_sync_service_db

            app.state.db_manager = orig_app_db

            # Dispose temp database engine
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()
