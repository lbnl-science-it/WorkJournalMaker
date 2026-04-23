# ABOUTME: Tests verifying that FastAPI dependency overrides correctly isolate the database.
# ABOUTME: Ensures get_db_manager returns app.state.db_manager and can be overridden in tests.

"""
Tests for FastAPI Dependency Override Isolation

Verifies that the get_db_manager dependency function works correctly
and can be overridden in tests to provide a temporary database.
"""

import asyncio
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import insert

from web.app import app
from web.database import DatabaseManager, JournalEntryIndex
from web.dependencies import get_db_manager


class TestGetDbManagerDependency:
    """Verify get_db_manager dependency function exists and is importable."""

    def test_get_db_manager_is_importable(self):
        """get_db_manager can be imported and the health endpoint responds."""
        with TestClient(app) as client:
            # The health endpoint uses get_db_manager via Depends —
            # if it responds, the dependency resolved successfully
            response = client.get("/api/health/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ("healthy", "degraded")


class TestDbManagerOverrideInHealthEndpoints:
    """Verify health endpoints use the overridden db_manager."""

    def test_health_check_uses_overridden_db_manager(self, tmp_path):
        """GET /api/health/ should use the dependency-injected db_manager."""
        temp_db_path = str(tmp_path / "override_test.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        app.dependency_overrides[get_db_manager] = lambda: temp_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/health/")
                assert response.status_code == 200
                data = response.json()
                # The temp DB is valid, so health check should succeed
                assert data["status"] in ("healthy", "degraded")
        finally:
            app.dependency_overrides.clear()
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()

    def test_metrics_uses_overridden_db_manager(self, tmp_path):
        """GET /api/health/metrics should use the dependency-injected db_manager."""
        temp_db_path = str(tmp_path / "metrics_test.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        async def seed():
            async with temp_db.get_session() as session:
                await session.execute(
                    insert(JournalEntryIndex).values(
                        date=date(2026, 1, 1),
                        week_ending_date=date(2026, 1, 3),
                        file_path="/tmp/test.txt",
                        has_content=True,
                    )
                )
                await session.commit()

        loop.run_until_complete(seed())

        app.dependency_overrides[get_db_manager] = lambda: temp_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/health/metrics")
                assert response.status_code == 200
                data = response.json()
                assert "database" in data
                # Temp DB has exactly 1 seeded entry, proving the override is active
                assert data["database"]["entry_count"] == 1
        finally:
            app.dependency_overrides.clear()
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()


class TestDbManagerOverrideInEntriesEndpoints:
    """Verify entries stats endpoint uses the overridden db_manager."""

    def test_database_stats_uses_overridden_db_manager(self, tmp_path):
        """GET /api/entries/stats/database should use dependency-injected db_manager."""
        temp_db_path = str(tmp_path / "entries_stats_test.db")
        temp_db = DatabaseManager(temp_db_path)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(temp_db.initialize())

        app.dependency_overrides[get_db_manager] = lambda: temp_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/entries/stats/database")
                assert response.status_code == 200
                data = response.json()
                # Temp DB has zero entries — real DB has 460+, so == 0 is discriminating
                assert data["total_entries"] == 0
                assert data["entries_with_content"] == 0
        finally:
            app.dependency_overrides.clear()
            loop.run_until_complete(temp_db.engine.dispose())
            loop.close()
