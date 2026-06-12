# ABOUTME: Tests for CSRF protection middleware on state-changing endpoints.
# ABOUTME: Verifies that POST/PUT/DELETE/PATCH require X-Requested-With header.

"""
Tests for CSRF protection middleware.

Validates that state-changing requests (POST, PUT, DELETE, PATCH) are rejected
unless they carry the X-Requested-With header, and that safe methods and
auth endpoints are exempt.
"""

import pytest
from fastapi.testclient import TestClient
from web.app import app


class TestCSRFMiddleware:
    """Test CSRF protection via required custom header."""

    @pytest.fixture
    def client(self, isolated_app_client):
        """Isolated client WITH X-Requested-With (simulates legitimate JS)."""
        yield isolated_app_client

    @pytest.fixture
    def bare_client(self):
        """Client WITHOUT X-Requested-With (simulates cross-origin attack)."""
        with TestClient(app) as c:
            yield c

    # --- Rejection: state-changing requests WITHOUT the header ---

    def test_post_without_csrf_header_rejected(self, bare_client):
        """POST without X-Requested-With should get 403."""
        response = bare_client.post(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
        )
        assert response.status_code == 403
        assert "csrf" in response.json()["detail"].lower()

    def test_put_without_csrf_header_rejected(self, bare_client):
        """PUT without X-Requested-With should get 403."""
        response = bare_client.put(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
        )
        assert response.status_code == 403

    def test_delete_without_csrf_header_rejected(self, bare_client):
        """DELETE without X-Requested-With should get 403."""
        response = bare_client.delete("/api/entries/2024-01-15")
        assert response.status_code == 403

    def test_patch_without_csrf_header_rejected(self, bare_client):
        """PATCH without X-Requested-With should get 403."""
        response = bare_client.patch("/api/entries/2024-01-15")
        assert response.status_code == 403

    # --- Acceptance: state-changing requests WITH the header ---

    def test_post_with_csrf_header_allowed(self, client):
        """POST with X-Requested-With should pass through to the endpoint."""
        response = client.post(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
        )
        assert response.status_code != 403

    def test_put_with_csrf_header_allowed(self, client):
        """PUT with X-Requested-With should pass through."""
        response = client.put(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "updated"},
        )
        assert response.status_code != 403

    def test_delete_with_csrf_header_allowed(self, client):
        """DELETE with X-Requested-With should pass through."""
        response = client.delete("/api/entries/2024-01-15")
        assert response.status_code != 403

    # --- Safe methods are always allowed (no header needed) ---

    def test_get_without_header_allowed(self, bare_client):
        """GET requests should pass without X-Requested-With."""
        response = bare_client.get("/api/health")
        assert response.status_code != 403

    def test_options_without_header_allowed(self, bare_client):
        """OPTIONS requests should pass without X-Requested-With."""
        response = bare_client.options("/api/entries/2024-01-15")
        assert response.status_code != 403

    def test_head_without_header_allowed(self, bare_client):
        """HEAD requests should pass without X-Requested-With."""
        response = bare_client.head("/api/health")
        assert response.status_code != 403

    # --- Exempt paths (no header needed even for POST) ---

    def test_login_exempt_from_csrf(self, bare_client):
        """POST /api/auth/login should work without X-Requested-With."""
        response = bare_client.post(
            "/api/auth/login",
            json={"username": "test", "password": "test"},
        )
        # Should not be 403 — login is exempt
        # (May be 503 if auth disabled, but not 403)
        assert response.status_code != 403

    def test_refresh_exempt_from_csrf(self, bare_client):
        """POST /api/auth/refresh should work without X-Requested-With."""
        response = bare_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "fake-token"},
        )
        assert response.status_code != 403

    # --- Header value flexibility ---

    def test_any_header_value_accepted(self, bare_client):
        """Any non-empty value for X-Requested-With should be accepted."""
        response = bare_client.post(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
            headers={"X-Requested-With": "fetch"},
        )
        assert response.status_code != 403

    # --- Rejection on non-entry endpoints too ---

    def test_settings_post_without_csrf_rejected(self, bare_client):
        """POST to settings without header should be rejected."""
        response = bare_client.post(
            "/api/settings/bulk-update",
            json={"settings": {}},
        )
        assert response.status_code == 403

    def test_sync_post_without_csrf_rejected(self, bare_client):
        """POST to sync without header should be rejected."""
        response = bare_client.post("/api/sync/full")
        assert response.status_code == 403
