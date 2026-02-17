#!/usr/bin/env python3
# ABOUTME: Tests for LLM data structures including the LLMClientProtocol interface contract.
# ABOUTME: Verifies Protocol conformance, runtime checkability, and dataclass correctness.

import pytest
from pathlib import Path
from typing import Dict, Any

from llm_data_structures import AnalysisResult, APIStats, LLMClientProtocol


class TestLLMClientProtocol:
    """Tests for the LLMClientProtocol interface contract."""

    def test_protocol_is_runtime_checkable(self):
        """LLMClientProtocol should be usable with isinstance() checks."""
        assert hasattr(LLMClientProtocol, '__protocol_attrs__') or hasattr(LLMClientProtocol, '__abstractmethods__') or hasattr(LLMClientProtocol, '_is_runtime_protocol')
        # runtime_checkable protocols have this attribute
        assert getattr(LLMClientProtocol, '_is_runtime_protocol', False) is True

    def test_conforming_class_passes_isinstance(self):
        """A class implementing all required methods should satisfy the Protocol."""

        class ConformingClient:
            def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
                pass

            def get_stats(self) -> APIStats:
                pass

            def reset_stats(self) -> None:
                pass

            def test_connection(self) -> bool:
                pass

            def get_provider_info(self) -> Dict[str, Any]:
                pass

        client = ConformingClient()
        assert isinstance(client, LLMClientProtocol)

    def test_non_conforming_class_fails_isinstance(self):
        """A class missing required methods should not satisfy the Protocol."""

        class NonConformingClient:
            def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
                pass
            # Missing: get_stats, reset_stats, test_connection, get_provider_info

        client = NonConformingClient()
        assert not isinstance(client, LLMClientProtocol)

    def test_partial_conformance_fails(self):
        """A class with only some methods should not satisfy the Protocol."""

        class PartialClient:
            def analyze_content(self, content: str, file_path: Path) -> AnalysisResult:
                pass

            def get_stats(self) -> APIStats:
                pass

            def reset_stats(self) -> None:
                pass
            # Missing: test_connection, get_provider_info

        client = PartialClient()
        assert not isinstance(client, LLMClientProtocol)


class TestAnalysisResult:
    """Tests for the AnalysisResult dataclass."""

    def test_creation_with_all_fields(self):
        """AnalysisResult should store all provided fields."""
        result = AnalysisResult(
            file_path=Path("test.txt"),
            projects=["Project A"],
            participants=["John"],
            tasks=["Task 1"],
            themes=["Theme A"],
            api_call_time=1.5,
            confidence_score=0.9,
            raw_response='{"test": "data"}'
        )

        assert result.file_path == Path("test.txt")
        assert result.projects == ["Project A"]
        assert result.participants == ["John"]
        assert result.tasks == ["Task 1"]
        assert result.themes == ["Theme A"]
        assert result.api_call_time == 1.5
        assert result.confidence_score == 0.9
        assert result.raw_response == '{"test": "data"}'

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        result = AnalysisResult(
            file_path=Path("test.txt"),
            projects=[],
            participants=[],
            tasks=[],
            themes=[],
            api_call_time=0.0
        )

        assert result.confidence_score is None
        assert result.raw_response is None


class TestAPIStats:
    """Tests for the APIStats dataclass."""

    def test_creation(self):
        """APIStats should store all provided fields."""
        stats = APIStats(
            total_calls=10,
            successful_calls=8,
            failed_calls=2,
            total_time=15.5,
            average_response_time=1.94,
            rate_limit_hits=1
        )

        assert stats.total_calls == 10
        assert stats.successful_calls == 8
        assert stats.failed_calls == 2
        assert stats.total_time == 15.5
        assert stats.average_response_time == 1.94
        assert stats.rate_limit_hits == 1
