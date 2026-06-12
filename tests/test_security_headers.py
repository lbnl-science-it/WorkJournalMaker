# ABOUTME: Tests for security response headers on all HTTP responses.
# ABOUTME: Verifies CSP, X-Frame-Options, X-Content-Type-Options, and other headers.

"""
Tests for GH#91: No security response headers.

Every HTTP response must include standard security headers to provide
defense-in-depth against clickjacking, MIME sniffing, and XSS.
"""

import pytest


class TestSecurityResponseHeaders:
    """Verify security headers are present on all responses."""

    @pytest.fixture
    def client(self, isolated_app_client):
        yield isolated_app_client

    def _get_response(self, client):
        """Get a typical API response to inspect headers."""
        return client.get("/api/settings/health")

    # --- Individual header checks ---

    def test_x_content_type_options(self, client):
        """X-Content-Type-Options must be 'nosniff'."""
        response = self._get_response(client)
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        """X-Frame-Options must be 'DENY'."""
        response = self._get_response(client)
        assert response.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        """Referrer-Policy must be set."""
        response = self._get_response(client)
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        """Permissions-Policy must restrict browser features."""
        response = self._get_response(client)
        value = response.headers.get("permissions-policy")
        assert value is not None
        # Should restrict at least camera, microphone, geolocation
        assert "camera=()" in value
        assert "microphone=()" in value
        assert "geolocation=()" in value

    def test_content_security_policy(self, client):
        """Content-Security-Policy must be present with key directives."""
        response = self._get_response(client)
        csp = response.headers.get("content-security-policy")
        assert csp is not None
        assert "default-src" in csp
        assert "script-src" in csp
        assert "frame-ancestors 'none'" in csp

    def test_csp_allows_self_scripts(self, client):
        """CSP script-src must include 'self' for local scripts."""
        response = self._get_response(client)
        csp = response.headers.get("content-security-policy")
        assert "'self'" in csp

    def test_csp_allows_cdn_jsdelivr(self, client):
        """CSP must allow cdn.jsdelivr.net for marked/dompurify."""
        response = self._get_response(client)
        csp = response.headers.get("content-security-policy")
        assert "cdn.jsdelivr.net" in csp

    # --- Headers present on different response types ---

    def test_headers_on_html_page(self, client):
        """Security headers must be present on HTML page responses."""
        response = client.get("/")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"

    def test_headers_on_api_endpoint(self, client):
        """Security headers must be present on API JSON responses."""
        response = client.get("/api/settings/health")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"

    def test_headers_on_error_response(self, client):
        """Security headers must be present even on error responses."""
        response = client.get("/api/settings/nonexistent_setting_key")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
