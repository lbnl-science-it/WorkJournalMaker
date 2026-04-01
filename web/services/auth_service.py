# ABOUTME: Authentication service supporting API key and Google OAuth2
# ABOUTME: Disabled in local mode, returns user_id="local" for all requests

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    authenticated: bool
    user_id: Optional[str] = None
    error: Optional[str] = None


class AuthService:
    """Authentication service for multi-user server mode."""

    def __init__(
        self,
        enabled: bool = False,
        provider: str = "api_key",
        api_keys: Optional[Dict[str, str]] = None,
        google_client_id: str = "",
        allowed_domains: Optional[list] = None,
    ):
        self.enabled = enabled
        self.provider = provider
        self.api_keys = api_keys or {}
        self.google_client_id = google_client_id
        self.allowed_domains = allowed_domains or []

    def authenticate_api_key(self, key: str) -> AuthResult:
        """Authenticate using an API key."""
        if not self.enabled:
            return AuthResult(authenticated=True, user_id="local")

        user_id = self.api_keys.get(key)
        if user_id:
            return AuthResult(authenticated=True, user_id=user_id)
        return AuthResult(authenticated=False, error="Invalid API key")

    def authenticate_bearer_token(self, token: str) -> AuthResult:
        """Authenticate using a bearer token (Google OAuth2)."""
        if not self.enabled:
            return AuthResult(authenticated=True, user_id="local")

        # Google OAuth2 token verification - placeholder for real implementation
        # In production: verify token with Google, extract email, check allowed_domains
        return AuthResult(authenticated=False, error="OAuth2 not yet implemented")
