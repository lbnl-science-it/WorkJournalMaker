#!/usr/bin/env python3
"""
Reset database and sync with the corrected week ending logic.
This script will clear the database and re-sync all entries using the fixed file discovery.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import asyncio

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager, JournalEntryIndex
from web.services.sync_service import DatabaseSyncService
from sqlalchemy import select, delete, func

async def reset_database_with_fix():
    """Reset database and sync with corrected week ending logic."""
    print("=== Database Reset with Week Ending Fix ===\n")
    
    try:
        # 1. Setup
        config = AppConfig()
        log_config = LogConfig(
            level=config.logging.level,
            console_output=config.logging.console_output,
            file_output=config.logging.file_output,
            log_dir=config.logging.log_dir,
            include_timestamps=config.logging.include_timestamps,
            include_module_names=config.logging.include_module_names,
            max_file_size_mb=config.logging.max_file_size_mb,
            backup_count=config.logging.backup_count
        )
        logger = JournalSummarizerLogger(log_config)
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # 2. Check current database state
        print("1. Checking current database state...")
        async with db_manager.get_session() as session:
            count_stmt = select(func.count(JournalEntryIndex.id))
            count_result = await session.execute(count_stmt)
            current_count = count_result.scalar()
            print(f"   ✓ Current database entries: {current_count}")
        
        # 3. Clear database
        print("\n2. Clearing existing database entries...")
        async with db_manager.get_session() as session:
            delete_stmt = delete(JournalEntryIndex)
            result = await session.execute(delete_stmt)
            await session.commit()
            print(f"   ✓ Deleted {result.rowcount} existing entries")
        
        # 4. Perform full sync with fixed logic
        print("\n3. Performing full sync with corrected week ending logic...")
        sync_service = DatabaseSyncService(config, logger, db_manager)
        
        # Sync a broader date range to catch all entries
        result = await sync_service.full_sync(date_range_days=1095)  # 3 years
        
        if result.success:
            print(f"   ✅ Full sync completed successfully!")
            print(f"   ✓ Entries processed: {result.entries_processed}")
            print(f"   ✓ Entries added: {result.entries_added}")
            print(f"   ✓ Entries updated: {result.entries_updated}")
            if hasattr(result, 'entries_removed'):
                print(f"   ✓ Entries removed: {result.entries_removed}")
        else:
            error_msg = result.errors[0] if result.errors else "Unknown error"
            print(f"   ❌ Full sync failed: {error_msg}")
            return False
        
        # 5. Verify final state
        print("\n4. Verifying final database state...")
        async with db_manager.get_session() as session:
            # Count total entries
            count_stmt = select(func.count(JournalEntryIndex.id))
            count_result = await session.execute(count_stmt)
            final_count = count_result.scalar()
            print(f"   ✓ Final database entries: {final_count}")
            
            # Show recent entries
            recent_stmt = (
                select(JournalEntryIndex.date, JournalEntryIndex.file_path, JournalEntryIndex.word_count)
                .order_by(JournalEntryIndex.date.desc())
                .limit(5)
            )
            recent_result = await session.execute(recent_stmt)
            recent_entries = recent_result.fetchall()
            
            print("   ✓ Recent entries in database:")
            for entry_date, file_path, word_count in recent_entries:
                file_exists = Path(file_path).exists() if file_path else False
                status = "✅" if file_exists else "❌"
                print(f"     {status} {entry_date} - {Path(file_path).name if file_path else 'No path'} ({word_count} words)")
        
        print(f"\n🎉 Database reset and sync completed successfully!")
        print(f"📊 Total entries synchronized: {final_count}")
        print(f"🔄 Please restart your web server to see all entries.")
        
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(reset_database_with_fix())
    sys.exit(0 if success else 1)