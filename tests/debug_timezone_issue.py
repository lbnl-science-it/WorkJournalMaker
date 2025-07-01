#!/usr/bin/env python3
"""
Debug script to specifically test timezone and date display issues.
This will validate the two most likely sources of the July 1st date problem.
"""

import sys
from pathlib import Path
from datetime import date, datetime, timezone
import asyncio
import json

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager, JournalEntryIndex
from web.services.entry_manager import EntryManager
from web.services.calendar_service import CalendarService
from sqlalchemy import select

async def debug_timezone_issue():
    """Debug timezone and date display issues specifically."""
    print("=== Timezone and Date Display Diagnostic ===\n")
    
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
        
        # 1. Test current date/time handling
        print("1. Testing Current Date/Time Handling...")
        
        # Python date.today() - what the backend uses
        python_today = date.today()
        print(f"   ✓ Python date.today(): {python_today}")
        
        # Python datetime.now() with different timezones
        utc_now = datetime.now(timezone.utc)
        local_now = datetime.now()
        print(f"   ✓ Python datetime.now() UTC: {utc_now}")
        print(f"   ✓ Python datetime.now() local: {local_now}")
        
        # Check if there's a timezone offset issue
        utc_date = utc_now.date()
        local_date = local_now.date()
        print(f"   ✓ UTC date: {utc_date}")
        print(f"   ✓ Local date: {local_date}")
        
        if utc_date != local_date:
            print(f"   ⚠️  WARNING: UTC date ({utc_date}) != Local date ({local_date})")
            print(f"   ⚠️  This could cause the July 1st issue if UTC is used!")
        
        # 2. Test database entry timestamps
        print(f"\n2. Testing Database Entry Timestamps...")
        
        # Get recent entries to check their timestamps
        recent_entries = await entry_manager.get_recent_entries(limit=5)
        
        for i, entry in enumerate(recent_entries.entries[:3], 1):
            print(f"\n   Entry {i}: {entry.date}")
            print(f"     ✓ File path: {entry.file_path}")
            print(f"     ✓ Created at: {entry.created_at}")
            print(f"     ✓ Modified at: {entry.modified_at}")
            print(f"     ✓ File modified at: {entry.file_modified_at}")
            
            # Check if any timestamps are in the future relative to entry date
            if entry.modified_at:
                modified_date = entry.modified_at.date()
                if modified_date > entry.date:
                    print(f"     ⚠️  WARNING: Modified date ({modified_date}) > Entry date ({entry.date})")
                    print(f"     ⚠️  This could cause display issues!")
                    
                    # Check timezone info
                    if entry.modified_at.tzinfo:
                        print(f"     ✓ Modified timestamp has timezone: {entry.modified_at.tzinfo}")
                    else:
                        print(f"     ⚠️  Modified timestamp is naive (no timezone)")
            
            # Check file system timestamp vs database timestamp
            if entry.file_path:
                file_path = Path(entry.file_path)
                if file_path.exists():
                    file_stat = file_path.stat()
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    print(f"     ✓ File system mtime: {file_mtime}")
                    
                    if entry.modified_at:
                        time_diff = abs((file_mtime - entry.modified_at.replace(tzinfo=None)).total_seconds())
                        if time_diff > 3600:  # More than 1 hour difference
                            print(f"     ⚠️  WARNING: File mtime differs from DB by {time_diff/3600:.1f} hours")
        
        # 3. Test calendar service today info
        print(f"\n3. Testing Calendar Service Today Info...")
        today_info = await calendar_service.get_today_info()
        
        print(f"   ✓ Today from calendar service: {today_info['today']}")
        print(f"   ✓ Formatted date: {today_info['formatted_date']}")
        print(f"   ✓ Has entry: {today_info['has_entry']}")
        
        if today_info['entry_metadata']:
            metadata = today_info['entry_metadata']
            print(f"   ✓ Entry metadata modified_at: {metadata.get('modified_at')}")
            
            # This is likely where the issue occurs - check the modified_at timestamp
            if metadata.get('modified_at'):
                modified_dt = metadata['modified_at']
                if isinstance(modified_dt, str):
                    print(f"   ⚠️  Modified timestamp is string: {modified_dt}")
                    # Test parsing this string like JavaScript would
                    try:
                        parsed_dt = datetime.fromisoformat(modified_dt.replace('Z', '+00:00'))
                        print(f"   ✓ Parsed as datetime: {parsed_dt}")
                        print(f"   ✓ Parsed date: {parsed_dt.date()}")
                        
                        # Check if this creates the July 1st issue
                        if parsed_dt.date() != python_today:
                            print(f"   ⚠️  ISSUE FOUND: Parsed date ({parsed_dt.date()}) != Today ({python_today})")
                    except Exception as e:
                        print(f"   ✗ Failed to parse timestamp: {e}")
        
        # 4. Test specific entry that shows July 1st
        print(f"\n4. Testing Specific Entry with July 1st Issue...")
        
        # Look for June 26, 2025 entry (the one highlighted in the image)
        june_26 = date(2025, 6, 26)
        june_26_entry = await entry_manager.get_entry_by_date(june_26, include_content=True)
        
        if june_26_entry:
            print(f"   ✓ Found June 26, 2025 entry")
            print(f"   ✓ Entry date: {june_26_entry.date}")
            print(f"   ✓ Created at: {june_26_entry.created_at}")
            print(f"   ✓ Modified at: {june_26_entry.modified_at}")
            
            # Simulate JavaScript date parsing
            if june_26_entry.modified_at:
                # Convert to ISO string like the API would return
                iso_string = june_26_entry.modified_at.isoformat()
                print(f"   ✓ ISO string for frontend: {iso_string}")
                
                # Test different parsing scenarios
                print(f"\n   Testing JavaScript-like parsing scenarios:")
                
                # Scenario 1: Direct Date() constructor (problematic)
                try:
                    import dateutil.parser
                    parsed_1 = dateutil.parser.parse(iso_string)
                    print(f"     Scenario 1 (dateutil): {parsed_1} -> {parsed_1.date()}")
                except:
                    print(f"     Scenario 1: Failed to parse")
                
                # Scenario 2: Manual component parsing (correct)
                if 'T' in iso_string:
                    date_part = iso_string.split('T')[0]
                    year, month, day = date_part.split('-')
                    manual_date = date(int(year), int(month), int(day))
                    print(f"     Scenario 2 (manual): {date_part} -> {manual_date}")
                    
                    if manual_date != june_26_entry.date:
                        print(f"     ⚠️  Manual parsing mismatch!")
        
        # 5. Generate test data for frontend debugging
        print(f"\n5. Generating Test Data for Frontend Debugging...")
        
        test_data = {
            "python_today": str(python_today),
            "utc_now": utc_now.isoformat(),
            "local_now": local_now.isoformat(),
            "timezone_offset_hours": (local_now - utc_now.replace(tzinfo=None)).total_seconds() / 3600,
            "recent_entries": []
        }
        
        for entry in recent_entries.entries[:3]:
            entry_data = {
                "date": str(entry.date),
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "modified_at": entry.modified_at.isoformat() if entry.modified_at else None,
                "file_path": entry.file_path
            }
            test_data["recent_entries"].append(entry_data)
        
        # Write test data for frontend debugging
        test_file = Path(__file__).parent / "timezone_test_data.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        print(f"   ✓ Test data written to: {test_file}")
        
        print(f"\n=== Diagnosis Summary ===")
        print(f"Current time: {local_now} (Local)")
        print(f"Current date: {python_today}")
        print(f"UTC time: {utc_now}")
        print(f"UTC date: {utc_date}")
        
        if utc_date != local_date:
            print(f"\n🔍 LIKELY ISSUE FOUND:")
            print(f"   UTC date ({utc_date}) != Local date ({local_date})")
            print(f"   If timestamps are stored in UTC but displayed without timezone conversion,")
            print(f"   this would cause June 30 (local) to appear as July 1 (UTC).")
            print(f"\n💡 RECOMMENDED FIX:")
            print(f"   1. Ensure all timestamps are properly timezone-aware")
            print(f"   2. Convert UTC timestamps to Los Angeles timezone before display")
            print(f"   3. Fix JavaScript date parsing to handle timezones correctly")
        
    except Exception as e:
        print(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_timezone_issue())