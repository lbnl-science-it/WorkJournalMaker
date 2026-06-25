#!/usr/bin/env python3
# ABOUTME: Tests that LLM providers separate system instructions from user content.
# ABOUTME: Verifies each provider uses its native mechanism for role-based message separation.
"""
Tests for LLM System/User Message Separation (Issue #33/#36)

Verifies that trusted system instructions and untrusted user content are sent
through separate API fields in each LLM provider, rather than concatenated
into a single user message.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from base_llm_client import BaseLLMClient


# ---------------------------------------------------------------------------
# Base client tests — prompt splitting
# ---------------------------------------------------------------------------

class StubSplitClient(BaseLLMClient):
    """Concrete subclass that captures the system/user args passed to _make_api_call."""

    def __init__(self):
        self.last_system = None
        self.last_user = None
        super().__init__()

    def _make_api_call(self, system: str, user: str) -> str:
        self.last_system = system
        self.last_user = user
        return json.dumps({
            "projects": [], "participants": [], "tasks": [], "themes": []
        })

    def test_connection(self) -> bool:
        return True

    def get_provider_info(self):
        return {"provider": "stub"}


class TestBaseClientPromptSeparation:
    """Tests that _create_analysis_prompt returns (system, user) tuple."""

    def test_create_analysis_prompt_returns_tuple(self):
        """_create_analysis_prompt returns a two-element tuple."""
        client = StubSplitClient()
        result = client._create_analysis_prompt("some journal content")
        assert isinstance(result, tuple), "Expected tuple, got %s" % type(result).__name__
        assert len(result) == 2

    def test_system_prompt_contains_instructions(self):
        """System prompt contains extraction instructions but not user content."""
        client = StubSplitClient()
        system, user = client._create_analysis_prompt("Work on Project X")
        assert "JSON" in system
        assert "projects" in system
        assert "participants" in system
        assert "Work on Project X" not in system

    def test_user_prompt_contains_journal_content(self):
        """User prompt contains the journal content."""
        client = StubSplitClient()
        system, user = client._create_analysis_prompt("Work on Project X with Alice")
        assert "Work on Project X with Alice" in user

    def test_user_prompt_has_delimiter_tags(self):
        """User content is wrapped in delimiter tags for defense-in-depth."""
        client = StubSplitClient()
        system, user = client._create_analysis_prompt("my journal entry")
        assert "<journal-content>" in user
        assert "</journal-content>" in user

    def test_system_prompt_does_not_contain_user_data(self):
        """System prompt never contains the user's journal text."""
        client = StubSplitClient()
        unique_content = "UNIQUETOKEN_abc123_xyz"
        system, _user = client._create_analysis_prompt(unique_content)
        assert unique_content not in system

    def test_truncation_still_works(self):
        """Content exceeding 8000 chars is still truncated in user prompt."""
        client = StubSplitClient()
        long_content = "A" * 9000
        _system, user = client._create_analysis_prompt(long_content)
        assert "[Content truncated for analysis]" in user
        assert "A" * 9000 not in user

    def test_analyze_content_passes_both_parts(self):
        """analyze_content calls _make_api_call with separate system and user args."""
        client = StubSplitClient()
        client.analyze_content("daily journal text", Path("/test.txt"))
        assert client.last_system is not None
        assert client.last_user is not None
        assert "daily journal text" in client.last_user
        assert "daily journal text" not in client.last_system


# ---------------------------------------------------------------------------
# Bedrock provider tests
# ---------------------------------------------------------------------------

class TestBedrockSystemUserSeparation:
    """Tests that Bedrock sends system and user as separate API fields."""

    def test_bedrock_request_has_system_field(self):
        """Bedrock request body includes a top-level 'system' field."""
        from bedrock_client import BedrockClient
        from config_manager import BedrockConfig

        config = BedrockConfig(
            region="us-west-2",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            max_retries=0,
            rate_limit_delay=0,
        )

        with patch.dict("os.environ", {
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }):
            client = BedrockClient(config)

        request = client._format_bedrock_request(
            system="You are an analyzer.",
            user="Journal entry content here."
        )

        assert "system" in request, "Bedrock request must have a top-level 'system' field"
        assert request["system"] == "You are an analyzer."
        # User content should be in messages with role=user
        user_messages = [m for m in request["messages"] if m["role"] == "user"]
        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "Journal entry content here."

    def test_bedrock_request_no_system_in_user_message(self):
        """System instructions must not appear inside the user message."""
        from bedrock_client import BedrockClient
        from config_manager import BedrockConfig

        config = BedrockConfig(
            region="us-west-2",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            max_retries=0,
            rate_limit_delay=0,
        )

        with patch.dict("os.environ", {
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }):
            client = BedrockClient(config)

        system_text = "Extract structured information."
        request = client._format_bedrock_request(
            system=system_text,
            user="Some journal text."
        )

        user_messages = [m for m in request["messages"] if m["role"] == "user"]
        for msg in user_messages:
            assert system_text not in msg["content"]


# ---------------------------------------------------------------------------
# Google GenAI provider tests
# ---------------------------------------------------------------------------

class TestGoogleGenAISystemUserSeparation:
    """Tests that Google GenAI uses system_instruction for system content."""

    @pytest.fixture
    def mock_google_client(self):
        """Create a GoogleGenAIClient with mocked dependencies."""
        from google_genai_client import GoogleGenAIClient
        from config_manager import GoogleGenAIConfig

        config = GoogleGenAIConfig(
            project="test-project",
            location="us-central1",
            model="gemini-2.0-flash-001",
        )

        with patch("google_genai_client.genai") as mock_genai:
            mock_client_instance = MagicMock()
            mock_genai.Client.return_value = mock_client_instance

            # Mock a successful response
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "projects": [], "participants": [], "tasks": [], "themes": []
            })
            mock_response.candidates = []
            mock_client_instance.models.generate_content.return_value = mock_response

            client = GoogleGenAIClient(config)
            yield client, mock_client_instance

    def test_genai_uses_system_instruction(self, mock_google_client):
        """Google GenAI passes system content via system_instruction config."""
        client, mock_inner = mock_google_client

        client._make_api_call(
            system="You are an analyzer.",
            user="Journal text here."
        )

        call_kwargs = mock_inner.models.generate_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")

        assert "system_instruction" in config, \
            "Google GenAI config must include system_instruction"
        assert config["system_instruction"] == "You are an analyzer."

    def test_genai_user_content_in_contents(self, mock_google_client):
        """Google GenAI passes user content as the contents parameter."""
        client, mock_inner = mock_google_client

        client._make_api_call(
            system="System instructions.",
            user="User journal entry."
        )

        call_kwargs = mock_inner.models.generate_content.call_args
        contents = call_kwargs.kwargs.get("contents") or call_kwargs[1].get("contents")

        assert "User journal entry." in str(contents)


# ---------------------------------------------------------------------------
# CBORG provider tests
# ---------------------------------------------------------------------------

class TestCBORGSystemUserSeparation:
    """Tests that CBORG uses separate system and user role messages."""

    @pytest.fixture
    def mock_cborg_client(self):
        """Create a CBORGClient with mocked dependencies."""
        from cborg_client import CBORGClient
        from config_manager import CBORGConfig

        config = CBORGConfig(
            endpoint="https://cborg.lbl.gov/api/v1",
            model="lbl/cborg-chat:latest",
            api_key_env="CBORG_API_KEY",
            max_retries=0,
            timeout=30,
        )

        with patch.dict("os.environ", {"CBORG_API_KEY": "test-key"}):
            with patch("cborg_client.openai") as mock_openai:
                mock_client_instance = MagicMock()
                mock_openai.OpenAI.return_value = mock_client_instance

                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps({
                    "projects": [], "participants": [], "tasks": [], "themes": []
                })
                mock_client_instance.chat.completions.create.return_value = mock_response

                client = CBORGClient(config)
                yield client, mock_client_instance

    def test_cborg_sends_system_role_message(self, mock_cborg_client):
        """CBORG includes a message with role='system' in the messages list."""
        client, mock_inner = mock_cborg_client

        client._make_api_call(
            system="You are an analyzer.",
            user="Journal text here."
        )

        call_kwargs = mock_inner.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")

        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) == 1, "Expected exactly one system message"
        assert system_msgs[0]["content"] == "You are an analyzer."

    def test_cborg_sends_user_role_message(self, mock_cborg_client):
        """CBORG includes a message with role='user' containing the journal content."""
        client, mock_inner = mock_cborg_client

        client._make_api_call(
            system="System instructions.",
            user="User journal entry."
        )

        call_kwargs = mock_inner.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")

        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 1, "Expected exactly one user message"
        assert user_msgs[0]["content"] == "User journal entry."

    def test_cborg_system_before_user(self, mock_cborg_client):
        """System message appears before user message in the messages list."""
        client, mock_inner = mock_cborg_client

        client._make_api_call(
            system="System prompt.",
            user="User content."
        )

        call_kwargs = mock_inner.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")

        roles = [m["role"] for m in messages]
        system_idx = roles.index("system")
        user_idx = roles.index("user")
        assert system_idx < user_idx, "System message must precede user message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
