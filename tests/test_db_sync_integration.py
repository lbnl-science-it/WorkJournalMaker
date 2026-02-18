#!/usr/bin/env python3
"""
Simple integration test for database synchronization with work week service.
"""

import asyncio
import tempfile
import os
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock

# Add current directory to path
import sys

from web.database import DatabaseManager, JournalEntryIndex
from web.services.entry_manager import EntryManager  
from web.services.work_week_service import WorkWeekService
from config_manager import AppConfig
from logger import JournalSummarizerLogger


async def test_database_sync_integration():
    """Test that database synchronization works with work week service integration."""
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Initialize database
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Create mock config and logger
        config = Mock(spec=AppConfig)
        config.processing = Mock()
        config.processing.base_path = "/tmp/test_journals"
        
        logger = Mock(spec=JournalSummarizerLogger)
        logger.logger = Mock()
        logger.error = Mock()
        
        # Create services
        work_week_service = WorkWeekService(config, logger, db_manager)
        entry_manager = EntryManager(config, logger, db_manager, work_week_service)
        
        # Test entry synchronization
        entry_date = date(2024, 1, 15)  # Monday
        test_file_path = Path("/tmp/test/2024-01-19/2024-01-15.md")
        test_content = "Test journal entry content"
        
        print(f"Testing entry synchronization for {entry_date}")
        
        # Mock file stats since file doesn't actually exist
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = Path(temp_file.name)
        
        try:
            # Sync entry to database
            async with db_manager.get_session() as session:
                await entry_manager._sync_entry_to_database_session(
                    session, entry_date, temp_file_path, test_content
                )
                await session.commit()
            
            print("Entry synchronized successfully")
            
            # Verify entry was created with calculated week ending
            async with db_manager.get_session() as session:
                from sqlalchemy import select
                stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
                result = await session.execute(stmt)
                entry = result.scalar_one_or_none()
                
                if entry:
                    print(f"Entry found:")
                    print(f"  Date: {entry.date}")
                    print(f"  Week ending: {entry.week_ending_date}")
                    print(f"  Word count: {entry.word_count}")
                    print(f"  Has content: {entry.has_content}")
                    
                    # Verify week ending calculation
                    expected_week_ending = await work_week_service.calculate_week_ending_date(entry_date)
                    print(f"  Expected week ending: {expected_week_ending}")
                    
                    if entry.week_ending_date == expected_week_ending:
                        print("✅ Week ending date calculation matches expected value")
                    else:
                        print("❌ Week ending date calculation mismatch")
                        return False
                        
                    if entry.word_count == 4:  # "Test journal entry content"
                        print("✅ Word count calculation correct")
                    else:
                        print(f"❌ Word count mismatch: got {entry.word_count}, expected 4")
                        return False
                        
                    if entry.has_content:
                        print("✅ Has content flag correct")
                    else:
                        print("❌ Has content flag incorrect")
                        return False
                        
                else:
                    print("❌ Entry not found in database")
                    return False
            
            # Test database migration functionality
            print("\nTesting database migration functionality...")
            
            # Create another entry with old week ending date
            old_entry_date = date(2024, 1, 16)  # Tuesday
            async with db_manager.get_session() as session:
                old_entry = JournalEntryIndex(
                    date=old_entry_date,
                    file_path=str(temp_file_path),
                    week_ending_date=date(2024, 1, 12),  # Old week ending (Friday before)
                    word_count=2,
                    character_count=10,
                    line_count=1,
                    has_content=True
                )
                session.add(old_entry)
                await session.commit()
            
            print(f"Created test entry with old week ending: {date(2024, 1, 12)}")
            
            # Run migration
            migration_result = await db_manager.migrate_week_ending_dates(work_week_service, batch_size=10)
            
            print(f"Migration result: {migration_result}")
            
            if migration_result["success"]:
                print("✅ Migration completed successfully")
                print(f"  Entries processed: {migration_result['entries_processed']}")
                print(f"  Entries updated: {migration_result['entries_updated']}")
            else:
                print("❌ Migration failed")
                return False
            
            # Verify migration updated the entry
            async with db_manager.get_session() as session:
                stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == old_entry_date)
                result = await session.execute(stmt)
                updated_entry = result.scalar_one_or_none()
                
                if updated_entry:
                    expected_week_ending = await work_week_service.calculate_week_ending_date(old_entry_date)
                    print(f"Updated entry week ending: {updated_entry.week_ending_date}")
                    print(f"Expected week ending: {expected_week_ending}")
                    
                    if updated_entry.week_ending_date == expected_week_ending:
                        print("✅ Migration updated week ending date correctly")
                    else:
                        print("❌ Migration did not update week ending date correctly")
                        return False
                else:
                    print("❌ Updated entry not found")
                    return False
            
            # Test data integrity validation
            print("\nTesting data integrity validation...")
            
            validation_result = await db_manager.validate_week_ending_dates_integrity()
            print(f"Validation result: {validation_result}")
            
            if validation_result["success"]:
                print("✅ Data integrity validation completed")
                print(f"  Total entries: {validation_result['total_entries']}")
                print(f"  Valid entries: {validation_result['valid_entries']}")
                print(f"  Invalid entries: {validation_result['invalid_entries']}")
            else:
                print("❌ Data integrity validation failed")
                return False
            
            print("\n🎉 All database synchronization tests passed!")
            return True
            
        finally:
            # Cleanup temp file
            if temp_file_path.exists():
                temp_file_path.unlink()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup database
        if os.path.exists(db_path):
            os.unlink(db_path)


async def main():
    """Run the integration test."""
    print("Starting database synchronization integration test...\n")
    
    success = await test_database_sync_integration()
    
    if success:
        print("\n✅ Integration test PASSED")
        return 0
    else:
        print("\n❌ Integration test FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)