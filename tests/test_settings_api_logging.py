# ABOUTME: Tests that error logging in settings API endpoints actually calls the logger.
# ABOUTME: Verifies fix for broken conditional expression pattern that silently swallowed errors.

"""
Tests for error logging in settings API endpoints.

Validates that when settings endpoints encounter errors, the logger.logger.error
method is actually called with the error message, rather than being silently
discarded by a broken conditional expression.
"""

import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import web.api.settings as settings_module
from web.api.settings import router


@pytest.fixture
def mock_logger():
    """Create a mock logger matching the JournalSummarizerLogger interface."""
    mock = MagicMock()
    mock.logger = MagicMock()
    mock.logger.error = MagicMock()
    mock.logger.info = MagicMock()
    return mock


@pytest.fixture
def mock_settings_service():
    """Create a mock settings service whose methods raise exceptions."""
    service = AsyncMock()
    return service


@pytest.fixture(autouse=True)
def patch_settings_module(mock_logger):
    """Inject mock logger into the settings module for each test."""
    original_logger = settings_module.logger
    settings_module.logger = mock_logger
    yield
    settings_module.logger = original_logger


class TestSettingsApiErrorLogging:
    """Verify that error logging is actually invoked when endpoints raise exceptions."""

    @pytest.mark.asyncio
    async def test_get_all_settings_logs_error(self, mock_logger, mock_settings_service):
        """Line 62: get_all_settings should log error when service raises."""
        mock_settings_service.get_all_settings.side_effect = RuntimeError("db failure")

        from web.api.settings import get_all_settings
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_all_settings(settings_service=mock_settings_service)

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "db failure" in call_args

    @pytest.mark.asyncio
    async def test_get_settings_categories_logs_error(self, mock_logger, mock_settings_service):
        """Line 77: get_settings_categories should log error when service raises."""
        # get_setting_categories is a sync method, so use MagicMock (not AsyncMock)
        mock_settings_service.get_setting_categories = MagicMock(
            side_effect=RuntimeError("category error")
        )

        from web.api.settings import get_settings_categories
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_settings_categories(settings_service=mock_settings_service)

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "category error" in call_args

    @pytest.mark.asyncio
    async def test_get_setting_logs_error(self, mock_logger, mock_settings_service):
        """Line 315: get_setting should log error when service raises."""
        mock_settings_service.get_setting.side_effect = RuntimeError("lookup error")

        from web.api.settings import get_setting
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_setting(key="ui.theme", settings_service=mock_settings_service)

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "lookup error" in call_args

    @pytest.mark.asyncio
    async def test_update_setting_logs_error(self, mock_logger, mock_settings_service):
        """Line 342: update_setting should log error when service raises."""
        mock_settings_service.update_setting.side_effect = RuntimeError("update error")

        from web.api.settings import update_setting
        from web.models.settings import WebSettingUpdate
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await update_setting(
                key="ui.theme",
                setting_update=WebSettingUpdate(value="dark"),
                settings_service=mock_settings_service
            )

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "update error" in call_args

    @pytest.mark.asyncio
    async def test_reset_setting_logs_error(self, mock_logger, mock_settings_service):
        """Line 537: reset_setting should log error when service raises."""
        mock_settings_service.reset_setting.side_effect = RuntimeError("reset error")

        from web.api.settings import reset_setting
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await reset_setting(key="ui.theme", settings_service=mock_settings_service)

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "reset error" in call_args

    @pytest.mark.asyncio
    async def test_reset_all_settings_logs_error(self, mock_logger, mock_settings_service):
        """Line 552: reset_all_settings should log error when service raises."""
        mock_settings_service.reset_all_settings.side_effect = RuntimeError("reset all error")

        from web.api.settings import reset_all_settings
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await reset_all_settings(settings_service=mock_settings_service)

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "reset all error" in call_args

    @pytest.mark.asyncio
    async def test_export_settings_logs_error(self, mock_logger, mock_settings_service):
        """Line 567: export_settings should log error when service raises."""
        mock_settings_service.export_settings.side_effect = RuntimeError("export error")

        from web.api.settings import export_settings
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await export_settings(settings_service=mock_settings_service)

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "export error" in call_args

    @pytest.mark.asyncio
    async def test_import_settings_logs_error(self, mock_logger, mock_settings_service):
        """Line 588: import_settings should log error when service raises."""
        mock_settings_service.import_settings.side_effect = RuntimeError("import error")

        from web.api.settings import import_settings
        from web.models.settings import SettingsImport
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await import_settings(
                import_data=SettingsImport(settings={}),
                settings_service=mock_settings_service
            )

        assert exc_info.value.status_code == 500
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "import error" in call_args

    @pytest.mark.asyncio
    async def test_validate_path_logs_error(self, mock_logger):
        """Line 648: validate_filesystem_path should log error on unexpected exception."""
        from web.api.settings import validate_filesystem_path
        from fastapi import HTTPException

        # Patch pathlib.Path (used via local import inside the function) to raise
        with patch("pathlib.Path") as MockPath:
            MockPath.side_effect = RuntimeError("path error")
            with pytest.raises(HTTPException) as exc_info:
                await validate_filesystem_path(
                    path="/some/test/path",
                    settings_service=AsyncMock()
                )

        assert exc_info.value.status_code == 400
        mock_logger.logger.error.assert_called_once()
        call_args = mock_logger.logger.error.call_args[0][0]
        assert "path error" in call_args
