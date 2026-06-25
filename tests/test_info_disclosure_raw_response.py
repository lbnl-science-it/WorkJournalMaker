#!/usr/bin/env python3
# ABOUTME: Tests that raw_response does not leak exception details on LLM API failure.
# ABOUTME: Ensures error type is indicated without exposing ARNs, URIs, or internal paths.
"""
Information Disclosure Tests for raw_response Field

Verifies that when an LLM API call fails, the raw_response field of
AnalysisResult only contains a sanitized error type indicator, not the
full exception message which could contain sensitive data such as ARNs,
credentials, file paths, or internal URIs.
"""

import pytest
from pathlib import Path

from base_llm_client import BaseLLMClient
from llm_data_structures import AnalysisResult


class StubLLMClient(BaseLLMClient):
    """Minimal concrete subclass for testing error handling in BaseLLMClient."""

    def __init__(self, fail_error=None):
        self._fail_error = fail_error or Exception("Stub API failure")
        super().__init__()

    def _make_api_call(self, system: str, user: str) -> str:
        raise self._fail_error

    def test_connection(self) -> bool:
        return False

    def get_provider_info(self):
        return {"provider": "stub", "model": "test-model"}


class TestRawResponseInfoDisclosure:
    """Tests that sensitive exception details are not stored in raw_response."""

    def test_raw_response_does_not_contain_exception_message(self):
        """raw_response must not include the exception message text on failure."""
        sensitive_message = "Connection failed: arn:aws:iam::123456789:role/MyRole"
        error = ConnectionError(sensitive_message)
        client = StubLLMClient(fail_error=error)

        result = client.analyze_content("journal content", Path("/test.txt"))

        assert sensitive_message not in result.raw_response

    def test_raw_response_does_not_contain_file_path(self):
        """raw_response must not leak internal file system paths."""
        path_in_error = "Failed to open /var/run/secrets/aws/credentials"
        error = OSError(path_in_error)
        client = StubLLMClient(fail_error=error)

        result = client.analyze_content("content", Path("/test.txt"))

        assert path_in_error not in result.raw_response
        assert "/var/run/secrets" not in result.raw_response

    def test_raw_response_does_not_contain_uri(self):
        """raw_response must not leak internal service URIs."""
        uri_in_error = "https://internal.corp.example.com:8443/api/v2/token"
        error = ValueError(f"Auth error at {uri_in_error}")
        client = StubLLMClient(fail_error=error)

        result = client.analyze_content("content", Path("/test.txt"))

        assert uri_in_error not in result.raw_response
        assert "internal.corp.example.com" not in result.raw_response

    def test_raw_response_contains_error_type_only(self):
        """raw_response contains just the error type name in the expected format."""
        error = ConnectionError("arn:aws:bedrock:us-east-1::foundation-model/secret")
        client = StubLLMClient(fail_error=error)

        result = client.analyze_content("content", Path("/test.txt"))

        assert result.raw_response == "ERROR (ConnectionError)"

    def test_raw_response_format_for_generic_exception(self):
        """raw_response follows ERROR (<TypeName>) format for generic Exception."""
        client = StubLLMClient(fail_error=Exception("internal detail"))

        result = client.analyze_content("content", Path("/test.txt"))

        assert result.raw_response == "ERROR (Exception)"

    def test_raw_response_format_for_runtime_error(self):
        """raw_response reflects the actual exception class name."""
        client = StubLLMClient(fail_error=RuntimeError("sensitive internal trace"))

        result = client.analyze_content("content", Path("/test.txt"))

        assert result.raw_response == "ERROR (RuntimeError)"

    def test_failed_result_has_empty_entity_lists(self):
        """Failure path still returns empty entity lists alongside sanitized response."""
        client = StubLLMClient(fail_error=Exception("boom"))

        result = client.analyze_content("content", Path("/fail.txt"))

        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []

    def test_successful_call_raw_response_unaffected(self):
        """Success path raw_response still stores the parsed JSON entities."""
        import json

        class SuccessClient(BaseLLMClient):
            def _make_api_call(self, system, user):
                return json.dumps({
                    "projects": ["Alpha"],
                    "participants": [],
                    "tasks": [],
                    "themes": [],
                })

            def test_connection(self):
                return True

            def get_provider_info(self):
                return {}

        client = SuccessClient()
        result = client.analyze_content("content", Path("/ok.txt"))

        assert result.raw_response is not None
        assert "Alpha" in result.raw_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
