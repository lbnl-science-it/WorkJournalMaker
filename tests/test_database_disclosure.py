# ABOUTME: Security tests for DatabaseManager response sanitization.
# ABOUTME: Verifies health_check and get_database_stats do not leak internal paths or errors.
"""Tests that DatabaseManager methods do not disclose internal details."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from web.database import DatabaseManager


@pytest_asyncio.fixture
async def db_manager(tmp_path):
    """Create an isolated DatabaseManager for testing."""
    db_path = str(tmp_path / "test.db")
    manager = DatabaseManager(database_path=db_path)
    await manager.initialize()
    return manager


class TestHealthCheckDisclosure:
    """health_check() must not expose database_path or raw error strings."""

    @pytest.mark.asyncio
    async def test_healthy_no_database_path(self, db_manager):
        result = await db_manager.health_check()
        assert result["status"] == "healthy"
        assert "database_path" not in result

    @pytest.mark.asyncio
    async def test_healthy_no_error_key(self, db_manager):
        result = await db_manager.health_check()
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_healthy_has_entry_count(self, db_manager):
        result = await db_manager.health_check()
        assert "entry_count" in result

    @pytest.mark.asyncio
    async def test_unhealthy_no_database_path(self, db_manager):
        """When the DB is broken, the response must still not leak the path."""
        # Dispose the engine to force a failure
        await db_manager.engine.dispose()
        db_manager.SessionLocal = None
        # Force an exception by making get_session fail
        with patch.object(db_manager, 'get_session', side_effect=Exception("connection failed")):
            result = await db_manager.health_check()
            assert result["status"] == "unhealthy"
            assert "database_path" not in result

    @pytest.mark.asyncio
    async def test_unhealthy_no_error_string(self, db_manager):
        """When the DB is broken, the raw error string must not be returned."""
        with patch.object(db_manager, 'get_session', side_effect=Exception("secret path /var/db")):
            result = await db_manager.health_check()
            assert "error" not in result


class TestGetDatabaseStatsDisclosure:
    """get_database_stats() must not expose raw error strings on failure."""

    @pytest.mark.asyncio
    async def test_stats_error_no_error_key(self, db_manager):
        """When stats collection fails, no 'error' key should be in the response."""
        with patch.object(db_manager, 'get_session', side_effect=Exception("internal error details")):
            result = await db_manager.get_database_stats()
            assert "error" not in result
            # Should still return zeroed-out stats
            assert result["total_entries"] == 0
