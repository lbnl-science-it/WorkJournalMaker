# ABOUTME: Unit tests for auth configuration, JWT utilities, and FastAPI dependencies.
# ABOUTME: Validates auth-disabled mode, token lifecycle, and role-based access control.

import asyncio
import os
import pytest
from unittest.mock import patch
from config_manager import AppConfig, AuthConfig, ConfigManager
from web.database import DatabaseManager, UserAccount, RefreshToken


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

    SECRET = "test-secret-key-for-jwt-testing"

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
        from web.auth import User, encode_access_token, decode_access_token
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=-1)
        with pytest.raises(Exception):
            decode_access_token(token, self.SECRET)

    def test_decode_invalid_token_raises(self):
        from web.auth import decode_access_token
        with pytest.raises(Exception):
            decode_access_token("not.a.valid.token", self.SECRET)

    def test_decode_wrong_secret_raises(self):
        from web.auth import User, encode_access_token, decode_access_token
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        with pytest.raises(Exception):
            decode_access_token(token, "wrong-secret")


class TestAuthConfigLoading:
    """Tests for loading auth config from files and environment."""

    def test_secret_key_from_env_var(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("auth:\n  enabled: true\n")
        with patch.dict(os.environ, {"WJS_AUTH_SECRET_KEY": "test-secret-key-12345"}):
            manager = ConfigManager(config_path=config_file)
            assert manager.config.auth.secret_key == "test-secret-key-12345"
            assert manager.config.auth.enabled is True
