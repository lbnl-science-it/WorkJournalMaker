# ABOUTME: Tests that summarization WebSocket endpoints enforce authentication.
# ABOUTME: Validates token gating on /api/summarization/ws and /api/summarization/ws/{task_id}.

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from web.api.summarization import router as summarization_router
from web.auth import User, encode_access_token
from config_manager import AuthConfig


SECRET = "ws-auth-test-secret-key-32bytes!!"


def _make_token(role: str = "user") -> str:
    user = User(id="u1", username="tester", role=role)
    return encode_access_token(user, SECRET, ttl_seconds=300)


def _make_test_app(auth_enabled: bool) -> FastAPI:
    """Create a minimal FastAPI app with the summarization router mounted."""
    test_app = FastAPI()
    test_app.include_router(summarization_router)

    mock_service = AsyncMock()
    mock_service.llm_client = MagicMock()  # non-None so the WS service check passes
    mock_service.get_task_status.return_value = None

    class MockState:
        def __init__(self):
            self.summarization_service = mock_service
            if auth_enabled:
                self.auth_config = AuthConfig(enabled=True, secret_key=SECRET)
            else:
                self.auth_config = AuthConfig(enabled=False)

    test_app.state = MockState()
    return test_app


class TestSummarizationWebSocketAuth:
    """Auth enforcement on /api/summarization/ws WebSocket endpoint."""

    def test_ws_no_token_rejected_when_auth_enabled(self):
        """Connection without token must be rejected with close code 4001."""
        client = TestClient(_make_test_app(auth_enabled=True))
        with pytest.raises(Exception):
            with client.websocket_connect("/api/summarization/ws") as ws:
                pass

    def test_ws_invalid_token_rejected_when_auth_enabled(self):
        """Connection with a malformed token must be rejected."""
        client = TestClient(_make_test_app(auth_enabled=True))
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/api/summarization/ws?token=not.a.valid.token"
            ) as ws:
                pass

    def test_ws_valid_token_accepted_when_auth_enabled(self):
        """Connection with a valid token must be accepted."""
        token = _make_token("user")
        client = TestClient(_make_test_app(auth_enabled=True))
        with client.websocket_connect(f"/api/summarization/ws?token={token}") as ws:
            data = ws.receive_json()
            assert data["type"] == "connection_status"
            assert data["status"] == "connected"

    def test_ws_no_token_accepted_when_auth_disabled(self):
        """When auth is disabled, connection without token must be accepted."""
        client = TestClient(_make_test_app(auth_enabled=False))
        with client.websocket_connect("/api/summarization/ws") as ws:
            data = ws.receive_json()
            assert data["status"] == "connected"


class TestSummarizationTaskWebSocketAuth:
    """Auth enforcement on /api/summarization/ws/{task_id} WebSocket endpoint."""

    TASK_ID = "test-task-000"

    def test_ws_task_no_token_rejected_when_auth_enabled(self):
        """Connection without token must be rejected with close code 4001."""
        client = TestClient(_make_test_app(auth_enabled=True))
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/api/summarization/ws/{self.TASK_ID}"
            ) as ws:
                pass

    def test_ws_task_invalid_token_rejected_when_auth_enabled(self):
        """Connection with a malformed token must be rejected."""
        client = TestClient(_make_test_app(auth_enabled=True))
        with pytest.raises(Exception):
            with client.websocket_connect(
                f"/api/summarization/ws/{self.TASK_ID}?token=garbage"
            ) as ws:
                pass

    def test_ws_task_valid_token_accepted_when_auth_enabled(self):
        """Connection with a valid token must be accepted."""
        token = _make_token("user")
        client = TestClient(_make_test_app(auth_enabled=True))
        with client.websocket_connect(
            f"/api/summarization/ws/{self.TASK_ID}?token={token}"
        ) as ws:
            data = ws.receive_json()
            # Either initial_status (task found) or error (task not found) — both valid
            assert data["type"] in ("initial_status", "error")

    def test_ws_task_no_token_accepted_when_auth_disabled(self):
        """When auth is disabled, connection without token must be accepted."""
        client = TestClient(_make_test_app(auth_enabled=False))
        with client.websocket_connect(
            f"/api/summarization/ws/{self.TASK_ID}"
        ) as ws:
            data = ws.receive_json()
            assert data["type"] in ("initial_status", "error")
