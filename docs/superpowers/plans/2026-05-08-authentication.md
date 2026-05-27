# Authentication System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pluggable authentication to all web API endpoints, closing issue #87 (unauthenticated access to destructive operations).

**Architecture:** FastAPI dependency injection with a `Protocol`-based auth provider. Local username/password provider first (bcrypt + JWT). Auth-optional mode via config toggle preserves backward compatibility. Two roles: `user` and `admin`.

**Tech Stack:** PyJWT, bcrypt, SQLAlchemy (async, existing), FastAPI dependency injection

**Spec:** `docs/superpowers/specs/2026-05-08-authentication-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| **Create:** `web/auth.py` | `AuthProvider` protocol, `User`/`TokenPair` dataclasses, JWT encode/decode, FastAPI dependencies (`get_current_user`, `require_admin`) |
| **Create:** `web/providers/__init__.py` | Package init |
| **Create:** `web/providers/local.py` | Local auth provider: bcrypt password verify, JWT token issue, refresh token management |
| **Create:** `web/api/auth.py` | Auth API router: `/api/auth/login`, `/refresh`, `/logout`, `/me` |
| **Create:** `web/manage.py` | CLI tool for `create-admin` and `list-users` |
| **Create:** `tests/test_auth.py` | Unit tests for JWT utilities, dependencies, auth-disabled mode |
| **Create:** `tests/test_auth_provider_local.py` | Unit tests for local provider: authenticate, validate, refresh |
| **Create:** `tests/test_auth_api.py` | Integration tests for auth endpoints |
| **Create:** `tests/test_auth_protected.py` | Tests that existing endpoints enforce auth correctly |
| **Create:** `tests/test_manage.py` | Tests for CLI management tool |
| **Modify:** `web/database.py` | Add `UserAccount` and `RefreshToken` ORM models, add `user_id` column to `JournalEntryIndex` |
| **Modify:** `config_manager.py` | Add `AuthConfig` dataclass, wire into `AppConfig` |
| **Modify:** `web/app.py` | Register auth router, initialize auth provider on startup |
| **Modify:** `web/api/entries.py` | Add `get_current_user` dependency, filter entries by `user_id` |
| **Modify:** `web/api/settings.py` | Add `require_admin` dependency to destructive endpoints |
| **Modify:** `web/api/sync.py` | Add `require_admin` dependency to scheduler control endpoints |
| **Modify:** `web/api/health.py` | Add `require_admin` to `/config` and `/metrics`, leave `/` public |
| **Modify:** `requirements.txt` | Add `PyJWT` and `bcrypt` |
| **Modify:** `tests/conftest.py` | Add `auth_disabled_client` and `authenticated_client` fixtures |

---

## Task 1: Add Dependencies ✅ DONE

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add PyJWT and bcrypt to requirements**

```
# At the end of requirements.txt, add:
# Authentication
PyJWT>=2.8.0
bcrypt>=4.0.0
```

- [ ] **Step 2: Install dependencies**

Run: `pyenv activate WorkJournal && pip install PyJWT>=2.8.0 bcrypt>=4.0.0`
Expected: Both packages install successfully

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat(auth): add PyJWT and bcrypt dependencies for #87"
```

---

## Task 2: Add AuthConfig to Configuration ✅ DONE

**Files:**
- Modify: `config_manager.py:117-124` (AppConfig dataclass)
- Test: `tests/test_auth.py` (new)

- [ ] **Step 1: Write failing test for AuthConfig defaults**

Create `tests/test_auth.py`:

```python
# ABOUTME: Unit tests for auth configuration, JWT utilities, and FastAPI dependencies.
# ABOUTME: Validates auth-disabled mode, token lifecycle, and role-based access control.

import pytest
from config_manager import AppConfig, AuthConfig


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestAuthConfig -v`
Expected: FAIL — `ImportError: cannot import name 'AuthConfig'`

- [ ] **Step 3: Implement AuthConfig**

In `config_manager.py`, add the dataclass before `AppConfig` (after `ProcessingConfig` around line 114):

```python
@dataclass
class AuthConfig:
    """Configuration for authentication and authorization."""
    enabled: bool = False
    provider: str = "local"
    secret_key: str = ""
    access_token_ttl: int = 1800
    refresh_token_ttl: int = 604800
```

Add `auth` field to `AppConfig`:

```python
@dataclass
class AppConfig:
    """Complete application configuration."""
    bedrock: BedrockConfig = field(default_factory=BedrockConfig)
    google_genai: GoogleGenAIConfig = field(default_factory=GoogleGenAIConfig)
    cborg: CBORGConfig = field(default_factory=CBORGConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LogConfig = field(default_factory=LogConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestAuthConfig -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Add config-file loading for auth section**

In `ConfigManager._load_config()` (around line 186), the method calls `_build_config_from_dict`. Add auth parsing in the `_build_config_from_dict` method. Find where the other configs are built (look for `bedrock_dict`, `google_genai_dict`, etc.) and add:

```python
auth_dict = config_dict.get('auth', {})
config.auth = AuthConfig(
    enabled=auth_dict.get('enabled', AuthConfig.enabled),
    provider=auth_dict.get('provider', AuthConfig.provider),
    secret_key=auth_dict.get('secret_key', AuthConfig.secret_key),
    access_token_ttl=auth_dict.get('access_token_ttl', AuthConfig.access_token_ttl),
    refresh_token_ttl=auth_dict.get('refresh_token_ttl', AuthConfig.refresh_token_ttl),
)
```

- [ ] **Step 6: Add environment variable override for secret key**

In `ConfigManager._apply_env_overrides()`, add:

```python
auth_secret = os.getenv('WJM_AUTH_SECRET_KEY')
if auth_secret:
    config.auth.secret_key = auth_secret
```

- [ ] **Step 7: Write and run test for env var override**

Add to `tests/test_auth.py`:

```python
import os
from unittest.mock import patch
from config_manager import ConfigManager


class TestAuthConfigLoading:
    """Tests for loading auth config from files and environment."""

    def test_secret_key_from_env_var(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("auth:\n  enabled: true\n")
        with patch.dict(os.environ, {"WJM_AUTH_SECRET_KEY": "test-secret-key-12345"}):
            manager = ConfigManager(config_path=config_file)
            assert manager.config.auth.secret_key == "test-secret-key-12345"
            assert manager.config.auth.enabled is True
```

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py -v`
Expected: PASS (all tests)

- [ ] **Step 8: Commit**

```bash
git add config_manager.py tests/test_auth.py
git commit -m "feat(auth): add AuthConfig dataclass with env var override for #87"
```

---

## Task 3: Add Database Models (UserAccount, RefreshToken) ✅ DONE

**Files:**
- Modify: `web/database.py:27-108` (add models after existing ones)
- Test: `tests/test_auth.py` (extend)

- [ ] **Step 1: Write failing test for UserAccount model**

Add to `tests/test_auth.py`:

```python
import asyncio
from web.database import DatabaseManager, UserAccount, RefreshToken


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestAuthDatabaseModels -v`
Expected: FAIL — `ImportError: cannot import name 'UserAccount'`

- [ ] **Step 3: Implement UserAccount and RefreshToken models**

In `web/database.py`, add these models after the `SyncStatus` class (around line 101), before the Index definitions:

```python
class UserAccount(Base):
    """User account for authentication (local provider)."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=now_utc)
    modified_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class RefreshToken(Base):
    """Revocable refresh token (stores hash, not raw token)."""
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=now_utc)
```

Add indexes with the existing index definitions:

```python
Index('idx_users_username', UserAccount.username)
Index('idx_refresh_tokens_user', RefreshToken.user_id)
Index('idx_refresh_tokens_hash', RefreshToken.token_hash)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestAuthDatabaseModels -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add web/database.py tests/test_auth.py
git commit -m "feat(auth): add UserAccount and RefreshToken database models for #87"
```

---

## Task 4: Implement JWT Utilities and Core Auth Types ✅ DONE

**Files:**
- Create: `web/auth.py`
- Test: `tests/test_auth.py` (extend)

- [ ] **Step 1: Write failing tests for User and TokenPair dataclasses**

Add to `tests/test_auth.py`:

```python
from web.auth import User, TokenPair


class TestAuthTypes:
    """Tests for User and TokenPair dataclasses."""

    def test_user_creation(self):
        user = User(id="u1", username="alice", role="user")
        assert user.id == "u1"
        assert user.username == "alice"
        assert user.role == "user"

    def test_token_pair_creation(self):
        pair = TokenPair(access_token="acc", refresh_token="ref")
        assert pair.access_token == "acc"
        assert pair.refresh_token == "ref"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestAuthTypes -v`
Expected: FAIL — `ImportError: cannot import name 'User' from 'web.auth'`

- [ ] **Step 3: Write failing tests for JWT encode/decode**

Add to `tests/test_auth.py`:

```python
from web.auth import encode_access_token, decode_access_token
from datetime import datetime, timezone


class TestJWTUtilities:
    """Tests for JWT token encoding and decoding."""

    SECRET = "test-secret-key-for-jwt-testing"

    def test_encode_decode_roundtrip(self):
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        decoded = decode_access_token(token, self.SECRET)
        assert decoded["user_id"] == "u1"
        assert decoded["username"] == "alice"
        assert decoded["role"] == "user"
        assert "exp" in decoded

    def test_decode_expired_token_raises(self):
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=-1)
        with pytest.raises(Exception):
            decode_access_token(token, self.SECRET)

    def test_decode_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_access_token("not.a.valid.token", self.SECRET)

    def test_decode_wrong_secret_raises(self):
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        with pytest.raises(Exception):
            decode_access_token(token, "wrong-secret")
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestJWTUtilities -v`
Expected: FAIL — `ImportError`

- [ ] **Step 5: Implement web/auth.py with types and JWT utilities**

Create `web/auth.py`:

```python
# ABOUTME: Authentication protocol, user model, JWT utilities, and FastAPI dependencies.
# ABOUTME: Provides the pluggable auth provider interface and token validation.

from dataclasses import dataclass
from typing import Protocol, Optional
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestAuthTypes tests/test_auth.py::TestJWTUtilities -v`
Expected: PASS (6 tests)

- [ ] **Step 7: Commit**

```bash
git add web/auth.py tests/test_auth.py
git commit -m "feat(auth): add User/TokenPair types, JWT encode/decode, AuthProvider protocol for #87"
```

---

## Task 5: Implement FastAPI Auth Dependencies ✅ DONE

**Files:**
- Modify: `web/auth.py`
- Test: `tests/test_auth.py` (extend)

- [ ] **Step 1: Write failing tests for get_current_user dependency**

Add to `tests/test_auth.py`:

```python
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from web.auth import get_current_user, require_admin, User, encode_access_token
from config_manager import AuthConfig


class TestGetCurrentUser:
    """Tests for the get_current_user FastAPI dependency."""

    SECRET = "test-secret-key-for-dependency-testing"

    def _make_config(self, enabled=True):
        return AuthConfig(enabled=enabled, secret_key=self.SECRET)

    def _make_request(self, token=None):
        request = MagicMock()
        request.app.state.auth_config = self._make_config(enabled=True)
        request.app.state.auth_provider = None
        if token:
            request.headers = {"authorization": f"Bearer {token}"}
        else:
            request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        user = User(id="u1", username="alice", role="user")
        token = encode_access_token(user, self.SECRET, ttl_seconds=300)
        request = self._make_request(token)
        result = await get_current_user(request)
        assert result.id == "u1"
        assert result.username == "alice"

    @pytest.mark.asyncio
    async def test_missing_header_raises_401(self):
        request = self._make_request(token=None)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        request = self._make_request(token="garbage.token.here")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_disabled_returns_default_admin(self):
        request = MagicMock()
        request.app.state.auth_config = self._make_config(enabled=False)
        result = await get_current_user(request)
        assert result.id == "default"
        assert result.role == "admin"


class TestRequireAdmin:
    """Tests for the require_admin FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        user = User(id="u1", username="admin", role="admin")
        result = await require_admin(user)
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        user = User(id="u2", username="viewer", role="user")
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user)
        assert exc_info.value.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestGetCurrentUser tests/test_auth.py::TestRequireAdmin -v`
Expected: FAIL — `ImportError: cannot import name 'get_current_user'`

- [ ] **Step 3: Implement get_current_user and require_admin**

Add to the bottom of `web/auth.py`:

```python
from fastapi import Request, Depends, HTTPException, status


_DEFAULT_USER = User(id="default", username="default", role="admin")


async def get_current_user(request: Request) -> User:
    """FastAPI dependency: extract and validate the Bearer token, return User."""
    auth_config = request.app.state.auth_config

    if not auth_config.enabled:
        return _DEFAULT_USER

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

    return User(
        id=payload["user_id"],
        username=payload["username"],
        role=payload["role"],
    )


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: require the current user to be an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestGetCurrentUser tests/test_auth.py::TestRequireAdmin -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add web/auth.py tests/test_auth.py
git commit -m "feat(auth): add get_current_user and require_admin FastAPI dependencies for #87"
```

---

## Task 6: Implement Local Auth Provider

**Files:**
- Create: `web/providers/__init__.py`
- Create: `web/providers/local.py`
- Test: `tests/test_auth_provider_local.py` (new)

- [ ] **Step 1: Create providers package**

Create `web/providers/__init__.py`:

```python
# ABOUTME: Authentication provider package.
# ABOUTME: Contains pluggable provider implementations (local, future SSO).
```

- [ ] **Step 2: Write failing tests for local provider**

Create `tests/test_auth_provider_local.py`:

```python
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
            pair = await provider.authenticate({
                "username": "testuser",
                "password": "correct-password",
            })
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_provider_local.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'web.providers.local'`

- [ ] **Step 4: Implement LocalAuthProvider**

Create `web/providers/local.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_provider_local.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add web/providers/__init__.py web/providers/local.py tests/test_auth_provider_local.py
git commit -m "feat(auth): implement LocalAuthProvider with bcrypt and refresh tokens for #87"
```

---

## Task 7: Implement Auth API Endpoints

**Files:**
- Create: `web/api/auth.py`
- Test: `tests/test_auth_api.py` (new)
- Modify: `web/app.py` (register router, initialize provider on startup)

- [ ] **Step 1: Write failing integration tests for auth endpoints**

Create `tests/test_auth_api.py`:

```python
# ABOUTME: Integration tests for the /api/auth endpoints.
# ABOUTME: Tests login, refresh, logout, and profile using TestClient.

import asyncio
import uuid
import pytest
import bcrypt
from fastapi.testclient import TestClient

from web.app import app
from web.database import DatabaseManager, UserAccount
from config_manager import AuthConfig


@pytest.fixture
def auth_client(tmp_path):
    """TestClient with auth enabled and a seeded admin user."""
    secret = "integration-test-secret-key"

    with TestClient(app) as client:
        # Set up auth config on app state
        auth_config = AuthConfig(enabled=True, secret_key=secret)
        app.state.auth_config = auth_config

        # Set up temp DB
        db = DatabaseManager(str(tmp_path / "test_auth_api.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())

        # Seed an admin user
        pw_hash = bcrypt.hashpw(b"admin-pass", bcrypt.gensalt()).decode()
        user_id = str(uuid.uuid4())

        async def _seed():
            async with db.get_session() as session:
                session.add(UserAccount(
                    id=user_id,
                    username="admin",
                    password_hash=pw_hash,
                    role="admin",
                ))
                await session.commit()

        loop.run_until_complete(_seed())

        # Initialize the local provider
        from web.providers.local import LocalAuthProvider
        provider = LocalAuthProvider(db, auth_config)
        app.state.auth_provider = provider

        yield client

        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()


class TestAuthLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, auth_client):
        resp = auth_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin-pass",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_login_wrong_password(self, auth_client):
        resp = auth_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_unknown_user(self, auth_client):
        resp = auth_client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "anything",
        })
        assert resp.status_code == 401


class TestAuthRefresh:
    """Tests for POST /api/auth/refresh."""

    def test_refresh_success(self, auth_client):
        login = auth_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin-pass",
        })
        refresh_token = login.json()["refresh_token"]

        resp = auth_client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["access_token"] != login.json()["access_token"]

    def test_refresh_invalid_token(self, auth_client):
        resp = auth_client.post("/api/auth/refresh", json={
            "refresh_token": "not-a-real-token",
        })
        assert resp.status_code == 401


class TestAuthLogout:
    """Tests for POST /api/auth/logout."""

    def test_logout_revokes_refresh_token(self, auth_client):
        login = auth_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin-pass",
        })
        tokens = login.json()
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]

        resp = auth_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp.status_code == 200

        # Refresh token should now be invalid
        resp = auth_client.post("/api/auth/refresh", json={
            "refresh_token": refresh,
        })
        assert resp.status_code == 401


class TestAuthMe:
    """Tests for GET /api/auth/me."""

    def test_me_returns_profile(self, auth_client):
        login = auth_client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin-pass",
        })
        access = login.json()["access_token"]

        resp = auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "admin"
        assert body["role"] == "admin"

    def test_me_without_token_returns_401(self, auth_client):
        resp = auth_client.get("/api/auth/me")
        assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_api.py -v`
Expected: FAIL — router not registered / 404

- [ ] **Step 3: Implement auth API router**

Create `web/api/auth.py`:

```python
# ABOUTME: REST API endpoints for authentication (login, refresh, logout, profile).
# ABOUTME: Delegates to the active AuthProvider via app.state.

from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel

from web.auth import get_current_user, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserProfile(BaseModel):
    id: str
    username: str
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    """Authenticate with username/password and receive a token pair."""
    provider = request.app.state.auth_provider
    try:
        pair = await provider.authenticate({
            "username": body.username,
            "password": body.password,
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request):
    """Exchange a refresh token for a new token pair."""
    provider = request.app.state.auth_provider
    try:
        pair = await provider.refresh_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Revoke a refresh token (logout)."""
    provider = request.app.state.auth_provider
    await provider.revoke_token(body.refresh_token)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserProfile)
async def me(user: User = Depends(get_current_user)):
    """Return the current user's profile."""
    return UserProfile(id=user.id, username=user.username, role=user.role)
```

- [ ] **Step 4: Wire auth into app startup**

In `web/app.py`, add imports at the top:

```python
from web.auth import get_current_user, require_admin
from web.api import auth as auth_api
from web.providers.local import LocalAuthProvider
from config_manager import AuthConfig
```

In the `startup()` method of `WorkJournalWebApp`, after config is loaded (around line 64, after `self.config = config_manager.get_config()`), add:

```python
# Initialize auth
auth_config = self.config.auth
if auth_config.enabled and not auth_config.secret_key:
    raise RuntimeError(
        "auth.enabled is true but no secret_key configured. "
        "Set WJM_AUTH_SECRET_KEY environment variable."
    )
```

In the `lifespan()` function, after setting `app.state.scheduler`, add:

```python
app.state.auth_config = web_app.config.auth
if web_app.config.auth.enabled:
    app.state.auth_provider = LocalAuthProvider(web_app.db_manager, web_app.config.auth)
else:
    app.state.auth_provider = None
```

Register the router with the existing routers:

```python
app.include_router(auth_api.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_api.py -v`
Expected: PASS (8 tests)

- [ ] **Step 6: Run all existing tests to check for regressions**

Run: `pyenv activate WorkJournal && python -m pytest tests/ -v --timeout=30 2>&1 | tail -30`
Expected: All previously passing tests still pass

- [ ] **Step 7: Commit**

```bash
git add web/api/auth.py web/app.py tests/test_auth_api.py
git commit -m "feat(auth): add auth API endpoints and wire provider into app startup for #87"
```

---

## Task 8: Protect Existing Endpoints

**Files:**
- Modify: `web/api/entries.py`
- Modify: `web/api/settings.py`
- Modify: `web/api/sync.py`
- Modify: `web/api/health.py`
- Test: `tests/test_auth_protected.py` (new)
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add test fixtures for auth in conftest**

Add to `tests/conftest.py`:

```python
from config_manager import AuthConfig
from web.auth import User, encode_access_token


@pytest.fixture
def auth_disabled_client(isolated_app_client):
    """Client with auth disabled (existing behavior)."""
    app.state.auth_config = AuthConfig(enabled=False)
    app.state.auth_provider = None
    yield isolated_app_client


def _make_auth_header(role="user", secret="test-secret"):
    """Helper: create a Bearer token header for the given role."""
    user = User(id="test-user-id", username="testuser", role=role)
    token = encode_access_token(user, secret, ttl_seconds=300)
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 2: Write failing tests for protected endpoints**

Create `tests/test_auth_protected.py`:

```python
# ABOUTME: Tests that existing endpoints enforce authentication correctly.
# ABOUTME: Validates 401 without token, 200 with token, and 403 for admin-only routes.

import asyncio
import pytest
from fastapi.testclient import TestClient

from web.app import app
from web.database import DatabaseManager
from config_manager import AuthConfig
from web.auth import User, encode_access_token


SECRET = "protected-endpoint-test-secret"


@pytest.fixture
def protected_client(tmp_path):
    """TestClient with auth ENABLED."""
    with TestClient(app) as client:
        auth_config = AuthConfig(enabled=True, secret_key=SECRET)
        app.state.auth_config = auth_config
        app.state.auth_provider = None

        # Swap to temp DB
        db = DatabaseManager(str(tmp_path / "test_protected.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())

        orig_db = app.state.db_manager
        app.state.db_manager = db
        for name, svc in app.state._state.items():
            if name != "db_manager" and hasattr(svc, "db_manager"):
                svc.db_manager = db

        yield client

        app.state.db_manager = orig_db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()


def _token(role="user"):
    user = User(id="u1", username="tester", role=role)
    return encode_access_token(user, SECRET, ttl_seconds=300)


class TestEntriesAuth:
    """Entries endpoints require user-level auth."""

    def test_list_entries_no_token_401(self, protected_client):
        resp = protected_client.get("/api/entries/")
        assert resp.status_code == 401

    def test_list_entries_with_token_200(self, protected_client):
        resp = protected_client.get(
            "/api/entries/",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200


class TestSettingsAuth:
    """Settings reset requires admin auth."""

    def test_reset_all_no_token_401(self, protected_client):
        resp = protected_client.post("/api/settings/reset-all")
        assert resp.status_code == 401

    def test_reset_all_user_role_403(self, protected_client):
        resp = protected_client.post(
            "/api/settings/reset-all",
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403

    def test_reset_all_admin_role_allowed(self, protected_client):
        resp = protected_client.post(
            "/api/settings/reset-all",
            headers={"Authorization": f"Bearer {_token('admin')}"},
        )
        # Should not be 401 or 403
        assert resp.status_code not in (401, 403)


class TestSyncAuth:
    """Sync scheduler endpoints require admin auth."""

    def test_full_sync_no_token_401(self, protected_client):
        resp = protected_client.post("/api/sync/full")
        assert resp.status_code == 401

    def test_full_sync_user_role_403(self, protected_client):
        resp = protected_client.post(
            "/api/sync/full",
            headers={"Authorization": f"Bearer {_token('user')}"},
        )
        assert resp.status_code == 403


class TestAuthDisabled:
    """When auth is disabled, all endpoints work without tokens."""

    def test_entries_accessible(self, isolated_app_client):
        app.state.auth_config = AuthConfig(enabled=False)
        resp = isolated_app_client.get("/api/entries/")
        assert resp.status_code == 200

    def test_settings_accessible(self, isolated_app_client):
        app.state.auth_config = AuthConfig(enabled=False)
        resp = isolated_app_client.get("/api/settings/")
        assert resp.status_code == 200
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_protected.py -v`
Expected: FAIL — endpoints return 200 without tokens (not yet protected)

- [ ] **Step 4: Add auth dependency to entries.py**

In `web/api/entries.py`, add import:

```python
from web.auth import get_current_user, User
from fastapi import Depends
```

Add `user: User = Depends(get_current_user)` parameter to each endpoint function. For example, `list_entries` becomes:

```python
@router.get("/", response_model=RecentEntriesResponse)
async def list_entries(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    has_content: Optional[bool] = Query(None, description="Filter by content presence"),
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("date", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    entry_manager: EntryManager = Depends(get_entry_manager),
    user: User = Depends(get_current_user),
):
```

Repeat for all endpoints in entries.py. The `user` parameter does not need to be used in the function body yet — the dependency itself enforces the check.

- [ ] **Step 5: Add admin dependency to settings.py destructive endpoints**

In `web/api/settings.py`, add import:

```python
from web.auth import get_current_user, require_admin, User
```

Add `user: User = Depends(get_current_user)` to read endpoints (GET).

Add `user: User = Depends(require_admin)` to destructive endpoints: `reset_all_settings`, `import_settings`, and any PUT/DELETE.

- [ ] **Step 6: Add admin dependency to sync.py**

In `web/api/sync.py`, add import:

```python
from web.auth import require_admin, User
```

Add `user: User = Depends(require_admin)` to: `full_sync`, `scheduler_stop`, `scheduler_config` (PUT), and any other state-changing endpoints.

- [ ] **Step 7: Add admin dependency to health.py selective endpoints**

In `web/api/health.py`, add import:

```python
from web.auth import get_current_user, require_admin, User
```

Leave `GET /api/health/` public (no dependency). Add `user: User = Depends(require_admin)` to `/config` and `/metrics`.

- [ ] **Step 8: Update conftest.py with auth_config default**

In `tests/conftest.py`, inside the `isolated_app_client` fixture, after setting up the temp database and before `yield client`, add:

```python
app.state.auth_config = AuthConfig(enabled=False)
app.state.auth_provider = None
```

Add imports at top:

```python
from config_manager import AuthConfig
```

This ensures all existing tests continue to work with auth disabled.

- [ ] **Step 9: Run protected endpoint tests**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_protected.py -v`
Expected: PASS (all tests)

- [ ] **Step 10: Run all tests to verify no regressions**

Run: `pyenv activate WorkJournal && python -m pytest tests/ -v --timeout=30 2>&1 | tail -40`
Expected: All previously passing tests still pass

- [ ] **Step 11: Commit**

```bash
git add web/api/entries.py web/api/settings.py web/api/sync.py web/api/health.py tests/conftest.py tests/test_auth_protected.py
git commit -m "feat(auth): protect all API endpoints with auth dependencies for #87"
```

---

## Task 9: Implement CLI Management Tool

**Files:**
- Create: `web/manage.py`
- Test: `tests/test_manage.py` (new)

- [ ] **Step 1: Write failing tests for manage.py**

Create `tests/test_manage.py`:

```python
# ABOUTME: Tests for the CLI user management tool (create-admin, list-users).
# ABOUTME: Validates user creation with proper password hashing and role assignment.

import asyncio
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

from web.database import DatabaseManager, UserAccount
from web.manage import create_admin, list_users


class TestCreateAdmin:
    """Tests for the create-admin CLI command."""

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_manage.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    def test_create_admin_user(self, db):
        import bcrypt
        from sqlalchemy import select

        async def _test():
            await create_admin(db, "myadmin", "securepass123")

            async with db.get_session() as session:
                stmt = select(UserAccount).where(UserAccount.username == "myadmin")
                result = await session.execute(stmt)
                user = result.scalar_one()
                assert user.role == "admin"
                assert user.is_active is True
                assert bcrypt.checkpw(b"securepass123", user.password_hash.encode())

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_create_duplicate_username_raises(self, db):
        async def _test():
            await create_admin(db, "dup", "pass1")
            with pytest.raises(Exception):
                await create_admin(db, "dup", "pass2")

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()


class TestListUsers:
    """Tests for the list-users CLI command."""

    @pytest.fixture
    def db(self, tmp_path):
        db = DatabaseManager(str(tmp_path / "test_manage_list.db"))
        loop = asyncio.new_event_loop()
        loop.run_until_complete(db.initialize())
        yield db
        if db.engine:
            loop.run_until_complete(db.engine.dispose())
        loop.close()

    def test_list_empty(self, db):
        async def _test():
            users = await list_users(db)
            assert users == []

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()

    def test_list_after_create(self, db):
        async def _test():
            await create_admin(db, "admin1", "pass")
            users = await list_users(db)
            assert len(users) == 1
            assert users[0]["username"] == "admin1"
            assert users[0]["role"] == "admin"
            assert "password_hash" not in users[0]

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_test())
        loop.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_manage.py -v`
Expected: FAIL — `ImportError: cannot import name 'create_admin' from 'web.manage'`

- [ ] **Step 3: Implement web/manage.py**

Create `web/manage.py`:

```python
# ABOUTME: CLI tool for user account management (create-admin, list-users).
# ABOUTME: Bootstraps the first admin user without requiring API authentication.

import argparse
import asyncio
import getpass
import sys
import uuid

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from web.database import DatabaseManager, UserAccount


async def create_admin(db: DatabaseManager, username: str, password: str) -> str:
    """Create an admin user account. Returns the new user's ID."""
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())

    async with db.get_session() as session:
        stmt = select(UserAccount).where(UserAccount.username == username)
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ValueError(f"Username '{username}' already exists")

        session.add(UserAccount(
            id=user_id,
            username=username,
            password_hash=pw_hash,
            role="admin",
            is_active=True,
        ))
        await session.commit()

    return user_id


async def list_users(db: DatabaseManager) -> list:
    """List all user accounts (without password hashes)."""
    async with db.get_session() as session:
        stmt = select(UserAccount).order_by(UserAccount.created_at)
        result = await session.execute(stmt)
        accounts = result.scalars().all()

    return [
        {
            "id": a.id,
            "username": a.username,
            "role": a.role,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in accounts
    ]


async def _main(args: argparse.Namespace) -> None:
    db = DatabaseManager()
    await db.initialize()

    if args.command == "create-admin":
        password = args.password or getpass.getpass("Password: ")
        user_id = await create_admin(db, args.username, password)
        print(f"Admin user '{args.username}' created (id: {user_id})")

    elif args.command == "list-users":
        users = await list_users(db)
        if not users:
            print("No users found.")
        else:
            for u in users:
                status = "active" if u["is_active"] else "disabled"
                print(f"  {u['username']}  role={u['role']}  {status}  id={u['id']}")

    if db.engine:
        await db.engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Work Journal Maker user management")
    sub = parser.add_subparsers(dest="command", required=True)

    create_parser = sub.add_parser("create-admin", help="Create an admin user")
    create_parser.add_argument("--username", required=True)
    create_parser.add_argument("--password", default=None, help="Password (prompted if omitted)")

    sub.add_parser("list-users", help="List all users")

    args = parser.parse_args()
    asyncio.run(_main(args))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_manage.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add web/manage.py tests/test_manage.py
git commit -m "feat(auth): add CLI management tool for user creation for #87"
```

---

## Task 10: Add user_id Column to JournalEntryIndex

**Files:**
- Modify: `web/database.py:34-56` (JournalEntryIndex model)
- Test: `tests/test_auth.py` (extend)

- [ ] **Step 1: Write failing test for user_id column**

Add to `tests/test_auth.py`:

```python
from web.database import JournalEntryIndex
from datetime import date


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestJournalEntryUserScoping -v`
Expected: FAIL — `AttributeError: type object 'JournalEntryIndex' has no attribute 'user_id'`

- [ ] **Step 3: Add user_id column to JournalEntryIndex**

In `web/database.py`, add to the `JournalEntryIndex` model (after `has_content`):

```python
    # User scoping for multi-user deployments
    user_id = Column(String, nullable=False, default="default", index=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py::TestJournalEntryUserScoping -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run full test suite for regressions**

Run: `pyenv activate WorkJournal && python -m pytest tests/ -v --timeout=30 2>&1 | tail -30`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add web/database.py tests/test_auth.py
git commit -m "feat(auth): add user_id column to JournalEntryIndex for #87"
```

---

## Task 11: Add WebSocket Token Validation

**Files:**
- Modify: `web/app.py:267-290` (general WebSocket endpoint)
- Test: `tests/test_auth_protected.py` (extend)

- [ ] **Step 1: Write failing test for WebSocket auth**

Add to `tests/test_auth_protected.py`:

```python
from starlette.testclient import TestClient as StarletteTestClient


class TestWebSocketAuth:
    """WebSocket connections require a valid token in the query string."""

    def test_ws_no_token_rejected(self, protected_client):
        with pytest.raises(Exception):
            with protected_client.websocket_connect("/ws") as ws:
                pass

    def test_ws_invalid_token_rejected(self, protected_client):
        with pytest.raises(Exception):
            with protected_client.websocket_connect("/ws?token=garbage") as ws:
                pass

    def test_ws_valid_token_accepted(self, protected_client):
        token = _token("user")
        with protected_client.websocket_connect(f"/ws?token={token}") as ws:
            data = ws.receive_json()
            assert data["type"] == "connection_status"
            assert data["status"] == "connected"

    def test_ws_auth_disabled_no_token_accepted(self, isolated_app_client):
        from web.app import app
        app.state.auth_config = AuthConfig(enabled=False)
        with isolated_app_client.websocket_connect("/ws") as ws:
            data = ws.receive_json()
            assert data["status"] == "connected"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_protected.py::TestWebSocketAuth -v`
Expected: FAIL — WebSocket accepts connections without token

- [ ] **Step 3: Add token validation to WebSocket endpoint**

In `web/app.py`, modify the `general_websocket_endpoint` function:

```python
from web.auth import decode_access_token

@app.websocket("/ws")
async def general_websocket_endpoint(websocket: WebSocket):
    """General WebSocket endpoint for system-wide updates."""
    auth_config = websocket.app.state.auth_config

    if auth_config.enabled:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        try:
            decode_access_token(token, auth_config.secret_key)
        except Exception:
            await websocket.close(code=4001, reason="Invalid token")
            return

    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "status": "connected",
            "message": "WebSocket connection established",
            "service": "general"
        }))

        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({
                "type": "connection_status",
                "status": "connected",
                "message": "WebSocket connection established"
            }))
    except WebSocketDisconnect:
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth_protected.py::TestWebSocketAuth -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add web/app.py tests/test_auth_protected.py
git commit -m "feat(auth): add WebSocket token validation via query parameter for #87"
```

---

> **Note — Per-user settings scoping:** The spec mentions user-scoped settings,
> but the current settings system (`WebSettings`) is global. Filtering settings
> by `user_id` requires changes to the settings service, settings API, and
> frontend. This is deferred to a follow-up task after the core auth system is
> stable. The `WorkWeekSettings` table already has a `user_id` column, so it
> is partially prepared.

---

## Task 12: Final Validation

**Files:** None (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `pyenv activate WorkJournal && python -m pytest tests/ -v --timeout=30`
Expected: All tests pass. No regressions.

- [ ] **Step 2: Verify all auth tests pass together**

Run: `pyenv activate WorkJournal && python -m pytest tests/test_auth.py tests/test_auth_provider_local.py tests/test_auth_api.py tests/test_auth_protected.py tests/test_manage.py -v`
Expected: All auth-related tests pass.

- [ ] **Step 3: Verify CLI management tool runs**

Run: `pyenv activate WorkJournal && python -m web.manage --help`
Expected: Shows help with `create-admin` and `list-users` subcommands.

- [ ] **Step 4: Review commit history**

```bash
git status
git log --oneline feature/87-authentication ^main
```

Review the commit history to verify all tasks are represented.
