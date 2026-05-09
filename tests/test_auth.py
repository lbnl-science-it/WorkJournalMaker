# ABOUTME: Unit tests for auth configuration, JWT utilities, and FastAPI dependencies.
# ABOUTME: Validates auth-disabled mode, token lifecycle, and role-based access control.

import asyncio
import os
import pytest
from unittest.mock import patch
from config_manager import AppConfig, AuthConfig, ConfigManager
from datetime import date
from web.database import DatabaseManager, JournalEntryIndex, UserAccount, RefreshToken


class TestAuthConfig:
    """Tests for AuthConfig dataclass and its integration with AppConfig."""

    def test_auth_config_defaults(self):
        config = AuthConfig()
        assert config.enabled is False
        assert config.provider == "local"
        assert config.secret_key == ""
        assert config.access_token_ttl == 1800
        assert config.refresh_token_ttl == 604800

    def test_app_config_includes_auth(self):
        config = AppConfig()
        assert hasattr(config, "auth")
        assert isinstance(config.auth, AuthConfig)
        assert config.auth.enabled is False


class TestAuthDatabaseModels:
    """Tests for auth-related database models."""

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_auth.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    def test_create_user_account(self, db):
        from sqlalchemy import select
        import uuid

        async def _test():
            async with db.get_session() as session:
                user = UserAccount(
                    id=str(uuid.uuid4()),
                    username="testadmin",
                    password_hash="$2b$12$fakehash",
                    role="admin",
                    is_active=True,
                )
                session.add(user)
                await session.commit()

                stmt = select(UserAccount).where(UserAccount.username == "testadmin")
                result = await session.execute(stmt)
                found = result.scalar_one()
                assert found.username == "testadmin"
                assert found.role == "admin"
                assert found.is_active is True

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_create_refresh_token(self, db):
        from sqlalchemy import select
        import uuid
        from datetime import datetime, timedelta, timezone

        async def _test():
            async with db.get_session() as session:
                user_id = str(uuid.uuid4())
                user = UserAccount(
                    id=user_id,
                    username="tokenuser",
                    password_hash="$2b$12$fakehash",
                    role="user",
                )
                session.add(user)
                await session.commit()

                token = RefreshToken(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    token_hash="sha256hashvalue",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                )
                session.add(token)
                await session.commit()

                stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
                result = await session.execute(stmt)
                found = result.scalar_one()
                assert found.token_hash == "sha256hashvalue"
                assert found.revoked is False

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()


class TestAuthTypes:
    """Tests for User and TokenPair dataclasses."""

    def test_user_creation(self):
        from web.auth import User
        user = User(id="u1", username="alice", role="user")
        assert user.id == "u1"
        assert user.username == "alice"
        assert user.role == "user"

    def test_token_pair_creation(self):
        from web.auth import TokenPair
        pair = TokenPair(access_token="acc", refresh_token="ref")
        assert pair.access_token == "acc"
        assert pair.refresh_token == "ref"


class TestJWTUtilities:
    """Tests for JWT token encoding and decoding."""

    SECRET = "test-secret-key-for-jwt-testing!!"

    def test_encode_decode_roundtrip(self):
        from web.auth import User, encode_access_token, decode_access_token
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        decoded = decode_access_token(token, self.SECRET)
        assert decoded["user_id"] == "u1"
        assert decoded["username"] == "alice"
        assert decoded["role"] == "user"
        assert "exp" in decoded

    def test_decode_expired_token_raises(self):
        import jwt as pyjwt
        from web.auth import User, encode_access_token, decode_access_token
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=-1)
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_access_token(token, self.SECRET)

    def test_decode_invalid_token_raises(self):
        import jwt as pyjwt
        from web.auth import decode_access_token
        with pytest.raises(pyjwt.DecodeError):
            decode_access_token("not.a.valid.token", self.SECRET)

    def test_decode_wrong_secret_raises(self):
        import jwt as pyjwt
        from web.auth import User, encode_access_token, decode_access_token
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        with pytest.raises(pyjwt.InvalidSignatureError):
            decode_access_token(token, "wrong-secret")


class TestGetCurrentUser:
    """Tests for the get_current_user FastAPI dependency."""

    SECRET = "test-secret-key-for-dependency-testing-32b"

    def _make_request(self, token=None, enabled=True):
        from unittest.mock import MagicMock
        request = MagicMock()
        request.app.state.auth_config = AuthConfig(enabled=enabled, secret_key=self.SECRET)
        request.app.state.auth_provider = None
        if token:
            request.headers = {"authorization": f"Bearer {token}"}
        else:
            request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        from web.auth import User, encode_access_token, get_current_user
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        request = self._make_request(token)
        result = await get_current_user(request)
        assert result.id == "u1"
        assert result.username == "alice"

    @pytest.mark.asyncio
    async def test_missing_header_raises_401(self):
        from fastapi import HTTPException
        from web.auth import get_current_user
        request = self._make_request(token=None)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        from fastapi import HTTPException
        from web.auth import get_current_user
        request = self._make_request(token="garbage.token.here")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        from fastapi import HTTPException
        from web.auth import User, encode_access_token, get_current_user
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=-1)
        request = self._make_request(token)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_auth_disabled_returns_default_admin(self):
        from web.auth import get_current_user
        request = self._make_request(enabled=False)
        result = await get_current_user(request)
        assert result.id == "default"
        assert result.role == "admin"


class TestRequireAdmin:
    """Tests for the require_admin FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        from web.auth import User, require_admin
        user = User(id="u1", username="admin", role="admin")
        result = await require_admin(user)
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        from fastapi import HTTPException
        from web.auth import User, require_admin
        user = User(id="u2", username="viewer", role="user")
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user)
        assert exc_info.value.status_code == 403


class TestAuthConfigLoading:
    """Tests for loading auth config from files and environment."""

    def test_secret_key_from_env_var(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("auth:\n  enabled: true\n")
        with patch.dict(os.environ, {"WJS_AUTH_SECRET_KEY": "test-secret-key-12345"}):
            manager = ConfigManager(config_path=config_file)
            assert manager.config.auth.secret_key == "test-secret-key-12345"
            assert manager.config.auth.enabled is True


class TestJournalEntryUserScoping:
    """Tests for user_id column on journal entries."""

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_scoping.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    def test_entry_has_user_id_column(self):
        assert hasattr(JournalEntryIndex, "user_id")

    def test_entry_default_user_id(self, db):
        from sqlalchemy import select

        async def _test():
            async with db.get_session() as session:
                entry = JournalEntryIndex(
                    date=date(2026, 5, 1),
                    file_path="/tmp/test.txt",
                    week_ending_date=date(2026, 5, 2),
                )
                session.add(entry)
                await session.commit()

                stmt = select(JournalEntryIndex).where(
                    JournalEntryIndex.date == date(2026, 5, 1)
                )
                result = await session.execute(stmt)
                found = result.scalar_one()
                assert found.user_id == "default"

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()
