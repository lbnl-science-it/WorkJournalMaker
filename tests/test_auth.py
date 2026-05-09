# ABOUTME: Unit tests for auth configuration, JWT utilities, and FastAPI dependencies.
# ABOUTME: Validates auth-disabled mode, token lifecycle, and role-based access control.

import os
import pytest
from unittest.mock import patch
from config_manager import AppConfig, AuthConfig, ConfigManager


class TestAuthConfig:
    """Tests for AuthConfig dataclass and its integration with AppConfig."""

    def test_auth_config_defaults(self):
        config = AuthConfig()
        assert config.enabled is False
        assert config.provider == "local"
        assert config.secret_key == ""
        assert config.access_token_ttl == 1800
        assert config.refresh_token_ttl == 604800

    def test_app_config_includes_auth(self):
        config = AppConfig()
        assert hasattr(config, "auth")
        assert isinstance(config.auth, AuthConfig)
        assert config.auth.enabled is False


class TestAuthConfigLoading:
    """Tests for loading auth config from files and environment."""

    def test_secret_key_from_env_var(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("auth:\n  enabled: true\n")
        with patch.dict(os.environ, {"WJS_AUTH_SECRET_KEY": "test-secret-key-12345"}):
            manager = ConfigManager(config_path=config_file)
            assert manager.config.auth.secret_key == "test-secret-key-12345"
            assert manager.config.auth.enabled is True
