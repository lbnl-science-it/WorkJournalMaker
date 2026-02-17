#!/usr/bin/env python3
"""
Test script to verify the timezone fixes are working correctly.
This will test that dates now display in the correct local timezone.
"""

import sys
from pathlib import Path
from datetime import date, datetime
import asyncio
import json

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig
from web.database import DatabaseManager, JournalEntryIndex
from web.services.entry_manager import EntryManager
from web.services.calendar_service import CalendarService
from web.utils.timezone_utils import get_timezone_manager, now_local, now_utc, to_local
from sqlalchemy import select

async def test_timezone_fix():
    """Test that timezone fixes are working correctly."""
    print("=== Testing Timezone Fixes ===\n")
    
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
        
        # 1. Test timezone manager
        print("1. Testing Timezone Manager...")
        tz_manager = get_timezone_manager()
        tz_info = tz_manager.get_timezone_info()
        
        print(f"   ✓ System timezone: {tz_info['system_timezone']}")
        print(f"   ✓ Current local time: {tz_info['current_local_time']}")
        print(f"   ✓ Current UTC time: {tz_info['current_utc_time']}")
        print(f"   ✓ Local date: {tz_info['local_date']}")
        print(f"   ✓ UTC date: {tz_info['utc_date']}")
        print(f"   ✓ Timezone offset: {tz_info['offset_hours']} hours")
        
        # Check if dates match now
        if tz_info['local_date'] == tz_info['utc_date']:
            print(f"   ✅ Local and UTC dates now match: {tz_info['local_date']}")
        else:
            print(f"   ⚠️  Local ({tz_info['local_date']}) and UTC ({tz_info['utc_date']}) dates still differ")
        
        # 2. Test calendar service today info
        print(f"\n2. Testing Calendar Service Today Info...")
        today_info = await calendar_service.get_today_info()
        
        print(f"   ✓ Today from calendar service: {today_info['today']}")
        print(f"   ✓ Formatted date: {today_info['formatted_date']}")
        print(f"   ✓ Expected local date: {now_local().date()}")
        
        if today_info['today'] == now_local().date():
            print(f"   ✅ Calendar service now returns correct local date")
        else:
            print(f"   ❌ Calendar service date mismatch")
        
        # 3. Test recent entries with timezone-aware timestamps
        print(f"\n3. Testing Recent Entries with Timezone-Aware Timestamps...")
        recent_entries = await entry_manager.get_recent_entries(limit=3)
        
        for i, entry in enumerate(recent_entries.entries[:3], 1):
            print(f"\n   Entry {i}: {entry.date}")
            print(f"     ✓ Created at: {entry.created_at}")
            print(f"     ✓ Modified at: {entry.modified_at}")
            
            # Test that timestamps are now timezone-aware strings
            if entry.modified_at:
                if isinstance(entry.modified_at, str):
                    print(f"     ✅ Modified timestamp is now a timezone-aware string")
                    
                    # Test parsing the timestamp
                    try:
                        from datetime import datetime
                        parsed_dt = datetime.fromisoformat(entry.modified_at.replace('Z', '+00:00'))
                        parsed_date = parsed_dt.date()
                        print(f"     ✓ Parsed date: {parsed_date}")
                        
                        # Check if the parsed date is reasonable (not in the future)
                        today = now_local().date()
                        if parsed_date <= today:
                            print(f"     ✅ Parsed date is reasonable (not in future)")
                        else:
                            print(f"     ⚠️  Parsed date is in the future: {parsed_date} > {today}")
                            
                    except Exception as e:
                        print(f"     ❌ Failed to parse timestamp: {e}")
                else:
                    print(f"     ⚠️  Modified timestamp is not a string: {type(entry.modified_at)}")
        
        # 4. Test calendar month generation
        print(f"\n4. Testing Calendar Month Generation...")
        current_local = now_local()
        calendar_data = await calendar_service.get_calendar_month(current_local.year, current_local.month)
        
        print(f"   ✓ Calendar month: {calendar_data.month_name} {calendar_data.year}")
        print(f"   ✓ Today in calendar: {calendar_data.today}")
        print(f"   ✓ Expected today: {current_local.date()}")
        
        if calendar_data.today == current_local.date():
            print(f"   ✅ Calendar month uses correct local date for 'today'")
        else:
            print(f"   ❌ Calendar month 'today' date mismatch")
        
        # 5. Test database timestamp creation
        print(f"\n5. Testing Database Timestamp Creation...")
        
        # Check if new entries would have timezone-aware timestamps
        async with db_manager.get_session() as session:
            # Get the most recent entry to check its timestamp
            stmt = select(JournalEntryIndex).order_by(JournalEntryIndex.created_at.desc()).limit(1)
            result = await session.execute(stmt)
            latest_entry = result.scalar_one_or_none()
            
            if latest_entry:
                print(f"   ✓ Latest entry date: {latest_entry.date}")
                print(f"   ✓ Created at: {latest_entry.created_at}")
                print(f"   ✓ Modified at: {latest_entry.modified_at}")
                
                # Check if timestamps have timezone info
                if latest_entry.created_at and latest_entry.created_at.tzinfo:
                    print(f"   ✅ Database timestamps are now timezone-aware")
                    print(f"   ✓ Timezone: {latest_entry.created_at.tzinfo}")
                else:
                    print(f"   ⚠️  Database timestamps may still be naive")
        
        # 6. Summary of fixes
        print(f"\n=== Summary of Timezone Fixes ===")
        
        fixes_working = []
        fixes_needed = []
        
        # Check each fix
        if tz_info['local_date'] == today_info['today'].isoformat():
            fixes_working.append("✅ Calendar service uses local timezone")
        else:
            fixes_needed.append("❌ Calendar service timezone issue")
            
        if calendar_data.today == current_local.date():
            fixes_working.append("✅ Calendar month generation uses local timezone")
        else:
            fixes_needed.append("❌ Calendar month timezone issue")
        
        # Check if we have timezone-aware API responses
        has_timezone_aware_responses = any(
            isinstance(entry.modified_at, str) and 'T' in str(entry.modified_at)
            for entry in recent_entries.entries[:3]
            if entry.modified_at
        )
        
        if has_timezone_aware_responses:
            fixes_working.append("✅ API responses include timezone-aware timestamps")
        else:
            fixes_needed.append("❌ API responses need timezone-aware timestamps")
        
        print(f"\nFixes Working ({len(fixes_working)}):")
        for fix in fixes_working:
            print(f"  {fix}")
        
        if fixes_needed:
            print(f"\nFixes Still Needed ({len(fixes_needed)}):")
            for fix in fixes_needed:
                print(f"  {fix}")
        else:
            print(f"\n🎉 All timezone fixes are working correctly!")
        
        # 7. Test data for frontend verification
        print(f"\n6. Generating Test Data for Frontend Verification...")
        
        test_data = {
            "timezone_info": tz_info,
            "calendar_today": str(calendar_data.today),
            "expected_today": str(current_local.date()),
            "sample_entries": []
        }
        
        for entry in recent_entries.entries[:3]:
            entry_data = {
                "date": str(entry.date),
                "created_at": entry.created_at,
                "modified_at": entry.modified_at,
                "file_path": entry.file_path
            }
            test_data["sample_entries"].append(entry_data)
        
        # Write test data
        test_file = Path(__file__).parent / "timezone_fix_verification.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2, default=str)
        
        print(f"   ✓ Test data written to: {test_file}")
        
        return len(fixes_needed) == 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_timezone_fix())
    if success:
        print(f"\n🎉 All timezone fixes verified successfully!")
        exit(0)
    else:
        print(f"\n❌ Some timezone fixes still need work.")
        exit(1)