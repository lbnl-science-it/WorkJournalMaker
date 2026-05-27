# ABOUTME: Tests for migration 002 — adding user_id column to journal_entries.
# ABOUTME: Verifies both auto-migration in DatabaseManager and standalone script.

import asyncio
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch


def create_legacy_database(db_path: str):
    """Create a journal_entries table without the user_id column."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            file_path TEXT NOT NULL,
            week_ending_date DATE NOT NULL,
            word_count INTEGER DEFAULT 0,
            character_count INTEGER DEFAULT 0,
            line_count INTEGER DEFAULT 0,
            has_content BOOLEAN DEFAULT 0,
            file_size_bytes INTEGER DEFAULT 0,
            file_modified_at DATETIME,
            last_accessed_at DATETIME,
            access_count INTEGER DEFAULT 0,
            created_at DATETIME,
            modified_at DATETIME,
            synced_at DATETIME
        )
    """)
    conn.execute("CREATE INDEX ix_journal_entries_date ON journal_entries(date)")
    conn.execute("CREATE INDEX ix_journal_entries_has_content ON journal_entries(has_content)")
    conn.execute("CREATE INDEX ix_journal_entries_week_ending_date ON journal_entries(week_ending_date)")
    conn.execute("""
        INSERT INTO journal_entries (date, file_path, week_ending_date, word_count, has_content)
        VALUES ('2026-05-20', '/tmp/worklog_2026-05-20.txt', '2026-05-23', 100, 1)
    """)
    conn.commit()
    conn.close()


def get_columns(db_path: str, table: str) -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns


def get_indexes(db_path: str, table: str) -> list:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(f"PRAGMA index_list({table})")
    indexes = [row[1] for row in cursor.fetchall()]
    conn.close()
    return indexes


class TestDatabaseManagerAutoMigration:
    """Test that DatabaseManager.initialize() auto-migrates missing user_id."""

    @pytest.mark.asyncio
    async def test_adds_user_id_to_legacy_database(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        assert "user_id" not in get_columns(db_path, "journal_entries")

        from web.database import DatabaseManager
        dm = DatabaseManager()
        with patch.object(dm, 'database_path', db_path):
            await dm.initialize()

        columns = get_columns(db_path, "journal_entries")
        assert "user_id" in columns

    @pytest.mark.asyncio
    async def test_existing_rows_get_default_user_id(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        from web.database import DatabaseManager
        dm = DatabaseManager()
        with patch.object(dm, 'database_path', db_path):
            await dm.initialize()

        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT user_id FROM journal_entries")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 1
        assert rows[0][0] == "default"

    @pytest.mark.asyncio
    async def test_creates_user_id_index(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        from web.database import DatabaseManager
        dm = DatabaseManager()
        with patch.object(dm, 'database_path', db_path):
            await dm.initialize()

        indexes = get_indexes(db_path, "journal_entries")
        assert any("user_id" in idx for idx in indexes)

    @pytest.mark.asyncio
    async def test_noop_when_column_exists(self, tmp_path):
        """If user_id already exists, migration should be a no-op."""
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        # Manually add user_id first
        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE journal_entries ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        conn.commit()
        conn.close()

        assert "user_id" in get_columns(db_path, "journal_entries")

        from web.database import DatabaseManager
        dm = DatabaseManager()
        with patch.object(dm, 'database_path', db_path):
            await dm.initialize()

        # Should still work fine
        columns = get_columns(db_path, "journal_entries")
        assert "user_id" in columns


class TestStandaloneMigration:
    """Test the standalone migration script."""

    @pytest.mark.asyncio
    async def test_check_migration_needed_on_legacy_db(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        from web.migrations.migration_002_add_user_id import UserIdMigration
        migration = UserIdMigration(db_path)
        await migration.initialize()

        assert await migration.check_migration_needed() is True
        await migration.close()

    @pytest.mark.asyncio
    async def test_check_migration_not_needed(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute("ALTER TABLE journal_entries ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        conn.commit()
        conn.close()

        from web.migrations.migration_002_add_user_id import UserIdMigration
        migration = UserIdMigration(db_path)
        await migration.initialize()

        assert await migration.check_migration_needed() is False
        await migration.close()

    @pytest.mark.asyncio
    async def test_run_migration(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        from web.migrations.migration_002_add_user_id import UserIdMigration
        migration = UserIdMigration(db_path)
        await migration.initialize()

        result = await migration.run_migration()
        assert result["success"] is True

        columns = get_columns(db_path, "journal_entries")
        assert "user_id" in columns
        await migration.close()

    @pytest.mark.asyncio
    async def test_validate_migration(self, tmp_path):
        db_path = str(tmp_path / "test_journal.db")
        create_legacy_database(db_path)

        from web.migrations.migration_002_add_user_id import UserIdMigration
        migration = UserIdMigration(db_path)
        await migration.initialize()
        await migration.run_migration()

        result = await migration.validate_migration()
        assert result["valid"] is True
        assert result["column_exists"] is True
        assert result["all_rows_have_user_id"] is True
        await migration.close()
