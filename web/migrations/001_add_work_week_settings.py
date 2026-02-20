# ABOUTME: Database migration to add the WorkWeekSettings table.
# ABOUTME: Populates default work-week configuration for existing installations.
"""
Database Migration Script: Add Work Week Settings

This migration adds the WorkWeekSettings table and populates it with default values
for existing installations.

Migration: 001_add_work_week_settings
Created: 2025-07-07
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, inspect
import logging

from web.database import WorkWeekSettings, Base, now_utc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkWeekMigration:
    """Handle work week settings migration."""
    
    def __init__(self, database_path: str = "web/journal_index.db"):
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
                # Check if work_week_settings table exists
                inspector = inspect(conn.sync_engine)
                tables = inspector.get_table_names()
                return 'work_week_settings' not in tables
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return True
    
    async def run_migration(self) -> dict:
        """Run the migration."""
        migration_result = {
            "success": False,
            "tables_created": 0,
            "records_created": 0,
            "errors": []
        }
        
        try:
            # Create tables if they don't exist
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                migration_result["tables_created"] = 1
                logger.info("Created work_week_settings table")
            
            # Add default work week settings
            async with self.SessionLocal() as session:
                # Check if default settings already exist
                stmt = select(WorkWeekSettings).where(WorkWeekSettings.user_id == "default")
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    default_work_week = WorkWeekSettings(
                        user_id="default",
                        work_week_preset="monday_friday",
                        work_week_start_day=1,  # Monday
                        work_week_end_day=5,    # Friday
                        timezone="UTC"
                    )
                    session.add(default_work_week)
                    await session.commit()
                    migration_result["records_created"] = 1
                    logger.info("Created default work week settings")
                else:
                    logger.info("Default work week settings already exist")
            
            migration_result["success"] = True
            logger.info("Migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            migration_result["errors"].append(str(e))
        
        return migration_result
    
    async def rollback_migration(self) -> dict:
        """Rollback the migration (for testing purposes)."""
        rollback_result = {
            "success": False,
            "tables_dropped": 0,
            "errors": []
        }
        
        try:
            async with self.engine.begin() as conn:
                # Drop work_week_settings table
                await conn.execute(text("DROP TABLE IF EXISTS work_week_settings"))
                rollback_result["tables_dropped"] = 1
                logger.info("Dropped work_week_settings table")
            
            rollback_result["success"] = True
            logger.info("Rollback completed successfully")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            rollback_result["errors"].append(str(e))
        
        return rollback_result
    
    async def validate_migration(self) -> dict:
        """Validate that migration was successful."""
        validation_result = {
            "valid": False,
            "table_exists": False,
            "default_settings_exist": False,
            "errors": []
        }
        
        try:
            async with self.SessionLocal() as session:
                # Check if table exists and is accessible
                stmt = select(WorkWeekSettings)
                result = await session.execute(stmt)
                all_settings = result.scalars().all()
                validation_result["table_exists"] = True
                
                # Check if default settings exist
                default_settings = [s for s in all_settings if s.user_id == "default"]
                if default_settings:
                    validation_result["default_settings_exist"] = True
                    default = default_settings[0]
                    
                    # Validate default values
                    if (default.work_week_preset == "monday_friday" and
                        default.work_week_start_day == 1 and
                        default.work_week_end_day == 5):
                        validation_result["valid"] = True
                        logger.info("Migration validation successful")
                    else:
                        validation_result["errors"].append("Default settings have incorrect values")
                else:
                    validation_result["errors"].append("Default settings not found")
                    
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
    
    parser = argparse.ArgumentParser(description="Work Week Settings Migration")
    parser.add_argument("--database", default="web/journal_index.db", 
                       help="Database file path")
    parser.add_argument("--rollback", action="store_true", 
                       help="Rollback the migration")
    parser.add_argument("--validate", action="store_true", 
                       help="Validate the migration")
    parser.add_argument("--force", action="store_true", 
                       help="Force migration even if not needed")
    
    args = parser.parse_args()
    
    migration = WorkWeekMigration(args.database)
    await migration.initialize()
    
    try:
        if args.rollback:
            result = await migration.rollback_migration()
            print(f"Rollback result: {result}")
        elif args.validate:
            result = await migration.validate_migration()
            print(f"Validation result: {result}")
        else:
            # Check if migration is needed
            if not args.force and not await migration.check_migration_needed():
                print("Migration not needed - work_week_settings table already exists")
                return
            
            # Run migration
            result = await migration.run_migration()
            print(f"Migration result: {result}")
            
            # Validate migration
            validation = await migration.validate_migration()
            print(f"Validation result: {validation}")
    
    finally:
        await migration.close()


if __name__ == "__main__":
    asyncio.run(main())