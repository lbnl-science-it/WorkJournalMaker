# ABOUTME: Integration tests for the /api/auth endpoints.
# ABOUTME: Tests login, refresh, logout, and profile using TestClient.

import asyncio
import time
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

        # Sleep 1 second so the new access token has a different iat/exp
        time.sleep(1)

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
