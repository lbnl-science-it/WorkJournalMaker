#!/usr/bin/env python3
"""
Debug script to diagnose date mapping and parsing issues.
This will identify why dates are being misinterpreted between file system and web interface.
"""

import sys
from pathlib import Path
from datetime import date, datetime
import asyncio

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

from file_discovery import FileDiscovery
from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager, JournalEntryIndex
from sqlalchemy import select

async def debug_date_mapping():
    """Debug date mapping issues between file system and database."""
    print("=== Date Mapping Diagnostic ===\n")
    
    try:
        # Setup
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
        
        # 1. Check the specific problematic file
        print("1. Analyzing Problematic File...")
        problem_file = Path("/Users/TYFong/Desktop/worklogs/worklogs_2025/worklogs_2025-06/week_ending_2025-06-20/worklog_2025-06-17.txt")
        
        if problem_file.exists():
            print(f"   ✓ File exists: {problem_file}")
            
            # Read first few lines to see actual content
            with open(problem_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')[:5]  # First 5 lines
                
            print(f"   ✓ File size: {len(content)} characters")
            print("   ✓ File content preview:")
            for i, line in enumerate(lines, 1):
                print(f"     Line {i}: {line}")
            
            # Test file discovery parsing
            file_discovery = FileDiscovery(config.processing.base_path)
            
            # Test filename parsing
            parsed_date = file_discovery._parse_file_date(problem_file.name)
            print(f"   ✓ Parsed date from filename: {parsed_date}")
            
            # Test week ending calculation
            if parsed_date:
                week_ending = file_discovery._calculate_week_ending_for_date(parsed_date)
                print(f"   ✓ Calculated week ending: {week_ending}")
                
                # Test path construction
                constructed_path = file_discovery._construct_file_path(parsed_date, week_ending)
                print(f"   ✓ Constructed path: {constructed_path}")
                print(f"   ✓ Paths match: {constructed_path == problem_file}")
        else:
            print(f"   ✗ File does not exist: {problem_file}")
        
        # 2. Check database entry for this date
        print("\n2. Checking Database Entry...")
        async with db_manager.get_session() as session:
            # Check for June 17, 2025
            june_17 = date(2025, 6, 17)
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == june_17)
            result = await session.execute(stmt)
            db_entry = result.scalar_one_or_none()
            
            if db_entry:
                print(f"   ✓ Database entry found for {june_17}")
                print(f"   ✓ File path in DB: {db_entry.file_path}")
                print(f"   ✓ Week ending in DB: {db_entry.week_ending_date}")
                print(f"   ✓ Word count: {db_entry.word_count}")
                print(f"   ✓ Has content: {db_entry.has_content}")
                print(f"   ✓ Created at: {db_entry.created_at}")
                print(f"   ✓ Modified at: {db_entry.modified_at}")
                
                # Check if file path in DB actually exists
                db_file_path = Path(db_entry.file_path)
                print(f"   ✓ DB file path exists: {db_file_path.exists()}")
            else:
                print(f"   ✗ No database entry found for {june_17}")
        
        # 3. Check calendar date calculation
        print("\n3. Testing Calendar Date Logic...")
        test_date = date(2025, 6, 17)  # June 17, 2025
        
        # Check what day of week this is
        weekday = test_date.weekday()  # 0=Monday, 6=Sunday
        weekday_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]
        print(f"   ✓ June 17, 2025 is a {weekday_name}")
        
        # Check if there's confusion between June 16 and June 17
        june_16 = date(2025, 6, 16)
        june_16_weekday = june_16.weekday()
        june_16_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][june_16_weekday]
        print(f"   ✓ June 16, 2025 is a {june_16_name}")
        
        # 4. Check for July dates that might be confused
        print("\n4. Checking for July Date Confusion...")
        
        # Look for July 1, 2025 (mentioned in content)
        july_1 = date(2025, 7, 1)
        async with db_manager.get_session() as session:
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == july_1)
            result = await session.execute(stmt)
            july_entry = result.scalar_one_or_none()
            
            if july_entry:
                print(f"   ✓ Found July 1, 2025 entry in database")
                print(f"   ✓ File path: {july_entry.file_path}")
            else:
                print(f"   ✗ No July 1, 2025 entry in database")
        
        # Look for July 17, 2025 (what you mentioned it should be)
        july_17 = date(2025, 7, 17)
        async with db_manager.get_session() as session:
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == july_17)
            result = await session.execute(stmt)
            july_17_entry = result.scalar_one_or_none()
            
            if july_17_entry:
                print(f"   ✓ Found July 17, 2025 entry in database")
                print(f"   ✓ File path: {july_17_entry.file_path}")
            else:
                print(f"   ✗ No July 17, 2025 entry in database")
        
        # 5. Check all entries around this time period
        print("\n5. Checking All Entries in June-July 2025...")
        async with db_manager.get_session() as session:
            start_date = date(2025, 6, 1)
            end_date = date(2025, 7, 31)
            
            stmt = (
                select(JournalEntryIndex.date, JournalEntryIndex.file_path, JournalEntryIndex.word_count)
                .where(JournalEntryIndex.date.between(start_date, end_date))
                .order_by(JournalEntryIndex.date)
            )
            result = await session.execute(stmt)
            entries = result.fetchall()
            
            print(f"   ✓ Found {len(entries)} entries between June-July 2025:")
            for entry_date, file_path, word_count in entries:
                file_exists = Path(file_path).exists() if file_path else False
                status = "✓" if file_exists else "✗"
                print(f"     {status} {entry_date} - {Path(file_path).name if file_path else 'No path'} ({word_count} words)")
        
        print("\n=== Analysis Complete ===")
        print("\nPossible Issues Identified:")
        print("1. Date parsing from filename may be incorrect")
        print("2. Week ending calculation may be wrong")
        print("3. Calendar display logic may have off-by-one errors")
        print("4. Content date vs filename date mismatch")
        print("5. Database sync may be mapping wrong dates")
        
    except Exception as e:
        print(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_date_mapping())