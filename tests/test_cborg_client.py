#!/usr/bin/env python3
# ABOUTME: Tests for the CBORG LLM client (OpenAI-compatible API at cborg.lbl.gov).
# ABOUTME: Covers initialization, API calls, response parsing, error handling, and stats.
"""
Tests for CBORGClient — the CBORG LLM provider integration.

Tests mock the openai.OpenAI client to verify request formatting, response
parsing, retry logic, and statistics tracking without making real API calls.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

from config_manager import CBORGConfig
from llm_data_structures import AnalysisResult, APIStats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_config():
    """Provide a CBORGConfig with defaults."""
    return CBORGConfig()


@pytest.fixture
def custom_config():
    """Provide a CBORGConfig with custom values."""
    return CBORGConfig(
        endpoint="https://custom.cborg.example/v1",
        api_key_env="CUSTOM_CBORG_KEY",
        model="lbl/custom-model:latest",
        max_retries=5,
        rate_limit_delay=2.0,
        timeout=60,
    )


def _make_chat_completion(content_text: str):
    """Build a mock OpenAI ChatCompletion response object."""
    message = MagicMock()
    message.content = content_text

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------

class TestCBORGConfig:
    """Tests for CBORGConfig dataclass defaults and overrides."""

    def test_default_values(self, default_config):
        assert default_config.endpoint == "https://cborg.lbl.gov/v1"
        assert default_config.api_key_env == "CBORG_API_KEY"
        assert default_config.model == "lbl/cborg-chat:latest"
        assert default_config.max_retries == 3
        assert default_config.rate_limit_delay == 1.0
        assert default_config.timeout == 30

    def test_custom_values(self, custom_config):
        assert custom_config.endpoint == "https://custom.cborg.example/v1"
        assert custom_config.api_key_env == "CUSTOM_CBORG_KEY"
        assert custom_config.model == "lbl/custom-model:latest"
        assert custom_config.max_retries == 5
        assert custom_config.rate_limit_delay == 2.0
        assert custom_config.timeout == 60


# ---------------------------------------------------------------------------
# Client Initialization Tests
# ---------------------------------------------------------------------------

class TestCBORGClientInit:
    """Tests for CBORGClient initialization and dependency handling."""

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key-123"})
    @patch("cborg_client.openai")
    def test_successful_creation(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_openai_module.OpenAI.return_value = MagicMock()
        client = CBORGClient(default_config)

        mock_openai_module.OpenAI.assert_called_once_with(
            base_url="https://cborg.lbl.gov/v1",
            api_key="test-key-123",
            timeout=30,
        )
        assert client.config is default_config

    @patch.dict("os.environ", {}, clear=True)
    @patch("cborg_client.openai")
    def test_missing_api_key_raises(self, mock_openai_module, default_config):
        # Ensure CBORG_API_KEY is not set
        from cborg_client import CBORGClient

        with pytest.raises(ValueError, match="API key not found"):
            CBORGClient(default_config)

    def test_missing_openai_dependency_raises(self, default_config):
        """If openai package is not installed, importing should fail gracefully."""
        with patch.dict("sys.modules", {"openai": None}):
            # Force reimport
            import importlib
            import cborg_client
            importlib.reload(cborg_client)

            with pytest.raises(ImportError, match="openai"):
                cborg_client.CBORGClient(default_config)

            # Restore the real module
            importlib.reload(cborg_client)


# ---------------------------------------------------------------------------
# API Call Tests
# ---------------------------------------------------------------------------

class TestCBORGClientAPICall:
    """Tests for _make_api_call — request formatting and response extraction."""

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_successful_api_call(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        json_response = json.dumps({
            "projects": ["ProjectX"],
            "participants": ["Alice"],
            "tasks": ["Code review"],
            "themes": ["Testing"],
        })
        mock_client.chat.completions.create.return_value = _make_chat_completion(json_response)

        client = CBORGClient(default_config)
        result = client._make_api_call("test prompt")

        assert result == json_response
        mock_client.chat.completions.create.assert_called_once()

        # Verify the request structure
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == default_config.model
        assert call_kwargs.kwargs["messages"][0]["role"] == "user"
        assert call_kwargs.kwargs["messages"][0]["content"] == "test prompt"
        assert call_kwargs.kwargs["temperature"] == 0.1

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_api_call_retries_on_rate_limit(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        # First call raises rate limit, second succeeds
        rate_limit_error = Exception("429 Too Many Requests: rate limit exceeded")
        success_response = _make_chat_completion('{"projects":[],"participants":[],"tasks":[],"themes":[]}')
        mock_client.chat.completions.create.side_effect = [rate_limit_error, success_response]

        client = CBORGClient(default_config)

        with patch("time.sleep"):  # Skip actual sleep
            result = client._make_api_call("test prompt")

        assert result == '{"projects":[],"participants":[],"tasks":[],"themes":[]}'
        assert mock_client.chat.completions.create.call_count == 2

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_api_call_raises_after_max_retries(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        # All calls raise rate limit error
        rate_limit_error = Exception("429 Too Many Requests: rate limit exceeded")
        mock_client.chat.completions.create.side_effect = rate_limit_error

        client = CBORGClient(default_config)

        with patch("time.sleep"):
            with pytest.raises(Exception, match="rate limit"):
                client._make_api_call("test prompt")

        # max_retries=3 means 4 total attempts (initial + 3 retries)
        assert mock_client.chat.completions.create.call_count == default_config.max_retries + 1

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_api_call_no_retry_on_auth_error(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        auth_error = Exception("401 Unauthorized: invalid API key")
        mock_client.chat.completions.create.side_effect = auth_error

        client = CBORGClient(default_config)

        with pytest.raises(Exception, match="Unauthorized"):
            client._make_api_call("test prompt")

        # Authentication errors should not be retried
        assert mock_client.chat.completions.create.call_count == 1


# ---------------------------------------------------------------------------
# Full analyze_content Flow Tests
# ---------------------------------------------------------------------------

class TestCBORGClientAnalyzeContent:
    """Tests for the full analysis pipeline inherited from BaseLLMClient."""

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_successful_analysis(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        entities = {
            "projects": ["Atlas"],
            "participants": ["Bob", "Carol"],
            "tasks": ["Deploy service"],
            "themes": ["Infrastructure"],
        }
        mock_client.chat.completions.create.return_value = _make_chat_completion(json.dumps(entities))

        client = CBORGClient(default_config)
        result = client.analyze_content("Worked on Atlas deployment", Path("test.txt"))

        assert isinstance(result, AnalysisResult)
        assert result.projects == ["Atlas"]
        assert result.participants == ["Bob", "Carol"]
        assert result.tasks == ["Deploy service"]
        assert result.themes == ["Infrastructure"]
        assert result.file_path == Path("test.txt")

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_failed_analysis_returns_empty_result(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Server error")

        client = CBORGClient(default_config)
        result = client.analyze_content("some content", Path("test.txt"))

        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert "ERROR" in result.raw_response


# ---------------------------------------------------------------------------
# Statistics Tests
# ---------------------------------------------------------------------------

class TestCBORGClientStats:
    """Tests for API statistics tracking."""

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_initial_stats(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_openai_module.OpenAI.return_value = MagicMock()
        client = CBORGClient(default_config)

        stats = client.get_stats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_stats_after_successful_call(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_chat_completion(
            '{"projects":[],"participants":[],"tasks":[],"themes":[]}'
        )

        client = CBORGClient(default_config)
        client.analyze_content("content", Path("test.txt"))

        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 1
        assert stats.failed_calls == 0

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_stats_reset(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_chat_completion(
            '{"projects":[],"participants":[],"tasks":[],"themes":[]}'
        )

        client = CBORGClient(default_config)
        client.analyze_content("content", Path("test.txt"))
        client.reset_stats()

        stats = client.get_stats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0


# ---------------------------------------------------------------------------
# test_connection Tests
# ---------------------------------------------------------------------------

class TestCBORGClientConnection:
    """Tests for test_connection()."""

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_successful_connection(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_chat_completion('{"test":"ok"}')

        client = CBORGClient(default_config)
        assert client.test_connection() is True

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_failed_connection(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_client = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection refused")

        client = CBORGClient(default_config)
        assert client.test_connection() is False


# ---------------------------------------------------------------------------
# get_provider_info Tests
# ---------------------------------------------------------------------------

class TestCBORGClientProviderInfo:
    """Tests for get_provider_info()."""

    @patch.dict("os.environ", {"CBORG_API_KEY": "test-key"})
    @patch("cborg_client.openai")
    def test_provider_info_content(self, mock_openai_module, default_config):
        from cborg_client import CBORGClient

        mock_openai_module.OpenAI.return_value = MagicMock()
        client = CBORGClient(default_config)

        info = client.get_provider_info()
        assert info["provider"] == "cborg"
        assert info["endpoint"] == "https://cborg.lbl.gov/v1"
        assert info["model"] == "lbl/cborg-chat:latest"

    @patch.dict("os.environ", {"CUSTOM_CBORG_KEY": "key-456"})
    @patch("cborg_client.openai")
    def test_provider_info_custom_config(self, mock_openai_module, custom_config):
        from cborg_client import CBORGClient

        mock_openai_module.OpenAI.return_value = MagicMock()
        client = CBORGClient(custom_config)

        info = client.get_provider_info()
        assert info["endpoint"] == "https://custom.cborg.example/v1"
        assert info["model"] == "lbl/custom-model:latest"
