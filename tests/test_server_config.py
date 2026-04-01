"""ABOUTME: Tests for server mode configuration.
ABOUTME: Tests ServerConfig, AuthConfig, and SyncConfig dataclasses."""
import pytest
from config_manager import ServerConfig, AuthConfig, SyncConfig, AppConfig


class TestServerConfig:
    def test_default_mode_is_local(self):
        config = ServerConfig()
        assert config.mode == "local"

    def test_server_mode_requires_storage_root(self):
        config = ServerConfig(mode="server", storage_root="/data/users/")
        assert config.storage_root == "/data/users/"

    def test_local_mode_ignores_storage_root(self):
        config = ServerConfig(mode="local")
        assert config.storage_root is None


class TestAuthConfig:
    def test_auth_disabled_by_default(self):
        config = AuthConfig()
        assert config.enabled is False

    def test_google_auth_config(self):
        config = AuthConfig(
            enabled=True,
            provider="google",
            google_client_id="test-client-id",
            allowed_domains=["lbl.gov"],
        )
        assert config.provider == "google"
        assert "lbl.gov" in config.allowed_domains


class TestSyncConfig:
    def test_sync_disabled_by_default(self):
        config = SyncConfig()
        assert config.enabled is False

    def test_sync_with_remote_url(self):
        config = SyncConfig(
            enabled=True,
            remote_url="https://journal.example.com",
            auth_token="test-token",
        )
        assert config.remote_url == "https://journal.example.com"

    def test_auto_sync_interval_default(self):
        config = SyncConfig()
        assert config.auto_sync_interval == 0  # manual only


class TestAppConfigIntegration:
    def test_app_config_includes_server_config(self):
        config = AppConfig()
        assert hasattr(config, 'server')
        assert isinstance(config.server, ServerConfig)

    def test_app_config_includes_auth_config(self):
        config = AppConfig()
        assert hasattr(config, 'auth')
        assert isinstance(config.auth, AuthConfig)

    def test_app_config_includes_sync_config(self):
        config = AppConfig()
        assert hasattr(config, 'sync')
        assert isinstance(config.sync, SyncConfig)
