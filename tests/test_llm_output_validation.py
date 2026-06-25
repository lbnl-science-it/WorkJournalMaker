#!/usr/bin/env python3
# ABOUTME: Tests that LLM output entities are validated and sanitized before use.
# ABOUTME: Covers max length, control character stripping, and format-string injection defense.
"""
Tests for LLM Output Schema Validation (Issue #34/#37)

Verifies that entity strings returned by the LLM are validated at the element
level (max length, control character stripping) and sanitized before
interpolation into summary prompts (format-string injection defense).
"""

import json
import pytest
from pathlib import Path
from datetime import date

from base_llm_client import BaseLLMClient
from summary_generator import SummaryGenerator


# ---------------------------------------------------------------------------
# Stub client for testing parse/dedup pipeline
# ---------------------------------------------------------------------------

class StubValidationClient(BaseLLMClient):
    """Returns a pre-set JSON response to exercise the parse pipeline."""

    def __init__(self, response_json=""):
        self._response_json = response_json
        super().__init__()

    def _make_api_call(self, system: str, user: str) -> str:
        return self._response_json

    def test_connection(self) -> bool:
        return True

    def get_provider_info(self):
        return {"provider": "stub"}


# ---------------------------------------------------------------------------
# Element-level validation in _parse_response (base_llm_client.py)
# ---------------------------------------------------------------------------

class TestEntityLengthValidation:
    """Entity strings longer than 200 characters are truncated."""

    def test_overlong_entity_is_truncated(self):
        """An entity exceeding 200 chars is truncated to 200."""
        long_entity = "A" * 300
        response = json.dumps({
            "projects": [long_entity],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert len(result.projects[0]) <= 200

    def test_normal_length_entity_preserved(self):
        """An entity under 200 chars is not altered."""
        normal = "Project Alpha"
        response = json.dumps({
            "projects": [normal],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert result.projects[0] == normal

    def test_exactly_200_char_entity_preserved(self):
        """An entity of exactly 200 chars is not altered."""
        exact = "B" * 200
        response = json.dumps({
            "projects": [exact],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert result.projects[0] == exact

    def test_truncation_across_all_categories(self):
        """Truncation applies to all four entity categories."""
        long_val = "X" * 250
        response = json.dumps({
            "projects": [long_val],
            "participants": [long_val],
            "tasks": [long_val],
            "themes": [long_val],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert len(result.projects[0]) <= 200
        assert len(result.participants[0]) <= 200
        assert len(result.tasks[0]) <= 200
        assert len(result.themes[0]) <= 200


class TestControlCharacterStripping:
    """Control characters are stripped from entity strings."""

    def test_null_bytes_stripped(self):
        """Null bytes are removed from entity strings."""
        response = json.dumps({
            "projects": ["Project\x00Alpha"],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert "\x00" not in result.projects[0]
        assert "ProjectAlpha" in result.projects[0]

    def test_newlines_and_tabs_stripped(self):
        """Newline and tab characters are stripped from entity values."""
        response = json.dumps({
            "projects": ["Project\nAlpha\tBeta"],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert "\n" not in result.projects[0]
        assert "\t" not in result.projects[0]

    def test_carriage_return_stripped(self):
        """Carriage return characters are stripped."""
        response = json.dumps({
            "projects": ["Project\r\nAlpha"],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert "\r" not in result.projects[0]

    def test_other_control_chars_stripped(self):
        """Other ASCII control characters (0x01-0x1F) are stripped."""
        response = json.dumps({
            "projects": ["Project\x01\x02\x03Alpha"],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert "\x01" not in result.projects[0]
        assert "\x02" not in result.projects[0]
        assert "\x03" not in result.projects[0]

    def test_printable_characters_preserved(self):
        """Normal printable characters including unicode are preserved."""
        response = json.dumps({
            "projects": ["Café Résumé — Project"],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert result.projects[0] == "Café Résumé — Project"

    def test_empty_after_stripping_is_dropped(self):
        """An entity that becomes empty after control char stripping is dropped."""
        response = json.dumps({
            "projects": ["\x00\x01\x02"],
            "participants": [],
            "tasks": [],
            "themes": [],
        })
        client = StubValidationClient(response)
        result = client.analyze_content("journal text", Path("/test.txt"))
        assert result.projects == []


# ---------------------------------------------------------------------------
# Format-string injection defense in summary_generator.py
# ---------------------------------------------------------------------------

class TestFormatStringInjectionDefense:
    """Entity strings with {} braces must not crash .format() in summary generation."""

    def test_braces_in_entity_do_not_crash_format(self):
        """Entities containing {curly braces} must not cause KeyError in .format()."""
        malicious_entities = {
            "projects": ["{__class__}", "{0}", "{{nested}}"],
            "participants": ["Alice"],
            "tasks": ["{__init__.__globals__}"],
            "themes": ["Normal theme"],
        }

        # This should not raise KeyError or IndexError
        sanitized_projects = SummaryGenerator._sanitize_entity_list(malicious_entities["projects"])
        sanitized_tasks = SummaryGenerator._sanitize_entity_list(malicious_entities["tasks"])

        for item in sanitized_projects:
            assert "{" not in item
            assert "}" not in item

        for item in sanitized_tasks:
            assert "{" not in item
            assert "}" not in item

    def test_sanitize_preserves_normal_entities(self):
        """Normal entity strings without braces are unchanged."""
        entities = ["Project Alpha", "Code Review", "Weekly standup"]
        sanitized = SummaryGenerator._sanitize_entity_list(entities)
        assert sanitized == entities

    def test_sanitize_strips_braces_only(self):
        """Only curly braces are removed; other punctuation is preserved."""
        entities = ["Project (Alpha) [v2.0] <beta>"]
        sanitized = SummaryGenerator._sanitize_entity_list(entities)
        assert sanitized == ["Project (Alpha) [v2.0] <beta>"]

    def test_full_summary_generation_with_malicious_entities(self):
        """End-to-end: summary generation does not crash with brace-laden entities."""
        malicious_entities = {
            "projects": ["{__class__}", "Real Project"],
            "participants": ["{0}", "Bob"],
            "tasks": ["{key}", "Deploy v2"],
            "themes": ["Testing {injection}"],
        }

        # SummaryGenerator._generate_period_summary uses .format() internally.
        # Create a stub client that returns a simple summary text.
        stub_response = json.dumps({
            "projects": [], "participants": [], "tasks": [], "themes": [],
        })
        client = StubValidationClient(stub_response)
        generator = SummaryGenerator(client)

        # This must not raise — it should produce a fallback or sanitized summary
        try:
            summary = generator._generate_period_summary(
                period_name="Week of 2024-01-15",
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 21),
                aggregated_entities=malicious_entities,
                entry_count=5,
            )
            assert isinstance(summary, str)
            assert len(summary) > 0
        except (KeyError, IndexError) as e:
            pytest.fail(f".format() injection succeeded: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
