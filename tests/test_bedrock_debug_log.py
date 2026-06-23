# ABOUTME: Tests that bedrock_client debug logging does not leak full request bodies.
# ABOUTME: Validates that test_connection() logs structure-only metadata, not prompt content.
"""
Tests for Issue #12: Bedrock debug log must not expose full request body.

The test_connection() method logs diagnostic info at DEBUG level.
It must log only structural metadata (key names, message count),
never the full request body content which could contain journal entries.
"""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch
from bedrock_client import BedrockClient
from config_manager import BedrockConfig


@pytest.fixture
def mock_bedrock_config():
    """Create a minimal BedrockConfig for testing."""
    return BedrockConfig(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        region="us-east-1",
    )


@pytest.fixture
def bedrock_client_with_mock(mock_bedrock_config, monkeypatch):
    """Create a BedrockClient with mocked boto3 client."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    with patch("bedrock_client.boto3.client") as mock_boto:
        client = BedrockClient(mock_bedrock_config)
        # Mock successful invoke_model response
        mock_response = {
            "body": MagicMock(
                read=MagicMock(return_value=json.dumps({
                    "content": [{"text": '{"test": "success"}'}]
                }).encode())
            )
        }
        client.client.invoke_model.return_value = mock_response
        yield client


class TestBedrockDebugLogSafety:
    """Verify debug logging does not leak request body content."""

    def test_debug_log_does_not_contain_full_request_body(self, bedrock_client_with_mock, caplog):
        """Debug output must not contain the full JSON-dumped request body."""
        with caplog.at_level(logging.DEBUG):
            bedrock_client_with_mock.test_connection()

        debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
        for msg in debug_messages:
            # The full request body would contain the prompt text
            assert '"role": "user"' not in msg, \
                f"Debug log contains request body content: {msg}"
            assert '"anthropic_version"' not in msg, \
                f"Debug log contains request body JSON: {msg}"

    def test_debug_log_does_not_contain_prompt_text(self, bedrock_client_with_mock, caplog):
        """Debug output must not contain the test prompt string."""
        with caplog.at_level(logging.DEBUG):
            bedrock_client_with_mock.test_connection()

        debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
        for msg in debug_messages:
            assert "Respond with valid JSON" not in msg, \
                f"Debug log contains prompt text: {msg}"

    def test_debug_log_contains_structural_metadata(self, bedrock_client_with_mock, caplog):
        """Debug output should contain structure-only metadata like key names."""
        with caplog.at_level(logging.DEBUG):
            bedrock_client_with_mock.test_connection()

        debug_messages = " ".join(r.message for r in caplog.records if r.levelno == logging.DEBUG)
        # Should log some structural info about the request
        assert "request" in debug_messages.lower() or "body" in debug_messages.lower(), \
            "Expected some request structure logging at DEBUG level"
