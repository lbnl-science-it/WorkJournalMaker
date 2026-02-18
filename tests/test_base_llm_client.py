#!/usr/bin/env python3
# ABOUTME: Tests for BaseLLMClient abstract base class shared methods.
# ABOUTME: Uses a concrete test subclass to verify prompt building, JSON extraction, dedup, and stats.
"""
Tests for BaseLLMClient - Shared LLM Client Logic

Tests the shared methods extracted into BaseLLMClient using a minimal concrete
test subclass that stubs the abstract methods.
"""

import pytest
import json
from pathlib import Path

from base_llm_client import BaseLLMClient
from llm_data_structures import AnalysisResult, APIStats


class StubLLMClient(BaseLLMClient):
    """Minimal concrete subclass for testing BaseLLMClient shared methods."""

    def __init__(self, api_response_text="", should_fail=False, fail_error=None):
        self._api_response_text = api_response_text
        self._should_fail = should_fail
        self._fail_error = fail_error or Exception("Stub API failure")
        super().__init__()

    def _make_api_call(self, prompt: str) -> str:
        if self._should_fail:
            raise self._fail_error
        return self._api_response_text

    def test_connection(self) -> bool:
        return not self._should_fail

    def get_provider_info(self):
        return {"provider": "stub", "model": "test-model"}


class TestBaseLLMClientPrompt:
    """Tests for ANALYSIS_PROMPT and _create_analysis_prompt."""

    def test_analysis_prompt_contains_required_fields(self):
        """ANALYSIS_PROMPT template references all four entity categories."""
        client = StubLLMClient()
        prompt = client.ANALYSIS_PROMPT
        assert "projects" in prompt
        assert "participants" in prompt
        assert "tasks" in prompt
        assert "themes" in prompt
        assert "JSON" in prompt

    def test_create_analysis_prompt_includes_content(self):
        """Content is embedded in the formatted prompt."""
        client = StubLLMClient()
        prompt = client._create_analysis_prompt("Work on Project X with Alice")
        assert "Work on Project X with Alice" in prompt

    def test_create_analysis_prompt_truncates_long_content(self):
        """Content longer than 8000 chars is truncated."""
        client = StubLLMClient()
        long_content = "A" * 9000
        prompt = client._create_analysis_prompt(long_content)
        assert "[Content truncated for analysis]" in prompt
        # The full 9000-char content should NOT appear
        assert "A" * 9000 not in prompt

    def test_create_analysis_prompt_preserves_short_content(self):
        """Content under 8000 chars is not truncated."""
        client = StubLLMClient()
        short_content = "B" * 100
        prompt = client._create_analysis_prompt(short_content)
        assert short_content in prompt
        assert "[Content truncated for analysis]" not in prompt


class TestBaseLLMClientJsonExtraction:
    """Tests for _extract_json_from_text."""

    def test_extract_json_from_markdown_code_block(self):
        """Extracts JSON from ```json ... ``` blocks."""
        client = StubLLMClient()
        text = '```json\n{"key": "value"}\n```'
        result = client._extract_json_from_text(text)
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_extract_json_from_plain_code_block(self):
        """Extracts JSON from ``` ... ``` blocks without language tag."""
        client = StubLLMClient()
        text = '```\n{"key": "value"}\n```'
        result = client._extract_json_from_text(text)
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_extract_json_from_raw_text(self):
        """Extracts JSON object from text without code blocks."""
        client = StubLLMClient()
        text = 'Here is the result: {"projects": ["Alpha"]} done.'
        result = client._extract_json_from_text(text)
        parsed = json.loads(result)
        assert parsed == {"projects": ["Alpha"]}

    def test_extract_json_direct_json_string(self):
        """Returns JSON string directly when it IS the JSON."""
        client = StubLLMClient()
        text = '{"tasks": ["review"]}'
        result = client._extract_json_from_text(text)
        assert json.loads(result) == {"tasks": ["review"]}

    def test_extract_json_no_json_present(self):
        """Returns text as-is when no JSON is found."""
        client = StubLLMClient()
        text = "This is just plain text with no JSON"
        result = client._extract_json_from_text(text)
        assert result == text

    def test_extract_json_empty_string(self):
        """Handles empty string input."""
        client = StubLLMClient()
        result = client._extract_json_from_text("")
        assert result == ""

    def test_extract_json_non_string_input(self):
        """Handles non-string input by converting to string."""
        client = StubLLMClient()
        result = client._extract_json_from_text(12345)
        assert result == "12345"


class TestBaseLLMClientDeduplication:
    """Tests for _deduplicate_entities."""

    def test_removes_case_insensitive_duplicates(self):
        """Duplicates differing only by case are removed."""
        client = StubLLMClient()
        entities = {
            "projects": ["Alpha", "alpha", "ALPHA"],
            "participants": ["John Doe", "john doe"],
            "tasks": ["Review", "review"],
            "themes": ["Dev", "dev", "DEV"],
        }
        result = client._deduplicate_entities(entities)
        assert len(result["projects"]) == 1
        assert len(result["participants"]) == 1
        assert len(result["tasks"]) == 1
        assert len(result["themes"]) == 1

    def test_preserves_first_occurrence_casing(self):
        """The first casing encountered is kept."""
        client = StubLLMClient()
        entities = {"projects": ["Project Alpha", "project alpha"]}
        result = client._deduplicate_entities(entities)
        assert result["projects"] == ["Project Alpha"]

    def test_preserves_distinct_entries(self):
        """Genuinely different entries are all kept."""
        client = StubLLMClient()
        entities = {"projects": ["Alpha", "Beta", "Gamma"]}
        result = client._deduplicate_entities(entities)
        assert result["projects"] == ["Alpha", "Beta", "Gamma"]

    def test_handles_non_list_values(self):
        """Non-list values are replaced with empty list."""
        client = StubLLMClient()
        entities = {"projects": "not a list", "tasks": 42}
        result = client._deduplicate_entities(entities)
        assert result["projects"] == []
        assert result["tasks"] == []

    def test_handles_non_string_items(self):
        """Non-string items in lists are silently skipped."""
        client = StubLLMClient()
        entities = {"projects": ["Alpha", 123, None, "Beta"]}
        result = client._deduplicate_entities(entities)
        assert result["projects"] == ["Alpha", "Beta"]

    def test_strips_whitespace(self):
        """Leading/trailing whitespace is stripped."""
        client = StubLLMClient()
        entities = {"projects": ["  Alpha  ", "Alpha"]}
        result = client._deduplicate_entities(entities)
        assert result["projects"] == ["Alpha"]

    def test_skips_empty_strings(self):
        """Empty strings and whitespace-only strings are skipped."""
        client = StubLLMClient()
        entities = {"projects": ["", "  ", "Alpha"]}
        result = client._deduplicate_entities(entities)
        assert result["projects"] == ["Alpha"]


class TestBaseLLMClientStats:
    """Tests for get_stats and reset_stats."""

    def test_initial_stats_are_zero(self):
        """Stats are zeroed on construction."""
        client = StubLLMClient()
        stats = client.get_stats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.total_time == 0.0
        assert stats.average_response_time == 0.0
        assert stats.rate_limit_hits == 0

    def test_reset_stats_clears_all_fields(self):
        """reset_stats zeros out all APIStats fields."""
        client = StubLLMClient()
        # Manually set stats
        client.stats.total_calls = 10
        client.stats.successful_calls = 8
        client.stats.failed_calls = 2
        client.stats.total_time = 50.0
        client.stats.average_response_time = 6.25
        client.stats.rate_limit_hits = 3
        # Reset
        client.reset_stats()
        stats = client.get_stats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.total_time == 0.0
        assert stats.average_response_time == 0.0
        assert stats.rate_limit_hits == 0

    def test_get_stats_returns_same_object(self):
        """get_stats returns the live stats instance."""
        client = StubLLMClient()
        stats = client.get_stats()
        stats.total_calls = 5
        assert client.get_stats().total_calls == 5


class TestBaseLLMClientAnalyzeContent:
    """Tests for the analyze_content flow (shared bookkeeping)."""

    def test_successful_analysis_returns_populated_result(self):
        """Successful API call produces an AnalysisResult with entities."""
        response_json = json.dumps({
            "projects": ["Alpha"],
            "participants": ["John"],
            "tasks": ["review"],
            "themes": ["dev"],
        })
        client = StubLLMClient(api_response_text=response_json)
        result = client.analyze_content("journal content", Path("/test.txt"))

        assert isinstance(result, AnalysisResult)
        assert result.file_path == Path("/test.txt")
        assert result.projects == ["Alpha"]
        assert result.participants == ["John"]
        assert result.tasks == ["review"]
        assert result.themes == ["dev"]
        assert result.api_call_time > 0

    def test_successful_analysis_updates_stats(self):
        """Successful call increments total_calls and successful_calls."""
        response_json = json.dumps({
            "projects": [], "participants": [], "tasks": [], "themes": [],
        })
        client = StubLLMClient(api_response_text=response_json)
        client.analyze_content("content", Path("/f.txt"))

        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 1
        assert stats.failed_calls == 0
        assert stats.total_time > 0
        assert stats.average_response_time > 0

    def test_failed_analysis_returns_empty_result(self):
        """API failure returns empty AnalysisResult with error in raw_response."""
        client = StubLLMClient(should_fail=True)
        result = client.analyze_content("content", Path("/fail.txt"))

        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
        assert "ERROR (Exception):" in result.raw_response

    def test_failed_analysis_updates_stats(self):
        """Failed call increments total_calls and failed_calls."""
        client = StubLLMClient(should_fail=True)
        client.analyze_content("content", Path("/fail.txt"))

        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 0
        assert stats.failed_calls == 1

    def test_multiple_calls_accumulate_stats(self):
        """Multiple calls correctly accumulate timing and counts."""
        response_json = json.dumps({
            "projects": [], "participants": [], "tasks": [], "themes": [],
        })
        client = StubLLMClient(api_response_text=response_json)
        for _ in range(3):
            client.analyze_content("content", Path("/f.txt"))

        stats = client.get_stats()
        assert stats.total_calls == 3
        assert stats.successful_calls == 3
        assert stats.total_time > 0
        assert stats.average_response_time > 0

    def test_missing_entity_fields_default_to_empty_list(self):
        """Response missing expected fields gets them filled as empty lists."""
        response_json = json.dumps({"projects": ["Alpha"]})
        client = StubLLMClient(api_response_text=response_json)
        result = client.analyze_content("content", Path("/f.txt"))

        assert result.projects == ["Alpha"]
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []

    def test_non_list_entity_fields_replaced_with_empty_list(self):
        """Non-list entity field values are replaced with empty lists."""
        response_json = json.dumps({
            "projects": "not a list",
            "participants": 42,
            "tasks": [],
            "themes": [],
        })
        client = StubLLMClient(api_response_text=response_json)
        result = client.analyze_content("content", Path("/f.txt"))

        assert result.projects == []
        assert result.participants == []

    def test_malformed_json_response_returns_empty_result(self):
        """Invalid JSON from API produces empty AnalysisResult (no crash)."""
        client = StubLLMClient(api_response_text="not json at all")
        result = client.analyze_content("content", Path("/f.txt"))

        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []

    def test_markdown_wrapped_json_response_is_parsed(self):
        """JSON wrapped in markdown code block is correctly extracted."""
        response = '```json\n{"projects": ["Beta"], "participants": [], "tasks": [], "themes": []}\n```'
        client = StubLLMClient(api_response_text=response)
        result = client.analyze_content("content", Path("/f.txt"))

        assert result.projects == ["Beta"]

    def test_deduplication_applied_to_analysis_results(self):
        """Entities in the API response are deduplicated."""
        response_json = json.dumps({
            "projects": ["Alpha", "alpha", "Beta"],
            "participants": ["John", "john"],
            "tasks": ["review"],
            "themes": ["dev"],
        })
        client = StubLLMClient(api_response_text=response_json)
        result = client.analyze_content("content", Path("/f.txt"))

        assert len(result.projects) == 2  # Alpha + Beta
        assert len(result.participants) == 1  # John

    def test_raw_response_stored_on_success(self):
        """raw_response contains the API response text on success."""
        response_json = json.dumps({
            "projects": [], "participants": [], "tasks": [], "themes": [],
        })
        client = StubLLMClient(api_response_text=response_json)
        result = client.analyze_content("content", Path("/f.txt"))

        # raw_response should contain the JSON (possibly re-serialized)
        assert result.raw_response is not None


class TestBaseLLMClientIsAbstract:
    """Tests verifying BaseLLMClient cannot be instantiated directly."""

    def test_cannot_instantiate_directly(self):
        """BaseLLMClient raises TypeError if instantiated without abstract methods."""
        with pytest.raises(TypeError):
            BaseLLMClient()


if __name__ == "__main__":
    pytest.main([__file__])
