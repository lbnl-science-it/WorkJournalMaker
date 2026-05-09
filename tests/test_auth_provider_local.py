# ABOUTME: Tests for the local username/password authentication provider.
# ABOUTME: Validates password hashing, token issuance, refresh, and revocation.

import asyncio
import uuid
import pytest
from datetime import datetime, timedelta, timezone

from web.database import DatabaseManager, UserAccount
from web.providers.local import LocalAuthProvider
from web.auth import User, TokenPair, decode_access_token
from config_manager import AuthConfig


class TestLocalAuthProvider:
    """Tests for LocalAuthProvider."""

    SECRET = "test-secret-for-local-provider"

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_local_auth.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    @pytest.fixture
    def config(self):
        return AuthConfig(
            enabled=True,
            secret_key=self.SECRET,
            access_token_ttl=300,
            refresh_token_ttl=86400,
        )

    @pytest.fixture
    def provider(self, db, config):
        return LocalAuthProvider(db, config)

    @pytest.fixture
    def seeded_user(self, provider):
        """Create a test user via the provider's hash utility."""
        import bcrypt

        async def _seed(db):
            pw_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode()
            user_id = str(uuid.uuid4())
            async with db.get_session() as session:
                session.add(UserAccount(
                    id=user_id,
                    username="testuser",
                    password_hash=pw_hash,
                    role="user",
                ))
                await session.commit()
            return user_id

        loop = asyncio.new_event_loop()
        user_id = loop.run_until_complete(_seed(provider.db))
        loop.close()
        return user_id

    def test_authenticate_success(self, provider, seeded_user):
        async def _test():
            pair = await provider.authenticate({
                "username": "testuser",
                "password": "correct-password",
            })
            assert isinstance(pair, TokenPair)
            assert pair.access_token
            assert pair.refresh_token
            payload = decode_access_token(pair.access_token, self.SECRET)
            assert payload["username"] == "testuser"
            assert payload["role"] == "user"

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_authenticate_wrong_password(self, provider, seeded_user):
        async def _test():
            with pytest.raises(Exception):
                await provider.authenticate({
                    "username": "testuser",
                    "password": "wrong-password",
                })

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_authenticate_unknown_user(self, provider):
        async def _test():
            with pytest.raises(Exception):
                await provider.authenticate({
                    "username": "nonexistent",
                    "password": "anything",
                })

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_authenticate_inactive_user(self, provider, db):
        import bcrypt

        async def _test():
            pw_hash = bcrypt.hashpw(b"pass", bcrypt.gensalt()).decode()
            async with db.get_session() as session:
                session.add(UserAccount(
                    id=str(uuid.uuid4()),
                    username="inactive",
                    password_hash=pw_hash,
                    role="user",
                    is_active=False,
                ))
                await session.commit()

            with pytest.raises(Exception):
                await provider.authenticate({
                    "username": "inactive",
                    "password": "pass",
                })

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_validate_token(self, provider, seeded_user):
        async def _test():
            pair = await provider.authenticate({
                "username": "testuser",
                "password": "correct-password",
            })
            user = await provider.validate_token(pair.access_token)
            assert user.username == "testuser"

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_refresh_token_success(self, provider, seeded_user):
        async def _test():
            import asyncio as _asyncio
            pair = await provider.authenticate({
                "username": "testuser",
                "password": "correct-password",
            })
            # Wait 1 second so the new token's iat differs (PyJWT uses integer seconds).
            await _asyncio.sleep(1)
            new_pair = await provider.refresh_token(pair.refresh_token)
            assert isinstance(new_pair, TokenPair)
            assert new_pair.access_token != pair.access_token

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_revoke_token(self, provider, seeded_user):
        async def _test():
            pair = await provider.authenticate({
                "username": "testuser",
                "password": "correct-password",
            })
            await provider.revoke_token(pair.refresh_token)
            with pytest.raises(Exception):
                await provider.refresh_token(pair.refresh_token)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()
