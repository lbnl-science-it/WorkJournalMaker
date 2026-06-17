#!/usr/bin/env python3
# ABOUTME: Tests that no real GCP project ID is hardcoded in config defaults.
# ABOUTME: Ensures GoogleGenAIConfig ships with a placeholder, not production infrastructure metadata.
"""
Tests for GH#98 — GCP project ID must not be hardcoded in source code.
"""

import pytest

from config_manager import GoogleGenAIConfig


class TestGCPProjectIDNotHardcoded:
    """Verify the default GoogleGenAIConfig does not contain real infrastructure IDs."""

    def test_default_project_is_placeholder(self):
        """Default project must not be the real GCP project ID."""
        config = GoogleGenAIConfig()
        assert config.project != "geminijournal-463220", (
            "Real GCP project ID is hardcoded as default"
        )

    def test_default_project_signals_user_action_needed(self):
        """Default project value must clearly indicate it needs to be configured."""
        config = GoogleGenAIConfig()
        # Should be an obvious placeholder, not something that looks like a real ID
        assert "your" in config.project.lower() or "change" in config.project.lower() or "set" in config.project.lower(), (
            "Default project should be an obvious placeholder prompting user configuration"
        )


if __name__ == "__main__":
    pytest.main([__file__])
