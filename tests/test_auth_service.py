# ABOUTME: Tests for authentication service.
# ABOUTME: Covers API key auth, disabled auth mode, and auth result validation.
"""Tests for authentication service."""
import pytest
from web.services.auth_service import AuthService, AuthResult


class TestAPIKeyAuth:
    def test_valid_api_key(self):
        """Valid API key returns authenticated result."""
        service = AuthService(
            enabled=True,
            provider="api_key",
            api_keys={"test-key-123": "user-1"},
        )
        result = service.authenticate_api_key("test-key-123")
        assert result.authenticated is True
        assert result.user_id == "user-1"

    def test_invalid_api_key(self):
        """Invalid API key returns unauthenticated result."""
        service = AuthService(
            enabled=True,
            provider="api_key",
            api_keys={"test-key-123": "user-1"},
        )
        result = service.authenticate_api_key("wrong-key")
        assert result.authenticated is False

    def test_auth_disabled_returns_local(self):
        """When auth is disabled, all requests are user 'local'."""
        service = AuthService(enabled=False)
        result = service.authenticate_api_key("anything")
        assert result.authenticated is True
        assert result.user_id == "local"


class TestAuthResult:
    def test_auth_result_fields(self):
        result = AuthResult(authenticated=True, user_id="user-1")
        assert result.authenticated is True
        assert result.user_id == "user-1"
        assert result.error is None

    def test_auth_result_with_error(self):
        result = AuthResult(authenticated=False, error="Invalid token")
        assert result.authenticated is False
        assert result.user_id is None
        assert result.error == "Invalid token"
