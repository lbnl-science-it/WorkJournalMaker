# ABOUTME: Tests for settings.py dependency injection refactor (Cluster E, Step 1).
# ABOUTME: Verifies settings endpoints use app.state instead of module-level globals.

"""
Tests for settings.py dependency injection refactor.

Verifies that web/api/settings.py uses request.app.state for dependency
injection instead of module-level globals, matching the pattern used by
all other API modules.
"""

import ast
import inspect
import pytest
from fastapi.testclient import TestClient

from web.app import app
from web.api import settings as settings_module


class TestSettingsDependencyInjection:
    """Verify settings.py uses app.state DI pattern."""

    def test_no_module_level_globals(self):
        """Module-level DI globals must not exist in settings.py."""
        # These globals were the old pattern — they should be removed
        assert not hasattr(settings_module, 'config_manager') or settings_module.config_manager is None, \
            "Module-level 'config_manager' global should be removed"
        assert not hasattr(settings_module, 'config') or settings_module.config is None, \
            "Module-level 'config' global should be removed"
        # 'logger' and 'db_manager' should also not exist as module-level globals
        # We check the AST to be precise — attribute existence isn't enough
        # because the module could re-define them in a function scope

    def test_no_global_assignments_in_module(self):
        """The settings module must not contain module-level global assignments
        for config_manager, config, logger, or db_manager."""
        source = inspect.getsource(settings_module)
        tree = ast.parse(source)

        forbidden_globals = {'config_manager', 'config', 'logger', 'db_manager'}
        found = set()

        for node in ast.iter_child_nodes(tree):
            # Module-level assignments like `config_manager = None`
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in forbidden_globals:
                        found.add(target.id)

        assert not found, (
            f"Module-level global assignments found for: {found}. "
            "These should be removed in favor of request.app.state."
        )

    def test_get_settings_service_is_synchronous(self):
        """get_settings_service must be a synchronous function (not async),
        matching the pattern in calendar.py and other API modules."""
        func = settings_module.get_settings_service
        assert not inspect.iscoroutinefunction(func), \
            "get_settings_service should be synchronous, not async"

    def test_get_settings_service_accepts_request_parameter(self):
        """get_settings_service must accept a Request parameter."""
        sig = inspect.signature(settings_module.get_settings_service)
        param_names = list(sig.parameters.keys())
        assert 'request' in param_names, \
            "get_settings_service must accept a 'request' parameter"

    def test_no_global_keyword_in_get_settings_service(self):
        """get_settings_service must not use the 'global' keyword."""
        source = inspect.getsource(settings_module.get_settings_service)
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                pytest.fail(
                    "get_settings_service uses 'global' keyword — "
                    "it should read from request.app.state instead"
                )


class TestSettingsServiceOnAppState:
    """Verify that app.state.settings_service is set during lifespan."""

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    def test_settings_service_on_app_state(self, client):
        """app.state must have a settings_service attribute after startup."""
        assert hasattr(client.app.state, 'settings_service'), \
            "app.state.settings_service must be set during lifespan"

    def test_settings_service_shares_logger(self, client):
        """settings_service must use the same logger instance as app.state."""
        settings_svc = client.app.state.settings_service
        app_logger = client.app.state.logger
        assert settings_svc.logger is app_logger, \
            "SettingsService.logger must be the same instance as app.state.logger"

    def test_settings_service_shares_config(self, client):
        """settings_service must use the same config instance as app.state."""
        settings_svc = client.app.state.settings_service
        app_config = client.app.state.config
        assert settings_svc.config is app_config, \
            "SettingsService.config must be the same instance as app.state.config"

    def test_settings_service_shares_db_manager(self, client):
        """settings_service must use the same db_manager instance as app.state."""
        settings_svc = client.app.state.settings_service
        app_db = client.app.state.db_manager
        assert settings_svc.db_manager is app_db, \
            "SettingsService.db_manager must be the same instance as app.state.db_manager"


class TestSettingsEndpointsWithDI:
    """Verify settings API endpoints work with the new DI pattern."""

    @pytest.fixture
    def client(self):
        with TestClient(app) as c:
            yield c

    def test_get_all_settings(self, client):
        """GET /api/settings/ should return 200."""
        response = client.get("/api/settings/")
        assert response.status_code == 200

    def test_get_settings_categories(self, client):
        """GET /api/settings/categories should return 200."""
        response = client.get("/api/settings/categories")
        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data

    def test_settings_health_check(self, client):
        """GET /api/settings/health should return 200."""
        response = client.get("/api/settings/health")
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data

    def test_get_specific_setting(self, client):
        """GET /api/settings/ui.theme should return the theme setting."""
        response = client.get("/api/settings/ui.theme")
        assert response.status_code == 200
        data = response.json()
        assert data['key'] == 'ui.theme'

    def test_update_setting(self, client):
        """PUT /api/settings/ui.theme should update the setting."""
        response = client.put(
            "/api/settings/ui.theme",
            json={"value": "dark"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['key'] == 'ui.theme'

    def test_get_work_week_config(self, client):
        """GET /api/settings/work-week should return 200."""
        response = client.get("/api/settings/work-week")
        assert response.status_code == 200

    def test_get_work_week_presets(self, client):
        """GET /api/settings/work-week/presets should return 200."""
        response = client.get("/api/settings/work-week/presets")
        assert response.status_code == 200


class TestNoStaleImports:
    """Verify that stale imports from the globals pattern are removed."""

    def test_no_config_manager_import_for_instantiation(self):
        """settings.py should not import ConfigManager for instantiation.
        (It may still import it if needed for type hints, but should not
        create a new ConfigManager instance.)"""
        source = inspect.getsource(settings_module)
        # Check that there's no `ConfigManager()` call in the source
        assert 'ConfigManager()' not in source, \
            "settings.py should not instantiate ConfigManager — use app.state"

    def test_no_logger_instantiation(self):
        """settings.py should not instantiate JournalSummarizerLogger."""
        source = inspect.getsource(settings_module)
        assert 'JournalSummarizerLogger(' not in source, \
            "settings.py should not instantiate JournalSummarizerLogger — use app.state"

    def test_no_database_manager_instantiation(self):
        """settings.py should not instantiate DatabaseManager."""
        source = inspect.getsource(settings_module)
        assert 'DatabaseManager()' not in source, \
            "settings.py should not instantiate DatabaseManager — use app.state"
