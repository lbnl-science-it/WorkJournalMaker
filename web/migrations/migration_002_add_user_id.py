# ABOUTME: Database migration to add user_id column to journal_entries.
# ABOUTME: Backfills existing rows with the "default" user_id value.
"""
Database Migration Script: Add user_id to journal_entries

This migration adds the user_id column required for multi-user support.
Existing rows are backfilled with user_id='default'.

Migration: 002_add_user_id_to_journal_entries
Created: 2026-05-26
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserIdMigration:
    """Handle adding user_id column to journal_entries."""

    def __init__(self, database_path: str = None):
        if database_path is None:
            from web.database import DatabaseManager
            dm = DatabaseManager()
            self.database_path = dm.database_path
        else:
            self.database_path = database_path
        self.engine = None
        self.SessionLocal = None

    async def initialize(self):
        """Initialize database connection."""
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.database_path}",
            echo=False
        )
        self.SessionLocal = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def check_migration_needed(self) -> bool:
        """Check if migration is needed."""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("PRAGMA table_info(journal_entries)"))
                columns = [row[1] for row in result.fetchall()]
                return "user_id" not in columns
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return True

    async def run_migration(self) -> dict:
        """Run the migration."""
        migration_result = {
            "success": False,
            "column_added": False,
            "index_created": False,
            "errors": []
        }

        try:
            async with self.engine.begin() as conn:
                await conn.execute(text(
                    "ALTER TABLE journal_entries "
                    "ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'"
                ))
                migration_result["column_added"] = True
                logger.info("Added user_id column to journal_entries")

                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_journal_entries_user_id "
                    "ON journal_entries(user_id)"
                ))
                migration_result["index_created"] = True
                logger.info("Created index on journal_entries.user_id")

            migration_result["success"] = True
            logger.info("Migration completed successfully")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_result["errors"].append(str(e))

        return migration_result

    async def rollback_migration(self) -> dict:
        """Rollback the migration."""
        rollback_result = {
            "success": False,
            "errors": []
        }

        try:
            async with self.engine.begin() as conn:
                await conn.execute(text(
                    "DROP INDEX IF EXISTS ix_journal_entries_user_id"
                ))
                await conn.execute(text(
                    "ALTER TABLE journal_entries DROP COLUMN user_id"
                ))
                logger.info("Rolled back user_id column from journal_entries")

            rollback_result["success"] = True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_result["errors"].append(str(e))

        return rollback_result

    async def validate_migration(self) -> dict:
        """Validate that migration was successful."""
        validation_result = {
            "valid": False,
            "column_exists": False,
            "all_rows_have_user_id": False,
            "errors": []
        }

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("PRAGMA table_info(journal_entries)"))
                columns = [row[1] for row in result.fetchall()]
                validation_result["column_exists"] = "user_id" in columns

                if validation_result["column_exists"]:
                    result = await conn.execute(text(
                        "SELECT COUNT(*) FROM journal_entries "
                        "WHERE user_id IS NULL OR user_id = ''"
                    ))
                    null_count = result.scalar()
                    validation_result["all_rows_have_user_id"] = null_count == 0

                validation_result["valid"] = (
                    validation_result["column_exists"]
                    and validation_result["all_rows_have_user_id"]
                )

                if validation_result["valid"]:
                    logger.info("Migration validation successful")
                else:
                    logger.warning("Migration validation failed: %s", validation_result)

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            validation_result["errors"].append(str(e))

        return validation_result

    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()


async def main():
    """Run migration from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migration 002: Add user_id to journal_entries"
    )
    parser.add_argument("--database", default=None,
                        help="Database file path (defaults to OS-standard location)")
    parser.add_argument("--rollback", action="store_true",
                        help="Rollback the migration")
    parser.add_argument("--validate", action="store_true",
                        help="Validate the migration")
    parser.add_argument("--force", action="store_true",
                        help="Force migration even if not needed")

    args = parser.parse_args()

    migration = UserIdMigration(args.database)
    await migration.initialize()

    try:
        if args.rollback:
            result = await migration.rollback_migration()
            print(f"Rollback result: {result}")
        elif args.validate:
            result = await migration.validate_migration()
            print(f"Validation result: {result}")
        else:
            if not args.force and not await migration.check_migration_needed():
                print("Migration not needed - user_id column already exists")
                return

            result = await migration.run_migration()
            print(f"Migration result: {result}")

            validation = await migration.validate_migration()
            print(f"Validation result: {validation}")

    finally:
        await migration.close()


if __name__ == "__main__":
    asyncio.run(main())
