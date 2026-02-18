#!/usr/bin/env python3
"""
Debug script to identify all date display and parsing issues.
This will check calendar logic, modal display, content parsing, and recent entries.
"""

from pathlib import Path
from datetime import date, datetime
import asyncio
import re

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager, JournalEntryIndex
from web.services.entry_manager import EntryManager
from web.services.calendar_service import CalendarService
from sqlalchemy import select

async def debug_date_display_issues():
    """Debug all date display and parsing issues."""
    print("=== Date Display Issues Diagnostic ===\n")
    
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
        
        entry_manager = EntryManager(config, logger, db_manager)
        calendar_service = CalendarService(config, logger, db_manager)
        
        # 1. Test the specific problematic date: June 12, 2025
        print("1. Testing June 12, 2025 Entry...")
        test_date = date(2025, 6, 12)
        
        # Check database entry
        async with db_manager.get_session() as session:
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == test_date)
            result = await session.execute(stmt)
            db_entry = result.scalar_one_or_none()
            
            if db_entry:
                print(f"   ✓ Database entry found for {test_date}")
                print(f"   ✓ File path: {db_entry.file_path}")
                print(f"   ✓ Week ending: {db_entry.week_ending_date}")
                print(f"   ✓ Created at: {db_entry.created_at}")
                print(f"   ✓ Modified at: {db_entry.modified_at}")
                
                # Check actual file
                file_path = Path(db_entry.file_path)
                if file_path.exists():
                    print(f"   ✓ File exists: {file_path}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    print(f"   ✓ File content ({len(content)} chars):")
                    lines = content.split('\n')[:5]
                    for i, line in enumerate(lines, 1):
                        print(f"     Line {i}: {line}")
                    
                    # Look for date patterns in content
                    date_patterns = re.findall(r'\b\d{4}-\d{2}-\d{2}\b', content)
                    if date_patterns:
                        print(f"   ⚠️  Date patterns found in content: {date_patterns}")
                        for pattern in date_patterns:
                            try:
                                parsed_date = date.fromisoformat(pattern)
                                print(f"     - {pattern} -> {parsed_date} (weekday: {parsed_date.strftime('%A')})")
                            except:
                                print(f"     - {pattern} -> Invalid date")
                else:
                    print(f"   ✗ File does not exist: {file_path}")
            else:
                print(f"   ✗ No database entry found for {test_date}")
        
        # 2. Test EntryManager retrieval
        print(f"\n2. Testing EntryManager for {test_date}...")
        entry_response = await entry_manager.get_entry_by_date(test_date, include_content=True)
        
        if entry_response:
            print(f"   ✓ EntryManager found entry")
            print(f"   ✓ Entry date: {entry_response.date}")
            print(f"   ✓ File path: {entry_response.file_path}")
            print(f"   ✓ Week ending: {entry_response.week_ending_date}")
            print(f"   ✓ Created at: {entry_response.created_at}")
            print(f"   ✓ Modified at: {entry_response.modified_at}")
            
            if entry_response.content:
                print(f"   ✓ Content preview: {entry_response.content[:100]}...")
        else:
            print(f"   ✗ EntryManager could not retrieve entry")
        
        # 3. Test Calendar Service
        print(f"\n3. Testing Calendar Service for {test_date}...")
        
        # Get calendar data for June 2025
        calendar_data = await calendar_service.get_calendar_data(2025, 6)
        
        print(f"   ✓ Calendar data retrieved for June 2025")
        print(f"   ✓ Total days: {len(calendar_data.days)}")
        
        # Find June 12 in calendar data
        june_12_day = None
        for day in calendar_data.days:
            if day.date == test_date:
                june_12_day = day
                break
        
        if june_12_day:
            print(f"   ✓ June 12 found in calendar")
            print(f"   ✓ Has entry: {june_12_day.has_entry}")
            print(f"   ✓ Word count: {june_12_day.word_count}")
            print(f"   ✓ Is today: {june_12_day.is_today}")
            print(f"   ✓ Is weekend: {june_12_day.is_weekend}")
        else:
            print(f"   ✗ June 12 not found in calendar data")
        
        # 4. Check Recent Entries
        print(f"\n4. Testing Recent Entries...")
        recent_entries = await entry_manager.get_recent_entries(limit=10)
        
        print(f"   ✓ Recent entries retrieved: {len(recent_entries.entries)}")
        
        for i, entry in enumerate(recent_entries.entries[:5], 1):
            print(f"   Entry {i}: {entry.date} - {entry.metadata.word_count} words")
            
            # Check if this is June 26 (the bolded one)
            if entry.date == date(2025, 6, 26):
                print(f"     ⚠️  This is the June 26 entry that appears bolded")
                print(f"     ✓ File path: {entry.file_path}")
                print(f"     ✓ Week ending: {entry.week_ending_date}")
        
        # 5. Check for date calculation issues
        print(f"\n5. Testing Date Calculations...")
        
        # Test weekday calculation
        june_12_weekday = test_date.weekday()  # 0=Monday, 6=Sunday
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        calculated_weekday = weekday_names[june_12_weekday]
        
        print(f"   ✓ June 12, 2025 is a {calculated_weekday}")
        
        # Check if there's an off-by-one error
        june_11 = date(2025, 6, 11)
        june_11_weekday = weekday_names[june_11.weekday()]
        print(f"   ✓ June 11, 2025 is a {june_11_weekday}")
        
        # 6. Summary of Issues Found
        print(f"\n6. Summary of Issues Identified:")
        issues = []
        
        if db_entry and entry_response:
            if db_entry.date != entry_response.date:
                issues.append("Database date != EntryManager date")
            
            if date_patterns:
                issues.append(f"Content contains date patterns: {date_patterns}")
            
            # Check for year issues
            for pattern in date_patterns:
                if pattern.startswith("2028"):
                    issues.append("Content contains 2028 dates (should be 2025)")
                if pattern.endswith("07-01"):
                    issues.append("Content contains July 1 date")
        
        if issues:
            print("   ⚠️  Issues found:")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print("   ✅ No obvious issues detected")
        
        # 7. Recommendations
        print(f"\n7. Recommendations:")
        print("   1. Check if content dates are being parsed and displayed incorrectly")
        print("   2. Verify calendar modal title calculation logic")
        print("   3. Check recent entries highlighting/bolding logic")
        print("   4. Investigate content date vs filename date mismatch")
        
    except Exception as e:
        print(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_date_display_issues())