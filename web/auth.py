# ABOUTME: Authentication types, provider protocol, and JWT encode/decode utilities.
# ABOUTME: Provides the pluggable auth provider interface and token validation.

from dataclasses import dataclass
from typing import Protocol
from datetime import datetime, timedelta, timezone

import jwt


@dataclass
class User:
    """Authenticated user identity."""
    id: str
    username: str
    role: str


@dataclass
class TokenPair:
    """Access and refresh token pair returned after authentication."""
    access_token: str
    refresh_token: str


class AuthProvider(Protocol):
    """Pluggable authentication provider interface."""

    async def authenticate(self, credentials: dict) -> TokenPair: ...
    async def validate_token(self, token: str) -> User: ...
    async def refresh_token(self, raw_refresh_token: str) -> TokenPair: ...
    async def revoke_token(self, raw_refresh_token: str) -> None: ...


def encode_access_token(user: User, secret: str, ttl_seconds: int = 1800) -> str:
    """Encode a JWT access token for the given user."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> dict:
    """Decode and validate a JWT access token. Raises on expiry or bad signature."""
    return jwt.decode(token, secret, algorithms=["HS256"])
