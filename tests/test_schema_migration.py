# ABOUTME: Tests for database schema migration when upgrading existing databases.
# ABOUTME: Validates that user_id column is added to journal_entries on existing databases.
"""Tests for schema migration of existing databases."""
import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from web.database import DatabaseManager, Base


@pytest.fixture
def legacy_db_path():
    """Create a temporary database with the old schema (no user_id column)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create old schema without user_id
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE journal_entries (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                file_path VARCHAR NOT NULL,
                week_ending_date DATE NOT NULL,
                word_count INTEGER,
                character_count INTEGER,
                line_count INTEGER,
                has_content BOOLEAN,
                file_size_bytes INTEGER,
                file_modified_at DATETIME,
                last_accessed_at DATETIME,
                access_count INTEGER,
                created_at DATETIME,
                modified_at DATETIME,
                synced_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE UNIQUE INDEX ix_journal_entries_date ON journal_entries (date)
        """))
        # Insert a legacy row
        conn.execute(text("""
            INSERT INTO journal_entries (date, file_path, week_ending_date, has_content)
            VALUES ('2024-06-10', '/worklogs/worklog_2024-06-10.txt', '2024-06-14', 1)
        """))
        conn.commit()
    engine.dispose()

    yield db_path

    os.unlink(db_path)


class TestSchemaMigration:
    """Test that DatabaseManager.initialize() migrates old schemas forward."""

    @pytest.mark.asyncio
    async def test_adds_user_id_column(self, legacy_db_path):
        """Initializing a legacy database adds the user_id column."""
        db = DatabaseManager(database_path=legacy_db_path)
        await db.initialize()

        # Verify column exists
        engine = create_engine(f"sqlite:///{legacy_db_path}")
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("journal_entries")]
        engine.dispose()

        assert "user_id" in columns

    @pytest.mark.asyncio
    async def test_existing_rows_get_default_user_id(self, legacy_db_path):
        """Existing rows get user_id='local' after migration."""
        db = DatabaseManager(database_path=legacy_db_path)
        await db.initialize()

        engine = create_engine(f"sqlite:///{legacy_db_path}")
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT user_id FROM journal_entries WHERE date='2024-06-10'"
            ))
            row = result.fetchone()
        engine.dispose()

        assert row is not None
        assert row[0] == "local"

    @pytest.mark.asyncio
    async def test_migration_is_idempotent(self, legacy_db_path):
        """Running initialize() twice does not error."""
        db = DatabaseManager(database_path=legacy_db_path)
        await db.initialize()
        # Second call should be a no-op
        await db.initialize()

        engine = create_engine(f"sqlite:///{legacy_db_path}")
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("journal_entries")]
        engine.dispose()

        assert "user_id" in columns

    @pytest.mark.asyncio
    async def test_fresh_database_has_user_id(self):
        """A brand new database gets user_id from the start."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        os.unlink(db_path)  # remove so initialize creates it fresh

        try:
            db = DatabaseManager(database_path=db_path)
            await db.initialize()

            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)
            columns = [c["name"] for c in inspector.get_columns("journal_entries")]
            engine.dispose()

            assert "user_id" in columns
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
