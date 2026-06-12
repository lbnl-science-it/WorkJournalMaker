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
        """Use the shared isolated test client."""
        yield isolated_app_client

    # --- Rejection: state-changing requests WITHOUT the header ---

    def test_post_without_csrf_header_rejected(self, client):
        """POST without X-Requested-With should get 403."""
        response = client.post(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
        )
        assert response.status_code == 403
        assert "csrf" in response.json()["detail"].lower()

    def test_put_without_csrf_header_rejected(self, client):
        """PUT without X-Requested-With should get 403."""
        response = client.put(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
        )
        assert response.status_code == 403

    def test_delete_without_csrf_header_rejected(self, client):
        """DELETE without X-Requested-With should get 403."""
        response = client.delete("/api/entries/2024-01-15")
        assert response.status_code == 403

    def test_patch_without_csrf_header_rejected(self, client):
        """PATCH without X-Requested-With should get 403."""
        response = client.patch("/api/entries/2024-01-15")
        assert response.status_code == 403

    # --- Acceptance: state-changing requests WITH the header ---

    def test_post_with_csrf_header_allowed(self, client):
        """POST with X-Requested-With should pass through to the endpoint."""
        response = client.post(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        # Should NOT be 403 — the request reaches the actual endpoint
        assert response.status_code != 403

    def test_put_with_csrf_header_allowed(self, client):
        """PUT with X-Requested-With should pass through."""
        response = client.put(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "updated"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code != 403

    def test_delete_with_csrf_header_allowed(self, client):
        """DELETE with X-Requested-With should pass through."""
        response = client.delete(
            "/api/entries/2024-01-15",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code != 403

    # --- Safe methods are always allowed ---

    def test_get_without_header_allowed(self, client):
        """GET requests should pass without X-Requested-With."""
        response = client.get("/api/health")
        assert response.status_code != 403

    def test_options_without_header_allowed(self, client):
        """OPTIONS requests should pass without X-Requested-With."""
        response = client.options("/api/entries/2024-01-15")
        assert response.status_code != 403

    def test_head_without_header_allowed(self, client):
        """HEAD requests should pass without X-Requested-With."""
        response = client.head("/api/health")
        assert response.status_code != 403

    # --- Exempt paths ---

    def test_login_exempt_from_csrf(self, client):
        """POST /api/auth/login should work without X-Requested-With."""
        response = client.post(
            "/api/auth/login",
            json={"username": "test", "password": "test"},
        )
        # Should not be 403 — login is exempt from CSRF
        # (It may be 503 if auth is disabled, but not 403)
        assert response.status_code != 403

    def test_refresh_exempt_from_csrf(self, client):
        """POST /api/auth/refresh should work without X-Requested-With."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "fake-token"},
        )
        assert response.status_code != 403

    # --- Static and page routes are exempt ---

    def test_static_assets_not_affected(self, client):
        """GET requests for static assets should not be affected."""
        response = client.get("/static/css/style.css")
        assert response.status_code != 403

    def test_page_routes_not_affected(self, client):
        """GET requests for page routes should not be affected."""
        response = client.get("/")
        assert response.status_code != 403

    # --- Header value flexibility ---

    def test_any_header_value_accepted(self, client):
        """Any non-empty value for X-Requested-With should be accepted."""
        response = client.post(
            "/api/entries/2024-01-15",
            json={"date": "2024-01-15", "content": "test"},
            headers={"X-Requested-With": "fetch"},
        )
        assert response.status_code != 403

    # --- Settings endpoints (admin-only, should still require CSRF) ---

    def test_settings_post_without_csrf_rejected(self, client):
        """POST to settings endpoints without header should be rejected."""
        response = client.post(
            "/api/settings/bulk-update",
            json={"settings": {}},
        )
        assert response.status_code == 403

    def test_settings_post_with_csrf_allowed(self, client):
        """POST to settings with header should pass through."""
        response = client.post(
            "/api/settings/bulk-update",
            json={"settings": {}},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code != 403

    # --- Sync endpoints ---

    def test_sync_post_without_csrf_rejected(self, client):
        """POST to sync endpoints without header should be rejected."""
        response = client.post("/api/sync/full")
        assert response.status_code == 403

    def test_sync_post_with_csrf_allowed(self, client):
        """POST to sync with header should pass through."""
        response = client.post(
            "/api/sync/full",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code != 403
