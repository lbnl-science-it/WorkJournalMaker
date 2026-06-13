# ABOUTME: Tests for CORS middleware configuration (GH#97).
# ABOUTME: Verifies allow_headers uses an explicit list, not a wildcard.

"""
Tests for GH#97: CORS misconfiguration - allow_headers wildcard with credentials.

When allow_credentials=True, allow_headers=["*"] is overly permissive and
facilitates cross-origin data exfiltration if the origin list is ever expanded.
The middleware must use an explicit header allowlist.
"""

import pytest
from starlette.middleware.cors import CORSMiddleware

from web.app import app


def _get_cors_middleware():
    """Extract the CORSMiddleware instance from the app middleware stack."""
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware
    pytest.fail("CORSMiddleware not found in app middleware stack")


class TestCORSHeaderRestrictions:
    """Verify CORS allow_headers is an explicit list, not a wildcard."""

    def test_cors_middleware_exists(self):
        """CORS middleware must be registered on the app."""
        middleware = _get_cors_middleware()
        assert middleware is not None

    def test_allow_headers_not_wildcard(self):
        """allow_headers must not use the wildcard '*'."""
        middleware = _get_cors_middleware()
        allow_headers = middleware.kwargs.get("allow_headers", [])
        assert "*" not in allow_headers, (
            "allow_headers=['*'] with allow_credentials=True is a dangerous "
            "pattern. Use an explicit list of required headers."
        )

    def test_allow_headers_includes_content_type(self):
        """Content-Type must be in allow_headers for JSON API requests."""
        middleware = _get_cors_middleware()
        allow_headers = middleware.kwargs.get("allow_headers", [])
        normalized = [h.lower() for h in allow_headers]
        assert "content-type" in normalized

    def test_allow_headers_includes_x_requested_with(self):
        """X-Requested-With must be allowed since CSRF middleware requires it."""
        middleware = _get_cors_middleware()
        allow_headers = middleware.kwargs.get("allow_headers", [])
        normalized = [h.lower() for h in allow_headers]
        assert "x-requested-with" in normalized

    def test_allow_headers_includes_authorization(self):
        """Authorization must be allowed for authenticated API requests."""
        middleware = _get_cors_middleware()
        allow_headers = middleware.kwargs.get("allow_headers", [])
        normalized = [h.lower() for h in allow_headers]
        assert "authorization" in normalized


class TestCORSPreflightBehavior:
    """Verify CORS preflight responses reflect the explicit header list."""

    @pytest.fixture
    def client(self, isolated_app_client):
        yield isolated_app_client

    def test_preflight_returns_explicit_headers(self, client):
        """OPTIONS preflight must list explicit headers, not '*'."""
        response = client.options(
            "/api/settings/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        allow_headers = response.headers.get("access-control-allow-headers", "")
        assert allow_headers != "*", (
            "Preflight response must not echo '*' for allow-headers"
        )

    def test_preflight_rejects_unlisted_origin(self, client):
        """Preflight from an unlisted origin should not include allow-origin."""
        response = client.options(
            "/api/settings/health",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin != "http://evil.example.com"
