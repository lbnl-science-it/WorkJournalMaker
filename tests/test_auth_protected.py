# ABOUTME: Tests that existing endpoints enforce authentication correctly.
# ABOUTME: Validates 401 without token, 200 with token, and 403 for admin-only routes.

import asyncio
import pytest
from fastapi.testclient import TestClient

from web.app import app
from web.database import DatabaseManager
from config_manager import AuthConfig
from web.auth import User, encode_access_token


SECRET = "protected-endpoint-test-secret!!"


@pytest.fixture
def protected_client(tmp_path):
    """TestClient with auth ENABLED."""
    with TestClient(app) as client:
        orig_auth_config = getattr(app.state, 'auth_config', None)
        orig_auth_provider = getattr(app.state, 'auth_provider', None)

        auth_config = AuthConfig(enabled=True, secret_key=SECRET)
        app.state.auth_config = auth_config
        app.state.auth_provider = None

        # Swap to temp DB
        db = DatabaseManager(str(tmp_path / "test_protected.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())

        orig_db = app.state.db_manager
        app.state.db_manager = db
        for name, svc in app.state._state.items():
            if name not in ('db_manager', 'auth_config', 'auth_provider') and hasattr(svc, 'db_manager'):
                svc.db_manager = db

        yield client

        app.state.auth_config = orig_auth_config
        app.state.auth_provider = orig_auth_provider
        app.state.db_manager = orig_db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()


def _token(role="user"):
    user = User(id="u1", username="tester", role=role)
    return encode_access_token(user, SECRET, ttl_seconds=300)


class TestEntriesAuth:
    """Entries endpoints require user-level auth."""

    def test_list_entries_no_token_401(self, protected_client):
        resp = protected_client.get("/api/entries/")
        assert resp.status_code == 401

    def test_list_entries_with_token_200(self, protected_client):
        resp = protected_client.get(
            "/api/entries/",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_delete_entry_user_role_403(self, protected_client):
        resp = protected_client.delete(
            "/api/entries/2026-01-01",
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403


class TestSettingsAuth:
    """Settings endpoints enforce appropriate auth levels."""

    def test_get_settings_no_token_401(self, protected_client):
        resp = protected_client.get("/api/settings/")
        assert resp.status_code == 401

    def test_get_settings_with_token_200(self, protected_client):
        resp = protected_client.get(
            "/api/settings/",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_reset_all_no_token_401(self, protected_client):
        resp = protected_client.post("/api/settings/reset-all")
        assert resp.status_code == 401

    def test_reset_all_user_role_403(self, protected_client):
        resp = protected_client.post(
            "/api/settings/reset-all",
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403

    def test_reset_all_admin_role_allowed(self, protected_client):
        resp = protected_client.post(
            "/api/settings/reset-all",
            headers={"Authorization": f"Bearer {_token('admin')}"},
        )
        # Should not be 401 or 403
        assert resp.status_code not in (401, 403)


class TestSyncAuth:
    """Sync endpoints require admin auth for state changes."""

    def test_sync_status_no_token_401(self, protected_client):
        resp = protected_client.get("/api/sync/status")
        assert resp.status_code == 401

    def test_full_sync_no_token_401(self, protected_client):
        resp = protected_client.post("/api/sync/full")
        assert resp.status_code == 401

    def test_full_sync_user_role_403(self, protected_client):
        resp = protected_client.post(
            "/api/sync/full",
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403


class TestHealthAuth:
    """Health endpoint is public; /config and /metrics require admin."""

    def test_health_public(self, protected_client):
        resp = protected_client.get("/api/health/")
        assert resp.status_code == 200

    def test_config_no_token_401(self, protected_client):
        resp = protected_client.get("/api/health/config")
        assert resp.status_code == 401

    def test_metrics_no_token_401(self, protected_client):
        resp = protected_client.get("/api/health/metrics")
        assert resp.status_code == 401


class TestAuthDisabled:
    """When auth is disabled, all endpoints work without tokens."""

    def test_entries_accessible(self, isolated_app_client):
        app.state.auth_config = AuthConfig(enabled=False)
        resp = isolated_app_client.get("/api/entries/")
        assert resp.status_code == 200

    def test_settings_accessible(self, isolated_app_client):
        app.state.auth_config = AuthConfig(enabled=False)
        resp = isolated_app_client.get("/api/settings/")
        assert resp.status_code == 200


class TestCalendarAuth:
    """Calendar endpoints require user-level auth."""

    def test_today_no_token_401(self, protected_client):
        resp = protected_client.get("/api/calendar/today")
        assert resp.status_code == 401

    def test_today_with_token_200(self, protected_client):
        resp = protected_client.get(
            "/api/calendar/today",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200


class TestSummarizationAuth:
    """Summarization endpoints enforce appropriate auth levels."""

    def test_get_tasks_no_token_401(self, protected_client):
        resp = protected_client.get("/api/summarization/tasks")
        assert resp.status_code == 401

    def test_get_tasks_with_token_200(self, protected_client):
        resp = protected_client.get(
            "/api/summarization/tasks",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_create_task_user_role_403(self, protected_client):
        resp = protected_client.post(
            "/api/summarization/tasks",
            json={"summary_type": "weekly", "start_date": "2026-01-01", "end_date": "2026-01-07"},
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403

    def test_cleanup_user_role_403(self, protected_client):
        resp = protected_client.post(
            "/api/summarization/cleanup",
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403
