# ABOUTME: Integration tests for the fallback pipeline from config to CLI output.
# ABOUTME: Verifies YAML config loading, full provider chain, and user-visible notifications.
"""
Integration tests for Cluster C Step 4: config → UnifiedLLMClient → CLI fallback pipeline.
"""

import json
import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from config_manager import (
    AppConfig,
    BedrockConfig,
    CBORGConfig,
    ConfigManager,
    GoogleGenAIConfig,
    LLMConfig,
)
from llm_data_structures import AnalysisResult
from unified_llm_client import UnifiedLLMClient


# ---------------------------------------------------------------------------
# 1. ConfigManager correctly loads fallback_providers and cborg from YAML/JSON
# ---------------------------------------------------------------------------


class TestConfigFallbackLoading:
    """Verify ConfigManager deserializes fallback_providers and cborg sections."""

    def test_yaml_loads_fallback_providers(self):
        """A YAML config with fallback_providers should populate LLMConfig."""
        yaml_config = {
            "llm": {
                "provider": "google_genai",
                "fallback_providers": ["bedrock", "cborg"],
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()

            assert config.llm.provider == "google_genai"
            assert config.llm.fallback_providers == ["bedrock", "cborg"]
        finally:
            config_path.unlink()

    def test_json_loads_fallback_providers(self):
        """A JSON config with fallback_providers should populate LLMConfig."""
        json_config = {
            "llm": {
                "provider": "google_genai",
                "fallback_providers": ["bedrock"],
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(json_config, f)
            config_path = Path(f.name)

        try:
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()

            assert config.llm.fallback_providers == ["bedrock"]
        finally:
            config_path.unlink()

    def test_yaml_loads_cborg_config(self):
        """A YAML config with a cborg section should populate CBORGConfig."""
        yaml_config = {
            "llm": {"provider": "cborg"},
            "cborg": {
                "endpoint": "https://custom.lbl.gov/v1",
                "model": "custom-model",
                "max_retries": 5,
                "timeout": 60,
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()

            assert config.cborg.endpoint == "https://custom.lbl.gov/v1"
            assert config.cborg.model == "custom-model"
            assert config.cborg.max_retries == 5
            assert config.cborg.timeout == 60
        finally:
            config_path.unlink()

    def test_missing_fallback_providers_defaults_to_empty(self):
        """If fallback_providers is absent, it defaults to an empty list."""
        yaml_config = {"llm": {"provider": "google_genai"}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            config_manager = ConfigManager(config_path)
            config = config_manager.get_config()

            assert config.llm.fallback_providers == []
        finally:
            config_path.unlink()

    def test_invalid_fallback_provider_raises(self):
        """A fallback provider not in the valid set should raise ValueError."""
        yaml_config = {
            "llm": {
                "provider": "google_genai",
                "fallback_providers": ["invalid_provider"],
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid fallback provider"):
                ConfigManager(config_path)
        finally:
            config_path.unlink()

    def test_fallback_same_as_primary_raises(self):
        """A fallback that duplicates the primary provider should raise ValueError."""
        yaml_config = {
            "llm": {
                "provider": "google_genai",
                "fallback_providers": ["google_genai"],
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="cannot be the same as the primary"):
                ConfigManager(config_path)
        finally:
            config_path.unlink()

    def test_example_config_includes_cborg_and_fallback(self):
        """save_example_config should include cborg and fallback_providers sections."""
        with patch.object(ConfigManager, "_find_config_file", return_value=None):
            config_manager = ConfigManager()

        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False
        ) as f:
            config_path = Path(f.name)

        try:
            config_manager.save_example_config(config_path)
            with open(config_path) as f:
                saved = yaml.safe_load(f)

            assert "cborg" in saved
            assert "fallback_providers" in saved["llm"]
            assert isinstance(saved["llm"]["fallback_providers"], list)
            assert saved["cborg"]["endpoint"] == "https://cborg.lbl.gov/v1"
        finally:
            config_path.unlink()


# ---------------------------------------------------------------------------
# 2. Full pipeline: config → UnifiedLLMClient → fallback
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    """End-to-end test: config → client creation → fallback with mocked providers."""

    @pytest.fixture
    def mock_analysis_result(self):
        return AnalysisResult(
            file_path=Path("test.md"),
            projects=["P"],
            participants=["A"],
            tasks=["T"],
            themes=["Th"],
            api_call_time=0.1,
            raw_response="{}",
        )

    @patch("unified_llm_client.GoogleGenAIClient")
    def test_config_to_client_primary_succeeds(
        self, mock_google_client, mock_analysis_result
    ):
        """Config with google_genai primary → UnifiedLLMClient → analyze succeeds."""
        mock_instance = Mock()
        mock_instance.analyze_content.return_value = mock_analysis_result
        mock_google_client.return_value = mock_instance

        config = AppConfig(
            llm=LLMConfig(
                provider="google_genai", fallback_providers=["bedrock"]
            ),
            google_genai=GoogleGenAIConfig(project="test", model="test"),
            bedrock=BedrockConfig(region="us-east-1", model_id="m"),
        )

        client = UnifiedLLMClient(config)
        result = client.analyze_content("content", Path("f.md"))

        assert result == mock_analysis_result
        assert client.active_provider_name == "google_genai"

    @patch("unified_llm_client.BedrockClient")
    @patch("unified_llm_client.GoogleGenAIClient")
    def test_config_to_client_fallback_end_to_end(
        self, mock_google_client, mock_bedrock_client, mock_analysis_result
    ):
        """Config with fallback → primary fails → falls back → returns result."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google unavailable")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.return_value = mock_analysis_result
        mock_bedrock_client.return_value = mock_secondary

        config = AppConfig(
            llm=LLMConfig(
                provider="google_genai", fallback_providers=["bedrock"]
            ),
            google_genai=GoogleGenAIConfig(project="test", model="test"),
            bedrock=BedrockConfig(region="us-east-1", model_id="m"),
        )

        callback = Mock()
        client = UnifiedLLMClient(config, on_fallback=callback)
        result = client.analyze_content("content", Path("f.md"))

        assert result == mock_analysis_result
        assert client.active_provider_name == "bedrock"
        callback.assert_called_once()


# ---------------------------------------------------------------------------
# 3. CLI on_fallback callback prints to stdout
# ---------------------------------------------------------------------------


class TestCLIFallbackCallback:
    """Verify the CLI wires on_fallback so users see messages in the terminal."""

    @patch("unified_llm_client.BedrockClient")
    @patch("unified_llm_client.GoogleGenAIClient")
    def test_cli_creates_client_with_fallback_callback(
        self, mock_google_client, mock_bedrock_client
    ):
        """work_journal_summarizer should pass an on_fallback that prints."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Down")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.return_value = AnalysisResult(
            file_path=Path("t.md"),
            projects=[],
            participants=[],
            tasks=[],
            themes=[],
            api_call_time=0.1,
            raw_response="{}",
        )
        mock_bedrock_client.return_value = mock_secondary

        config = AppConfig(
            llm=LLMConfig(
                provider="google_genai", fallback_providers=["bedrock"]
            ),
            google_genai=GoogleGenAIConfig(project="t", model="m"),
            bedrock=BedrockConfig(region="us-east-1", model_id="m"),
        )

        # Import the callback function from the CLI module
        from work_journal_summarizer import fallback_notification

        captured = []
        with patch("builtins.print", side_effect=lambda *a, **kw: captured.append(a)):
            client = UnifiedLLMClient(config, on_fallback=fallback_notification)
            client.analyze_content("content", Path("f.md"))

        # The callback should have printed something with the ⚠ prefix
        printed_text = " ".join(str(a) for args in captured for a in args)
        assert "google_genai" in printed_text
        assert "bedrock" in printed_text

    def test_fallback_notification_function_exists(self):
        """The fallback_notification function should be importable from CLI module."""
        from work_journal_summarizer import fallback_notification

        assert callable(fallback_notification)

    def test_fallback_notification_prints_warning(self, capsys):
        """fallback_notification should print a user-friendly warning to stdout."""
        from work_journal_summarizer import fallback_notification

        fallback_notification("Provider 'google_genai' failed: API down. Falling back to 'bedrock'.")

        captured = capsys.readouterr()
        assert "google_genai" in captured.out
        assert "bedrock" in captured.out


class TestConfigSummaryWithFallback:
    """Verify print_config_summary shows fallback chain info."""

    @patch("builtins.print")
    def test_print_config_summary_shows_fallback_providers(self, mock_print):
        """print_config_summary should display the fallback chain if configured."""
        yaml_config = {
            "llm": {
                "provider": "google_genai",
                "fallback_providers": ["bedrock", "cborg"],
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            config_manager = ConfigManager(config_path)
            config_manager.print_config_summary()

            print_calls = [
                str(call) for call in mock_print.call_args_list
            ]
            joined = " ".join(print_calls)

            assert "Fallback" in joined or "fallback" in joined
            assert "bedrock" in joined
            assert "cborg" in joined
        finally:
            config_path.unlink()

    @patch("builtins.print")
    def test_print_config_summary_shows_cborg_details(self, mock_print):
        """print_config_summary should display CBORG details when it's the provider."""
        yaml_config = {
            "llm": {"provider": "cborg"},
            "cborg": {
                "endpoint": "https://cborg.lbl.gov/v1",
                "model": "lbl/cborg-chat:latest",
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(yaml_config, f)
            config_path = Path(f.name)

        try:
            config_manager = ConfigManager(config_path)
            config_manager.print_config_summary()

            print_calls = [
                str(call) for call in mock_print.call_args_list
            ]
            joined = " ".join(print_calls)

            assert "cborg" in joined.lower()
            assert "cborg.lbl.gov" in joined
        finally:
            config_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__])
