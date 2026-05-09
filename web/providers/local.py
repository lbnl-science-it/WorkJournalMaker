# ABOUTME: Local username/password authentication provider using bcrypt and JWT.
# ABOUTME: Manages user verification, token issuance, refresh token rotation, and revocation.

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select

from config_manager import AuthConfig
from web.auth import AuthProvider, User, TokenPair, encode_access_token, decode_access_token
from web.database import DatabaseManager, UserAccount, RefreshToken


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class LocalAuthProvider:
    """Authenticates users against local database with bcrypt-hashed passwords."""

    def __init__(self, db: DatabaseManager, config: AuthConfig):
        self.db = db
        self.config = config

    async def authenticate(self, credentials: dict) -> TokenPair:
        """Verify username/password and return a token pair."""
        username = credentials.get("username", "")
        password = credentials.get("password", "")

        async with self.db.get_session() as session:
            stmt = select(UserAccount).where(UserAccount.username == username)
            result = await session.execute(stmt)
            account = result.scalar_one_or_none()

        if account is None:
            raise AuthenticationError("Invalid username or password")

        if not account.is_active:
            raise AuthenticationError("Account is disabled")

        if not bcrypt.checkpw(password.encode(), account.password_hash.encode()):
            raise AuthenticationError("Invalid username or password")

        user = User(id=account.id, username=account.username, role=account.role)
        return await self._issue_token_pair(user)

    async def validate_token(self, token: str) -> User:
        """Decode a JWT access token and return the User."""
        payload = decode_access_token(token, self.config.secret_key)
        return User(
            id=payload["user_id"],
            username=payload["username"],
            role=payload["role"],
        )

    async def refresh_token(self, raw_refresh_token: str) -> TokenPair:
        """Exchange a valid refresh token for a new token pair."""
        token_hash = self._hash_refresh_token(raw_refresh_token)

        async with self.db.get_session() as session:
            stmt = select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
            )
            result = await session.execute(stmt)
            stored = result.scalar_one_or_none()

            if stored is None:
                raise AuthenticationError("Invalid or revoked refresh token")

            if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise AuthenticationError("Refresh token has expired")

            # Revoke the old token (rotation)
            stored.revoked = True
            await session.commit()

        # Look up user to build new tokens
        async with self.db.get_session() as session:
            stmt = select(UserAccount).where(UserAccount.id == stored.user_id)
            result = await session.execute(stmt)
            account = result.scalar_one_or_none()

        if account is None or not account.is_active:
            raise AuthenticationError("User account not found or disabled")

        user = User(id=account.id, username=account.username, role=account.role)
        return await self._issue_token_pair(user)

    async def revoke_token(self, raw_refresh_token: str) -> None:
        """Revoke a refresh token (logout)."""
        token_hash = self._hash_refresh_token(raw_refresh_token)

        async with self.db.get_session() as session:
            stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            result = await session.execute(stmt)
            stored = result.scalar_one_or_none()
            if stored:
                stored.revoked = True
                await session.commit()

    async def _issue_token_pair(self, user: User) -> TokenPair:
        """Create a new access + refresh token pair and persist the refresh token hash."""
        access_token = encode_access_token(
            user, self.config.secret_key, ttl_seconds=self.config.access_token_ttl
        )
        raw_refresh = uuid.uuid4().hex + uuid.uuid4().hex
        token_hash = self._hash_refresh_token(raw_refresh)

        async with self.db.get_session() as session:
            session.add(RefreshToken(
                id=str(uuid.uuid4()),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.config.refresh_token_ttl),
            ))
            await session.commit()

        return TokenPair(access_token=access_token, refresh_token=raw_refresh)

    @staticmethod
    def _hash_refresh_token(raw_token: str) -> str:
        """SHA-256 hash a raw refresh token for storage."""
        return hashlib.sha256(raw_token.encode()).hexdigest()
