# ABOUTME: Authentication types, provider protocol, JWT utilities, and FastAPI dependencies.
# ABOUTME: Provides the pluggable auth provider interface, token validation, and route guards.

from dataclasses import dataclass
from typing import Protocol
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request, Depends, HTTPException, status


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


async def get_current_user(request: Request) -> User:
    """FastAPI dependency: extract and validate the Bearer token, return User."""
    auth_config = getattr(request.app.state, "auth_config", None)

    if auth_config is None or not auth_config.enabled:
        return User(id="default", username="default", role="admin")

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[len("Bearer "):]
    try:
        payload = decode_access_token(token, auth_config.secret_key)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return User(
            id=payload["user_id"],
            username=payload["username"],
            role=payload["role"],
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: require the current user to be an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
