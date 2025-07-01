#!/usr/bin/env python3
"""
Debug script to diagnose database synchronization issues.
This will help identify if the database is out of sync with the file system.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import asyncio

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

from file_discovery import FileDiscovery
from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager, JournalEntryIndex
from sqlalchemy import select, func, delete

async def diagnose_database_sync():
    """Diagnose database synchronization issues."""
    print("=== Database Synchronization Diagnostic ===\n")
    
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
        
        # 2. Check file system
        print("1. Checking File System...")
        file_discovery = FileDiscovery(config.processing.base_path)
        
        # Check a broader date range
        end_date = date.today()
        start_date = end_date - timedelta(days=365)  # Last year
        
        print(f"   Scanning date range: {start_date} to {end_date}")
        result = file_discovery.discover_files(start_date, end_date)
        
        print(f"   ✓ Files found on disk: {len(result.found_files)}")
        print(f"   ✓ Files missing: {len(result.missing_files)}")
        print(f"   ✓ Success rate: {len(result.found_files)/result.total_expected*100:.1f}%")
        
        # Show sample files
        if result.found_files:
            print("   ✓ Sample files found:")
            for i, file_path in enumerate(sorted(result.found_files)[-5:]):  # Last 5 files
                print(f"     - {file_path.name} ({file_path.parent.name})")
        
        # 3. Check database
        print("\n2. Checking Database...")
        async with db_manager.get_session() as session:
            # Count total entries
            count_stmt = select(func.count(JournalEntryIndex.id))
            count_result = await session.execute(count_stmt)
            db_count = count_result.scalar()
            print(f"   ✓ Database entries: {db_count}")
            
            # Get date range in database
            min_date_stmt = select(func.min(JournalEntryIndex.date))
            max_date_stmt = select(func.max(JournalEntryIndex.date))
            
            min_result = await session.execute(min_date_stmt)
            max_result = await session.execute(max_date_stmt)
            
            min_date = min_result.scalar()
            max_date = max_result.scalar()
            
            if min_date and max_date:
                print(f"   ✓ Database date range: {min_date} to {max_date}")
            else:
                print("   ✗ No dates found in database")
            
            # Get recent entries
            recent_stmt = (
                select(JournalEntryIndex.date, JournalEntryIndex.file_path)
                .order_by(JournalEntryIndex.date.desc())
                .limit(5)
            )
            recent_result = await session.execute(recent_stmt)
            recent_entries = recent_result.fetchall()
            
            if recent_entries:
                print("   ✓ Recent database entries:")
                for entry_date, file_path in recent_entries:
                    file_exists = Path(file_path).exists() if file_path else False
                    status = "✓" if file_exists else "✗"
                    print(f"     {status} {entry_date} - {Path(file_path).name if file_path else 'No path'}")
            
        # 4. Compare file system vs database
        print("\n3. Comparing File System vs Database...")
        
        file_dates = set()
        for file_path in result.found_files:
            # Extract date from filename
            try:
                filename = file_path.name
                if filename.startswith("worklog_") and filename.endswith(".txt"):
                    date_str = filename[8:-4]  # Remove "worklog_" and ".txt"
                    year, month, day = map(int, date_str.split("-"))
                    file_dates.add(date(year, month, day))
            except:
                continue
        
        async with db_manager.get_session() as session:
            db_dates_stmt = select(JournalEntryIndex.date)
            db_dates_result = await session.execute(db_dates_stmt)
            db_dates = set(row[0] for row in db_dates_result.fetchall())
        
        print(f"   ✓ Unique dates in files: {len(file_dates)}")
        print(f"   ✓ Unique dates in database: {len(db_dates)}")
        
        missing_from_db = file_dates - db_dates
        missing_from_files = db_dates - file_dates
        
        if missing_from_db:
            print(f"   ⚠️  Files not in database: {len(missing_from_db)}")
            if len(missing_from_db) <= 10:
                for missing_date in sorted(missing_from_db)[-5:]:
                    print(f"     - {missing_date}")
            else:
                print(f"     - Recent missing: {sorted(missing_from_db)[-5:]}")
        
        if missing_from_files:
            print(f"   ⚠️  Database entries without files: {len(missing_from_files)}")
            if len(missing_from_files) <= 10:
                for missing_date in sorted(missing_from_files)[-5:]:
                    print(f"     - {missing_date}")
        
        # 5. Recommendation
        print("\n4. Recommendation...")
        if missing_from_db:
            print("   🔧 SOLUTION: Database is missing entries for existing files")
            print("   ✅ Run database reset and full sync to fix this issue")
            return "reset_database"
        elif db_count == 0:
            print("   🔧 SOLUTION: Database is empty")
            print("   ✅ Run full sync to populate database")
            return "full_sync"
        elif len(file_dates) != len(db_dates):
            print("   🔧 SOLUTION: Database and files are out of sync")
            print("   ✅ Run database reset and full sync")
            return "reset_database"
        else:
            print("   ✅ Database and files appear to be in sync")
            print("   🔍 Issue may be elsewhere - check web interface logic")
            return "check_interface"
            
    except Exception as e:
        print(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return "error"

async def reset_database_and_sync():
    """Reset database and perform full sync."""
    print("\n=== Resetting Database and Syncing ===\n")
    
    try:
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
        
        # Clear database
        print("1. Clearing existing database entries...")
        async with db_manager.get_session() as session:
            delete_stmt = delete(JournalEntryIndex)
            result = await session.execute(delete_stmt)
            await session.commit()
            print(f"   ✓ Deleted {result.rowcount} existing entries")
        
        # Import sync service
        from web.services.sync_service import DatabaseSyncService
        sync_service = DatabaseSyncService(config, logger, db_manager)
        
        # Perform full sync
        print("\n2. Performing full database sync...")
        result = await sync_service.full_sync()
        
        if result.success:
            print(f"   ✓ Full sync completed successfully")
            print(f"   ✓ Entries processed: {result.entries_processed}")
            print(f"   ✓ Entries added: {result.entries_added}")
            print(f"   ✓ Entries updated: {result.entries_updated}")
            if hasattr(result, 'entries_removed'):
                print(f"   ✓ Entries removed: {result.entries_removed}")
        else:
            error_msg = result.errors[0] if result.errors else "Unknown error"
            print(f"   ✗ Full sync failed: {error_msg}")
            return False
        
        # Verify sync
        print("\n3. Verifying sync...")
        async with db_manager.get_session() as session:
            count_stmt = select(func.count(JournalEntryIndex.id))
            count_result = await session.execute(count_stmt)
            final_count = count_result.scalar()
            print(f"   ✓ Final database count: {final_count}")
        
        return True
        
    except Exception as e:
        print(f"Database reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run diagnostic
    recommendation = asyncio.run(diagnose_database_sync())
    
    if recommendation == "reset_database":
        print("\n" + "="*50)
        response = input("Would you like to reset the database and sync now? (y/N): ")
        if response.lower() in ['y', 'yes']:
            success = asyncio.run(reset_database_and_sync())
            if success:
                print("\n✅ Database reset and sync completed!")
                print("🔄 Please restart your web server to see all entries.")
            else:
                print("\n❌ Database reset failed. Check the errors above.")
        else:
            print("\n💡 To fix manually, run: python -c \"import asyncio; from debug_database_sync import reset_database_and_sync; asyncio.run(reset_database_and_sync())\"")